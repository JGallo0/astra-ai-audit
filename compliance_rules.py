from typing import Dict


def clip_int(value, default=0, min_value=0, max_value=100):
    try:
        v = int(round(float(value)))
    except Exception:
        v = default
    return max(min_value, min(max_value, v))


# =========================================================
# STATUS CLASSIFICATION
# =========================================================
def classify_status(score: int, confidence: int, evidence_present: bool) -> str:
    score = clip_int(score)
    confidence = clip_int(confidence)

    if not evidence_present:
        return "Não evidenciado"

    if confidence < 20 and score < 40:
        return "Erro de análise"

    if score >= 80:
        return "Conforme"
    if score >= 55:
        return "Parcialmente conforme"
    if score > 0:
        return "Não conforme"

    return "Não evidenciado"


# =========================================================
# RISK CLASSIFICATION
# =========================================================
def classify_risk(score: int, confidence: int, status: str) -> str:
    if status in ["Não conforme", "Não evidenciado", "Erro de análise"]:
        return "alto"

    if status == "Parcialmente conforme":
        return "medio"

    if status == "Conforme":
        if confidence >= 70 and score >= 80:
            return "baixo"
        return "medio"

    return "alto"


# =========================================================
# SCORE ENGINE (DETALHADO)
# =========================================================
def calculate_score(
    project_evidence: str,
    methodology_basis: str,
    gap: str,
    recommendation: str,
    notes: str,
) -> int:

    score = 0

    pe = project_evidence.lower()
    mb = methodology_basis.lower()
    gp = gap.lower()
    rc = recommendation.lower()
    nt = notes.lower()

    # ---------------------------
    # EVIDÊNCIA DO PROJETO (0–40)
    # ---------------------------
    if pe.strip():
        score += 20

        if len(pe) > 120:
            score += 5
        if len(pe) > 250:
            score += 5
        if len(pe) > 400:
            score += 5

        strong_terms = [
            "batch",
            "lote",
            "mrv",
            "traceability",
            "rastreabilidade",
            "laboratório",
            "iso",
            "astm",
        ]

        score += min(sum(1 for t in strong_terms if t in pe), 5)

    # ---------------------------
    # BASE METODOLÓGICA (0–30)
    # ---------------------------
    if mb.strip():
        score += 15

        if len(mb) > 120:
            score += 5
        if len(mb) > 250:
            score += 5

        method_terms = [
            "requirement",
            "criteria",
            "threshold",
            "eligibility",
            "methodology",
        ]

        score += min(sum(1 for t in method_terms if t in mb), 5)

    # ---------------------------
    # GAP (-30 → +10)
    # ---------------------------
    if gp:
        if "no material gap" in gp or "não foi identificada lacuna" in gp:
            score += 8
        else:
            score -= 10

            if any(x in gp for x in ["missing", "ausência", "incomplete"]):
                score -= 5

            if any(x in gp for x in ["not compliant", "não atende"]):
                score -= 10

    # ---------------------------
    # RECOMENDAÇÃO (+0–5)
    # ---------------------------
    if rc:
        score += 2

    # ---------------------------
    # NOTAS (+0–5)
    # ---------------------------
    if nt:
        score += 2

    # ---------------------------
    # NORMALIZAÇÃO FINAL
    # ---------------------------
    return clip_int(score, default=0)


# =========================================================
# CONFIDENCE ENGINE
# =========================================================
def calculate_confidence(
    project_evidence: str,
    methodology_basis: str,
    gap: str,
    recommendation: str,
    notes: str,
) -> int:
    score = 0

    pe = (project_evidence or "").lower()
    mb = (methodology_basis or "").lower()
    gp = (gap or "").lower()
    rc = (recommendation or "").lower()
    nt = (notes or "").lower()

    combined = " ".join([pe, mb, gp, rc, nt])

    # ---------------------------
    # PRESENÇA BASE (0–45)
    # ---------------------------
    if pe.strip():
        score += 20
    if mb.strip():
        score += 15
    if gp.strip():
        score += 4
    if rc.strip():
        score += 3
    if nt.strip():
        score += 3

    # ---------------------------
    # DENSIDADE / DETALHE (0–20)
    # ---------------------------
    if len(pe) > 120:
        score += 4
    if len(pe) > 250:
        score += 4
    if len(pe) > 400:
        score += 4

    if len(mb) > 120:
        score += 3
    if len(mb) > 250:
        score += 3
    if len(mb) > 400:
        score += 2

    # ---------------------------
    # TERMOS TÉCNICOS FORTES (0–20)
    # ---------------------------
    strong_terms = [
        "astm",
        "iso",
        "iso/iec 17025",
        "mrv",
        "batch",
        "lote",
        "traceability",
        "rastreabilidade",
        "h/corg",
        "fixed carbon",
        "carbono fixo",
        "laboratório",
        "laudo",
        "sample",
        "sampling",
        "amostra",
    ]
    score += min(sum(1 for t in strong_terms if t in combined), 10)

    # ---------------------------
    # SINAIS DE FRAGILIDADE (-25)
    # ---------------------------
    weak_terms = [
        "unclear",
        "generic",
        "not clear",
        "não identificado",
        "não localizado",
        "insufficient",
        "insuficiente",
        "ausência",
        "incomplete",
        "incompleto",
    ]
    score -= min(sum(1 for t in weak_terms if t in combined) * 4, 20)

    # ---------------------------
    # AJUSTES POR LACUNA EXPLÍCITA
    # ---------------------------
    if gp:
        if "no material gap" in gp or "não foi identificada lacuna" in gp:
            score += 6
        elif any(x in gp for x in ["não atende", "not compliant", "ausência", "missing"]):
            score -= 8

    # ---------------------------
    # NORMALIZAÇÃO FINAL
    # ---------------------------
    return clip_int(score, default=55, min_value=15, max_value=95)


    # ---------------------------
    # PENALIZAÇÃO POR GAP RELEVANTE
    # ---------------------------
    if gp:
        if any(x in gp for x in [
            "não há evidência",
            "não foram apresentados",
            "não localizado",
            "ausência",
            "missing",
            "not provided",
            "não atende",
        ]):
            score -= 25
   


