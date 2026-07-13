from pathlib import Path

from app.documents.placeholder_engine import PlaceholderEngine


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

        doc.save(output_path)

    def replace_in_document(self, doc, values):
        PlaceholderEngine.replace_in_document(doc, values)

    def replace_paragraph(self, paragraph, values):
        PlaceholderEngine.replace_paragraph(paragraph, values)

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
