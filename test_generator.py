from app.contracts.generator import ContractGenerator

generator = ContractGenerator("templates/contrat_cession.docx")

generator.replace({

    "organisateur_structure": "Ville de Toulon",

    "organisateur_adresse": "Place de la Liberté",

    "prestation_date": "12 août 2026",

    "cession_montant": "1800 €"

})

generator.save("exports/test.docx")

print("Contrat généré.")
