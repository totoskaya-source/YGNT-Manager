"""Moteur commun de remplacement de placeholders {{cle}} dans un document
python-docx. Partage entre le generateur de Contrats, de Devis et de
Factures pour eviter de dupliquer la logique de substitution.

Filtres de formatage (optionnel, syntaxe `{{cle|filtre}}`)
------------------------------------------------------------
Un placeholder peut demander explicitement un formatage particulier en
suffixant son nom avec `|nom_du_filtre`, par exemple `{{montant|currency}}`.
Aucun filtre n'est jamais applique implicitement d'apres le type Python de
la valeur (un entier ou un flottant reste affiche tel quel via `str()` s'il
n'est pas explicitement marque) : un code postal, un numero de telephone,
un SIRET ou une reference qui seraient stockes sous forme numerique ne
risquent donc jamais d'etre transformes en devise par erreur. Le mapping
`PlaceholderEngine.FILTERS` est le point d'extension pour ajouter de
nouveaux filtres (dates, pourcentages...) sans jamais coupler ce module a
un document particulier.

Lignes conditionnelles
------------------------------------------------------------
Un paragraphe dont TOUS les placeholders qu'il contient correspondent a des
valeurs vides (chaine vide ou None) est retire automatiquement du document,
plutot que de laisser une ligne incomplete du type "Siret : " ou
"Represente par ,". Un paragraphe sans aucun placeholder n'est jamais
concerne ; un paragraphe dont au moins un placeholder a une valeur non vide
est conserve tel quel.
"""

import re

PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)(?:\|(\w+))?\}\}")


def _filter_currency(value):
    """Format explicite `currency` : nombre au format francais (virgule
    decimale, deux decimales, espace comme separateur de milliers), par
    exemple 1234.5 -> "1 234,50". Une valeur non convertible en nombre est
    renvoyee inchangee (str())."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    grouped = f"{number:,.2f}"
    return grouped.replace(",", "\x00").replace(".", ",").replace("\x00", " ")


class PlaceholderEngine:

    # Point d'extension pour de futurs filtres `{{cle|nom_du_filtre}}`.
    # Chaque filtre est une fonction (valeur_brute) -> texte.
    FILTERS = {
        "currency": _filter_currency,
    }

    @staticmethod
    def replace_in_document(doc, values):
        for paragraph in doc.paragraphs:
            PlaceholderEngine.replace_paragraph(paragraph, values)

        PlaceholderEngine.replace_in_tables(doc.tables, values)

        for section in doc.sections:
            for header_footer in (section.header, section.footer):
                # Une section "liee" (is_linked_to_previous) n'a pas sa
                # propre definition : elle herite de la section precedente
                # (ou d'un gabarit par defaut). La lire malgre tout via
                # python-docx creerait silencieusement une nouvelle
                # definition vide - on ne traite donc que les sections qui
                # possedent reellement leur propre en-tete/pied de page.
                if header_footer.is_linked_to_previous:
                    continue

                for paragraph in header_footer.paragraphs:
                    PlaceholderEngine.replace_paragraph(paragraph, values)

                PlaceholderEngine.replace_in_tables(header_footer.tables, values)

    @staticmethod
    def replace_in_tables(tables, values):
        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        PlaceholderEngine.replace_paragraph(paragraph, values)

    @staticmethod
    def replace_paragraph(paragraph, values):
        if not paragraph.runs:
            return

        full_text = "".join(run.text for run in paragraph.runs)

        # Seuls les placeholders reellement presents dans ce paragraphe et
        # connus de `values` comptent : pour la substitution, et pour la
        # regle "ligne vide" ci-dessous (un paragraphe sans placeholder, ou
        # un texte fixe, n'est jamais concerne).
        matches = [m for m in PLACEHOLDER_PATTERN.finditer(full_text) if m.group(1) in values]
        if not matches:
            return

        if all(PlaceholderEngine._is_empty(values[m.group(1)]) for m in matches):
            # Tous les placeholders de la ligne sont vides : la ligne
            # n'aurait plus que du texte fixe incomplet ("Siret : ",
            # "Represente par ,"...) - on supprime le paragraphe entier
            # plutot que d'afficher une ligne cassee.
            PlaceholderEngine._remove_paragraph(paragraph)
            return

        def substitute(match):
            key, filter_name = match.group(1), match.group(2)
            return PlaceholderEngine.format_value(values[key], filter_name)

        full_text = PLACEHOLDER_PATTERN.sub(substitute, full_text)

        paragraph.runs[0].text = full_text

        for run in paragraph.runs[1:]:
            run.text = ""

    @staticmethod
    def _is_empty(value):
        return value is None or not str(value).strip()

    @staticmethod
    def format_value(value, filter_name=None):
        """Convertit une valeur en texte. Sans filtre (cas par defaut,
        `{{cle}}`) : conversion brute via str(), quel que soit le type
        Python de la valeur - aucun formatage n'est jamais devine. Avec un
        filtre explicite (`{{cle|nom_du_filtre}}`) connu de `FILTERS` :
        le filtre correspondant est applique."""
        filter_func = PlaceholderEngine.FILTERS.get(filter_name)
        if filter_func is not None:
            return filter_func(value)
        return str(value)

    @staticmethod
    def _remove_paragraph(paragraph):
        element = paragraph._p
        parent = element.getparent()
        siblings = [child for child in parent if child.tag == element.tag]
        if len(siblings) <= 1:
            # Un parent (cellule de tableau, en-tete/pied de page...) doit
            # toujours conserver au moins un paragraphe (structure OOXML
            # valide) : on vide son contenu plutot que de le retirer.
            for run in paragraph.runs:
                run.text = ""
            return
        parent.remove(element)
