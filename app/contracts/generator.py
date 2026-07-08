from pathlib import Path
import os


class ContractGenerator:
    ORGANIZER_DETAILS = (
        ("Forme juridique", "organisateur_forme"),
        ("Adresse", "organisateur_adresse"),
        ("Code postal", "organisateur_postal_code"),
        ("Ville", "organisateur_city"),
        ("SIRET", "organisateur_siret"),
        ("Telephone", "organisateur_phone"),
        ("Email", "organisateur_email"),
        ("Code APE", "organisateur_ape"),
        ("Licence spectacle", "organisateur_licence"),
        ("TVA intracommunautaire", "organisateur_tva"),
        ("Representee par", "organisateur_representant"),
        ("Fonction du representant", "organisateur_fonction"),
    )

    def __init__(self, template_path):
        self.template_path = Path(template_path)

    def generate(self, contract, output_path):
        from docx import Document

        doc = Document(self.template_path)
        values = contract.to_dict()

        self.replace_in_document(doc, values)
        self.append_organizer_details(doc, values)

        doc.save(output_path)
        os.startfile(output_path)

    def replace_in_document(self, doc, values):
        for paragraph in doc.paragraphs:
            self.replace_paragraph(paragraph, values)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self.replace_paragraph(paragraph, values)

    def replace_paragraph(self, paragraph, values):
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

    def append_organizer_details(self, doc, values):
        details = [
            (label, values.get(key, ""))
            for label, key in self.ORGANIZER_DETAILS
            if values.get(key)
        ]

        if not details:
            return

        doc.add_paragraph()
        title = doc.add_paragraph("Informations organisateur")
        title.runs[0].bold = True

        table = doc.add_table(rows=0, cols=2)

        for label, value in details:
            cells = table.add_row().cells
            cells[0].text = label
            cells[1].text = str(value)
