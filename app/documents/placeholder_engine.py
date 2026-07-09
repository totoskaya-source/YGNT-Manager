"""Moteur commun de remplacement de placeholders {{cle}} dans un document
python-docx. Partage entre le generateur de Contrats et celui de Devis pour
eviter de dupliquer la logique de substitution."""


class PlaceholderEngine:

    @staticmethod
    def replace_in_document(doc, values):
        for paragraph in doc.paragraphs:
            PlaceholderEngine.replace_paragraph(paragraph, values)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        PlaceholderEngine.replace_paragraph(paragraph, values)

    @staticmethod
    def replace_paragraph(paragraph, values):
        if not paragraph.runs:
            return

        full_text = "".join(run.text for run in paragraph.runs)
        original = full_text

        for key, value in values.items():
            full_text = full_text.replace(
                "{{" + key + "}}",
                str(value)
            )

        if full_text == original:
            return

        paragraph.runs[0].text = full_text

        for run in paragraph.runs[1:]:
            run.text = ""
