from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 90.0

# Delai supplementaire, apres l'expiration du timeout, pendant lequel on
# continue de surveiller l'apparition de l'instance Word que nous avons
# demarree (DispatchEx peut ne pas avoir fini de lancer le processus au
# moment exact ou le timeout expire). Purement du nettoyage : n'allonge
# jamais le delai percu par l'utilisateur, qui recoit deja son erreur.
KILL_GRACE_SECONDS = 10.0


class WordNotAvailableError(RuntimeError):
    """Levee lorsque Microsoft Word n'est pas disponible via COM sur ce poste."""


class PdfConversionTimeoutError(RuntimeError):
    """Levee lorsque Microsoft Word ne repond plus dans le delai imparti
    (ex. boite de dialogue Word invisible en attente d'une intervention)."""


class PdfConverter:
    """Convertit un document DOCX en PDF via Microsoft Word (COM), pour un rendu fidele au DOCX.

    L'automatisation COM tourne dans un thread dedie et est bornee par
    `timeout` : si Word ne repond plus (ex. boite de dialogue masquee car
    l'instance est invisible), l'appel ne bloque jamais indefiniment
    l'appelant. Seule l'instance Word creee par cet appel (via DispatchEx)
    peut alors etre terminee de force - jamais une fenetre Word deja
    ouverte par l'utilisateur.
    """

    WD_EXPORT_FORMAT_PDF = 17

    def convert(
        self,
        docx_path: str | Path,
        pdf_path: str | Path,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        docx_path = Path(docx_path).resolve()
        pdf_path = Path(pdf_path).resolve()

        if not docx_path.exists():
            raise FileNotFoundError(f"Document DOCX introuvable : {docx_path}")

        try:
            import win32com.client  # noqa: F401
        except ImportError as exc:
            raise WordNotAvailableError(
                "Microsoft Word (pywin32) n'est pas disponible sur ce poste."
            ) from exc

        # Le DOCX source peut deja etre ouvert dans Word par l'utilisateur :
        # on convertit une copie temporaire pour eviter tout conflit de verrouillage.
        with tempfile.TemporaryDirectory(prefix="ygnt_pdf_") as tmp_dir:
            tmp_docx = Path(tmp_dir) / docx_path.name
            shutil.copy2(docx_path, tmp_docx)

            before_pids = _winword_pids()
            outcome: dict[str, object] = {}
            created_pid: list[int] = []

            worker = threading.Thread(
                target=self._convert_via_word,
                args=(tmp_docx, pdf_path, outcome, created_pid),
                daemon=True,
            )
            worker.start()
            worker.join(timeout)

            if worker.is_alive():
                # Word ne repond plus : on ferme uniquement l'instance que nous
                # avons nous-memes creee, jamais une fenetre Word ouverte par
                # l'utilisateur. La recherche du PID se poursuit en arriere-plan
                # (DispatchEx peut ne pas avoir fini de demarrer le processus
                # au moment precis ou le timeout expire) sans retarder l'erreur
                # renvoyee a l'appelant.
                threading.Thread(
                    target=_terminate_orphaned_word,
                    args=(before_pids, created_pid),
                    daemon=True,
                ).start()
                raise PdfConversionTimeoutError(
                    "La generation du PDF a depasse le delai autorise "
                    f"({int(timeout)}s) : Microsoft Word ne repond plus."
                )

            error = outcome.get("error")
            if error is not None:
                raise error  # type: ignore[misc]

    def _convert_via_word(
        self,
        tmp_docx: Path,
        pdf_path: Path,
        outcome: dict[str, object],
        created_pid: list[int],
    ) -> None:
        """Tourne sur un thread dedie (obligatoire pour l'appartement COM).
        Toute erreur est deposee dans `outcome["error"]` plutot que levee :
        ce thread n'est jamais celui qui attend le resultat."""
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        word = None
        document = None

        try:
            before_pids = _winword_pids()
            try:
                word = win32com.client.DispatchEx("Word.Application")
            except Exception:
                outcome["error"] = WordNotAvailableError(
                    "Microsoft Word n'est pas installe ou n'a pas pu demarrer."
                )
                return

            new_pids = _winword_pids() - before_pids
            if len(new_pids) == 1:
                created_pid.append(new_pids.pop())

            word.Visible = False
            word.DisplayAlerts = 0

            try:
                document = word.Documents.Open(
                    str(tmp_docx),
                    ReadOnly=True,
                    AddToRecentFiles=False,
                    ConfirmConversions=False,
                )
                document.ExportAsFixedFormat(
                    OutputFileName=str(pdf_path),
                    ExportFormat=self.WD_EXPORT_FORMAT_PDF,
                )
            except Exception as exc:
                outcome["error"] = RuntimeError(
                    f"Echec de la conversion PDF via Microsoft Word : {exc}"
                )
        finally:
            # Nettoyage toujours tente, meme apres une erreur ci-dessus - une
            # etape en echec ne doit jamais empecher les suivantes.
            try:
                if document is not None:
                    document.Close(False)
            except Exception:
                pass
            try:
                if word is not None:
                    word.Quit()
            except Exception:
                pass
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
            outcome["done"] = True


def _winword_pids() -> set[int]:
    """PID de tous les processus WINWORD.EXE actuellement lances (utilisateur
    inclus), via l'outil systeme `tasklist` - aucune dependance supplementaire."""
    try:
        completed = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq WINWORD.EXE", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return set()

    pids: set[int] = set()
    for line in completed.stdout.splitlines():
        fields = [field.strip('"') for field in line.split('","')]
        if len(fields) >= 2 and fields[0].upper() == "WINWORD.EXE":
            try:
                pids.add(int(fields[1]))
            except ValueError:
                continue
    return pids


def _terminate_orphaned_word(before_pids: set[int], created_pid: list[int]) -> None:
    """Identifie puis termine l'instance Word creee par un appel qui a
    depasse son timeout, y compris si DispatchEx n'avait pas encore fini de
    demarrer le processus au moment ou le timeout a expire. Ne termine
    jamais un WINWORD.exe present avant l'appel (`before_pids`) : uniquement
    ceux apparus depuis, jusqu'a `KILL_GRACE_SECONDS` d'attente."""
    deadline = time.monotonic() + KILL_GRACE_SECONDS
    while time.monotonic() < deadline:
        if created_pid:
            break
        if _winword_pids() - before_pids:
            break
        time.sleep(0.5)

    pids_to_kill = set(created_pid) | (_winword_pids() - before_pids)
    for pid in pids_to_kill:
        _kill_process(pid)


def _kill_process(pid: int) -> None:
    """Termine de force un unique processus par PID (l'instance Word que nous
    avons creee). N'affecte jamais les autres instances de Word."""
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F", "/T"],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass
