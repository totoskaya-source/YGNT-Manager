from ygnt_web.core.security.passwords import hacher_mot_de_passe, verifier_mot_de_passe


def test_verifier_le_bon_mot_de_passe_reussit():
    hash_stocke = hacher_mot_de_passe("s3cret!!")

    assert verifier_mot_de_passe("s3cret!!", hash_stocke) is True


def test_verifier_un_mauvais_mot_de_passe_echoue():
    hash_stocke = hacher_mot_de_passe("s3cret!!")

    assert verifier_mot_de_passe("autre-mot-de-passe", hash_stocke) is False


def test_deux_hachages_du_meme_mot_de_passe_sont_differents():
    hash_1 = hacher_mot_de_passe("s3cret!!")
    hash_2 = hacher_mot_de_passe("s3cret!!")

    assert hash_1 != hash_2
    assert verifier_mot_de_passe("s3cret!!", hash_1) is True
    assert verifier_mot_de_passe("s3cret!!", hash_2) is True
