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

    pe = project_evidence.lower()
    mb = methodology_basis.lower()

    if pe.strip():
        score += 40
    if mb.strip():
        score += 30

    if gap:
        score += 10

    if recommendation:
        score += 10

    if notes:
        score += 5

    vague_terms = ["unclear", "generic", "not clear"]

    if any(t in (pe + mb) for t in vague_terms):
        score -= 15

    return clip_int(score, default=50, min_value=10, max_value=95)
