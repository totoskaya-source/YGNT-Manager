class DomaineError(Exception):
    """Base des erreurs métier de la plateforme."""


class SocieteInexistante(DomaineError):
    def __init__(self, societe_id: int):
        super().__init__(f"Société {societe_id} introuvable.")


class NomSocieteObligatoire(DomaineError):
    def __init__(self):
        super().__init__("Le nom de la Société est obligatoire.")


class UtilisateurInexistant(DomaineError):
    """Levée aussi bien quand l'Utilisateur n'existe pas du tout que quand il
    appartient à une autre Société que celle du contexte appelant (T4) : les
    deux cas ne sont jamais distingués, pour ne jamais confirmer à un appelant
    l'existence d'une ressource hors de sa Société."""

    def __init__(self, utilisateur_id: int):
        super().__init__(f"Utilisateur {utilisateur_id} introuvable.")


class EmailDejaUtilise(DomaineError):
    def __init__(self, email: str):
        super().__init__(f"L'email {email} est déjà utilisé.")


class RoleInexistant(DomaineError):
    """Même principe que UtilisateurInexistant : un Rôle d'une autre Société
    est indiscernable d'un Rôle qui n'existe pas (T4, isolation multi-tenant)."""

    def __init__(self, role_id: int):
        super().__init__(f"Rôle {role_id} introuvable.")


class NomRoleObligatoire(DomaineError):
    def __init__(self):
        super().__init__("Le nom du Rôle est obligatoire.")


class MotDePasseTropCourt(DomaineError):
    def __init__(self, longueur_minimale: int):
        super().__init__(
            f"Le mot de passe doit contenir au moins {longueur_minimale} caractères."
        )


class IdentifiantsInvalides(DomaineError):
    """Volontairement générique (email ou mot de passe) : ne jamais révéler
    lequel des deux est incorrect, pour éviter l'énumération des comptes."""

    def __init__(self):
        super().__init__("Email ou mot de passe incorrect.")


class JetonInvalide(DomaineError):
    def __init__(self):
        super().__init__("Jeton invalide.")


class JetonExpire(DomaineError):
    def __init__(self):
        super().__init__("Jeton expiré.")


class PrestationInexistante(DomaineError):
    """Même principe que UtilisateurInexistant/RoleInexistant : une Prestation
    d'une autre Société est indiscernable d'une Prestation qui n'existe pas
    (isolation multi-tenant)."""

    def __init__(self, prestation_id: int):
        super().__init__(f"Prestation {prestation_id} introuvable.")


class NomPrestationObligatoire(DomaineError):
    def __init__(self):
        super().__init__("Le nom de la Prestation est obligatoire.")


class DateDebutObligatoire(DomaineError):
    def __init__(self):
        super().__init__("La date de début de la Prestation est obligatoire.")
