# Pour éviter les chevauchements de spans, on fusionne les spans qui se chevauchent en un seul par zone.

from backend.src.business_object.types import Position, Position, Positions


def resoudre_chevauchements(positions: Positions, content: str) -> Positions:
    """Fusionne les spans qui se chevauchent en un seul par zone
    La zone masquée = l'union des zones pr faire du sur-caviardage (texte de sortie pas corrompu)
    Étiquette de la zone = span le plus fiable (validation réussie, puis le plus long ?)
    """
    if not positions:
        return set()

    triees = sorted(positions, key=lambda p: p.indices)
    resolues = set()
    cluster = [triees[0]]
    fin_cluster = triees[0].indices[1]

    for pos in triees[1:]:
        debut, fin = pos.indices
        if debut < fin_cluster: # cas où y a un chevauchement
            cluster.append(pos)
            fin_cluster = max(fin_cluster, fin)
        else: # sinon on fait un nv cluster
            resolues.add(_fusionner(cluster, content))
            cluster = [pos]
            fin_cluster = fin

    resolues.add(_fusionner(cluster, content))
    return resolues


def _fusionner(cluster: list[Position], content: str) -> Position:
    debut = min(p.indices[0] for p in cluster)
    fin = max(p.indices[1] for p in cluster)
    gagnant = max(cluster, key=lambda p: _fiabilite(p, content))
    return Position(
        indices=(debut, fin),          # union des spans
        PII=gagnant.PII,               # étiquette = le + fiable
        confidence=gagnant.confidence,
        analyser_source=gagnant.analyser_source,
    )


def _fiabilite(position: Position, content: str) -> tuple:
    """Renvoie la fiabilité d'un span : (validé, longueur)"""
    texte = content[position.indices[0]:position.indices[1]]
    validateur = VALIDATORS.get(position.PII)
    valide = validateur(texte) if validateur else False
    longueur = position.indices[1] - position.indices[0]
    return (valide, longueur)