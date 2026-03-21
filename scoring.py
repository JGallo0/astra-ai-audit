def classify_status(score: float) -> str:
    if score >= 80:
        return "Conforme"
    elif score >= 50:
        return "Parcialmente conforme"
    elif score > 0:
        return "Não conforme"
    return "Não evidenciado"


def classify_risk(score: float) -> str:
    if score >= 80:
        return "baixo"
    elif score >= 50:
        return "medio"
    return "alto"
