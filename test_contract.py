from pathlib import Path

from app.contracts.generator import ContractGenerator
from app.models.contract import Contract

contract = Contract()

contract.organisateur_structure = "Ville de test"
contract.organisateur_forme = "Collectivité"
contract.organisateur_adresse = "301 rue du Pigeonnier"
contract.organisateur_siret = "12345678900011"
contract.organisateur_representant = "M. Dupont"
contract.organisateur_fonction = "Maire"

contract.spectacle_nom = "Sanfuego"
contract.spectacle_duree = "2h"

contract.prestation_date = "08/07/2026"
contract.prestation_adresse = "Fréjus"

contract.prestation_convocation = "18h"
contract.prestation_horaire = "20h"

contract.cession_montant = "650"

generator = ContractGenerator("templates/contrat_cession.docx")

Path("exports").mkdir(exist_ok=True)

generator.generate(
    contract,
    "exports/test_contrat.docx"
)

print("Contrat généré.")