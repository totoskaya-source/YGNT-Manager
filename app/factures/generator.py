from pathlib import Path

from app.documents.placeholder_engine import PlaceholderEngine

LOGO_MARKER = "{{producteur_logo}}"
LOGO_WIDTH_INCHES = 1.5


class FactureGenerator:
    def __init__(self, template_path):
        self.template_path = Path(template_path)

    def generate(self, facture, output_path):
        from docx import Document

        doc = Document(self.template_path)
        values = facture.to_dict()

        PlaceholderEngine.replace_in_document(doc, values)
        self._insert_logo(doc, getattr(facture, "producteur_logo_path", ""))

        doc.save(output_path)

    def _insert_logo(self, doc, logo_path):
        """Remplace le marqueur {{producteur_logo}} par l'image du Producteur si
        elle existe sur le disque, sinon efface simplement le marqueur. Le
        chemin provient exclusivement de l'instantane stocke dans la Facture,
        jamais d'une relecture de la table Producteurs."""
        from docx.shared import Inches

        for paragraph in doc.paragraphs:
            if LOGO_MARKER not in paragraph.text:
                continue

            for run in paragraph.runs:
                run.text = ""

            if paragraph.runs:
                target_run = paragraph.runs[0]
            else:
                target_run = paragraph.add_run()

            if logo_path and Path(logo_path).exists():
                target_run.add_picture(logo_path, width=Inches(LOGO_WIDTH_INCHES))
