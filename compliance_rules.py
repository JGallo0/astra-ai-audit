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
    pe = (project_evidence or "").lower().strip()
    mb = (methodology_basis or "").lower().strip()
    gp = (gap or "").lower().strip()
    rc = (recommendation or "").lower().strip()
    nt = (notes or "").lower().strip()

    combined = " ".join([pe, mb, gp, rc, nt])

    score = 0

    # =========================================================
    # 1. PRESENÇA BASE DOS CAMPOS (0–42)
    # =========================================================
    if pe:
        score += 18
    if mb:
        score += 12
    if gp:
        score += 5
    if rc:
        score += 4
    if nt:
        score += 3

    # =========================================================
    # 2. DENSIDADE / DETALHE DOCUMENTAL (0–18)
    # =========================================================
    if len(pe) > 80:
        score += 3
    if len(pe) > 180:
        score += 4
    if len(pe) > 320:
        score += 4

    if len(mb) > 80:
        score += 2
    if len(mb) > 180:
        score += 3
    if len(mb) > 320:
        score += 2

    # =========================================================
    # 3. TERMOS TÉCNICOS FORTES / SINAIS DE AUDITABILIDADE (0–20)
    # =========================================================
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
        "carbono fixo",
        "fixed carbon",
        "laboratório",
        "lab report",
        "laudo",
        "sampling",
        "sample",
        "amostra",
        "operator",
        "retention sample",
        "chain of custody",
        "digital record",
        "batch id",
    ]
    score += min(sum(1 for t in strong_terms if t in combined), 10)

    # =========================================================
    # 4. PENALIZAÇÕES POR VAGUEZA / FRAGILIDADE (-24)
    # =========================================================
    weak_terms = [
        "unclear",
        "generic",
        "not clear",
        "não identificado",
        "não localizado",
        "insufficient",
        "insuficiente",
        "incomplete",
        "incompleto",
        "partial",
        "parcial",
    ]
    score -= min(sum(1 for t in weak_terms if t in combined) * 3, 12)

    # =========================================================
    # 5. PENALIZAÇÕES POR AUSÊNCIA DE EVIDÊNCIA CONCRETA (-35)
    # =========================================================
    critical_gap_terms = [
        "não há evidência",
        "não foram apresentados",
        "não localizado",
        "ausência",
        "missing",
        "not provided",
        "não atende",
        "no explicit mention",
        "no information given",
        "not documented",
        "not explicitly stated",
        "not demonstrated",
        "faltam evidências",
        "faltam elementos",
        "não foi evidenciado",
        "não apresenta",
    ]
    score -= min(sum(1 for t in critical_gap_terms if t in gp) * 7, 35)

    # =========================================================
    # 6. AJUSTES POSITIVOS POR GAP FAVORÁVEL (+8)
    # =========================================================
    positive_gap_terms = [
        "no material gap",
        "não foi identificada lacuna",
        "none explicitly identified",
        "sem lacuna relevante",
    ]
    if any(t in gp for t in positive_gap_terms):
        score += 8

    # =========================================================
    # 7. AJUSTE POR EVIDÊNCIA MUITO POBRE (-20)
    # =========================================================
    if pe and len(pe) < 40:
        score -= 8
    if mb and len(mb) < 40:
        score -= 5

    if pe and not any(t in pe for t in strong_terms):
        score -= 4

    # =========================================================
    # 8. BÔNUS POR EVIDÊNCIA E BASE METODOLÓGICA FORTES (+10)
    # =========================================================
    pe_strong = len(pe) > 180 and sum(1 for t in strong_terms if t in pe) >= 2
    mb_strong = len(mb) > 100

    if pe_strong:
        score += 5
    if mb_strong:
        score += 3
    if pe_strong and mb_strong:
        score += 2

    # =========================================================
    # 9. REGRAS DE PISO E TETO CONTEXTUAIS
    # =========================================================
    # Sem evidência do projeto -> confiança não pode ser alta
    if not pe:
        score = min(score, 25)

    # Sem base metodológica -> confiança também deve ser limitada
    if not mb:
        score = min(score, 35)

    # Gap muito crítico limita teto
    if any(t in gp for t in critical_gap_terms):
        score = min(score, 68)

    # Ausência simultânea de evidência concreta e detalhamento metodológico
    if len(pe) < 60 and len(mb) < 60:
        score = min(score, 45)

    # Caso muito robusto e sem lacuna relevante
    if pe_strong and mb_strong and any(t in gp for t in positive_gap_terms):
        score = max(score, 75)

    # =========================================================
    # 10. NORMALIZAÇÃO FINAL
    # =========================================================
    return clip_int(score, default=55, min_value=15, max_value=92)

  
