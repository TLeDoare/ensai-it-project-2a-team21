"""Tests de resoudre_chevauchements : fusion des positions qui se recouvrent (étape entre l'analyse et le caviardage)."""

from business_object.analyser.overlap import resoudre_chevauchements
from business_object.types import PII, Analyser, Position

CONTENU = "Carte 4111 1111 1111 1111, contact : jean@exemple.fr"


def position(debut: int, fin: int, pii: PII, source: Analyser = Analyser.Regex) -> Position:
    """Construit une position ; la confiance suit la source (1.0 regex, 0.8 LLM)."""
    confiance = 1.0 if source == Analyser.Regex else 0.8
    return Position((debut, fin), pii, confiance, source)


def test_aucune_position():
    """Sans position, le résultat est vide."""
    assert resoudre_chevauchements(set(), CONTENU) == set()


def test_positions_disjointes_conservees():
    """Deux positions qui ne se touchent pas restent séparées et inchangées."""
    carte = position(6, 25, PII.PAN)
    email = position(37, 52, PII.email)

    resultat = resoudre_chevauchements({carte, email}, CONTENU)

    assert resultat == {carte, email}


def test_chevauchement_fusionne_en_une_zone():
    """Deux positions qui se recouvrent donnent une seule zone, qui couvre leur union."""
    carte = position(6, 25, PII.PAN)
    debut_carte = position(0, 10, PII.name, Analyser.LLM)

    resultat = resoudre_chevauchements({carte, debut_carte}, CONTENU)

    assert len(resultat) == 1
    assert next(iter(resultat)).indices == (0, 25)


def test_etiquette_validee_prioritaire():
    """L'étiquette gardée est celle du span validé (Luhn), même s'il est plus court que l'autre."""
    carte = position(6, 25, PII.PAN)  # numéro valide au sens de Luhn
    zone_large = position(0, 26, PII.name, Analyser.LLM)  # plus long, mais sans validation

    fusion = next(iter(resoudre_chevauchements({carte, zone_large}, CONTENU)))

    assert fusion.PII == PII.PAN
    assert fusion.analyser_source == Analyser.Regex


def test_sans_validation_le_plus_long_gagne():
    """Si aucun span n'est validé, l'étiquette du plus long est gardée."""
    court = position(37, 41, PII.first_name, Analyser.LLM)
    long = position(37, 52, PII.email)

    fusion = next(iter(resoudre_chevauchements({court, long}, CONTENU)))

    assert fusion.PII == PII.email
    assert fusion.indices == (37, 52)


def test_positions_contigues_non_fusionnees():
    """Deux positions qui se suivent sans se recouvrir (fin == début) restent séparées."""
    gauche = position(0, 5, PII.name, Analyser.LLM)
    droite = position(5, 10, PII.place, Analyser.LLM)

    assert len(resoudre_chevauchements({gauche, droite}, CONTENU)) == 2
