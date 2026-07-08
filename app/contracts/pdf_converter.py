from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class WordNotAvailableError(RuntimeError):
    """Levee lorsque Microsoft Word n'est pas disponible via COM sur ce poste."""


class PdfConverter:
    """Convertit un document DOCX en PDF via Microsoft Word (COM), pour un rendu fidele au DOCX."""

    WD_EXPORT_FORMAT_PDF = 17

    def convert(self, docx_path: str | Path, pdf_path: str | Path) -> None:
        docx_path = Path(docx_path).resolve()
        pdf_path = Path(pdf_path).resolve()

        if not docx_path.exists():
            raise FileNotFoundError(f"Document DOCX introuvable : {docx_path}")

        try:
            import pythoncom
            import win32com.client
        except ImportError as exc:
            raise WordNotAvailableError(
                "Microsoft Word (pywin32) n'est pas disponible sur ce poste."
            ) from exc

        # Le DOCX source peut deja etre ouvert (le generateur l'ouvre automatiquement) :
        # on convertit une copie temporaire pour eviter tout conflit de verrouillage.
        with tempfile.TemporaryDirectory(prefix="ygnt_pdf_") as tmp_dir:
            tmp_docx = Path(tmp_dir) / docx_path.name
            shutil.copy2(docx_path, tmp_docx)

            pythoncom.CoInitialize()
            word = None
            document = None

            try:
                try:
                    word = win32com.client.DispatchEx("Word.Application")
                except Exception as exc:
                    raise WordNotAvailableError(
                        "Microsoft Word n'est pas installe ou n'a pas pu demarrer."
                    ) from exc

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
                    raise RuntimeError(
                        f"Echec de la conversion PDF via Microsoft Word : {exc}"
                    ) from exc
            finally:
                if document is not None:
                    document.Close(False)
                if word is not None:
                    word.Quit()
                pythoncom.CoUninitialize()
