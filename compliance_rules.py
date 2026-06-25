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
    pe = (project_evidence or "").lower().strip()
    mb = (methodology_basis or "").lower().strip()
    gp = (gap or "").lower().strip()
    rc = (recommendation or "").lower().strip()
    nt = (notes or "").lower().strip()

    combined = " ".join([pe, mb, gp, rc, nt])

    score = 0

    # =========================================================
    # 1. EVIDÊNCIA DO PROJETO (0–42)
    # =========================================================
    if pe:
        score += 18

        if len(pe) > 80:
            score += 4
        if len(pe) > 180:
            score += 4
        if len(pe) > 320:
            score += 4

    evidence_terms = [
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
        "heavy metals",
        "metais pesados",
        "lab report",
        "laudo",
        "sample",
        "sampling",
        "amostra",
        "operator",
        "retention sample",
        "chain of custody",
        "digital record",
        "batch id",
        "report reference",
    ]
    score += min(sum(1 for t in evidence_terms if t in pe), 8)

    # =========================================================
    # 2. BASE METODOLÓGICA (0–24)
    # =========================================================
    if mb:
        score += 10

        if len(mb) > 80:
            score += 3
        if len(mb) > 180:
            score += 3
        if len(mb) > 320:
            score += 2

    method_terms = [
        "requirement",
        "criteria",
        "threshold",
        "eligibility",
        "methodology",
        "protocol",
        "must",
        "shall",
        "required",
        "production and storage protocol",
    ]
    score += min(sum(1 for t in method_terms if t in mb), 6)

    # =========================================================
    # 3. SINAIS DE EVIDÊNCIA CONCRETA (+0–12)
    # =========================================================
    concrete_evidence_terms = [
        "for each batch",
        "each batch",
        "batch id",
        "lab report reference",
        "digital record",
        "retention sample",
        "12 months",
        "iso/iec 17025",
        "fixed carbon",
        "volatile matter",
        "ash",
        "moisture",
        "total carbon",
        "pahs",
        "heavy metals",
        "sampling date",
        "operator",
        "reactor conditions",
    ]
    score += min(sum(1 for t in concrete_evidence_terms if t in pe), 8)

    # =========================================================
    # 4. GAP / LACUNA (-40 → +10)
    # =========================================================
    positive_gap_terms = [
        "no material gap",
        "não foi identificada lacuna",
        "none explicitly identified",
        "sem lacuna relevante",
    ]
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
    moderate_gap_terms = [
        "partial",
        "parcial",
        "incomplete",
        "incompleto",
        "not fully",
        "carece",
        "falta maior detalhe",
        "needs more detail",
        "not fully demonstrated",
        "não está completa",
        "detalhamento insuficiente",
    ]

    if gp:
        if any(t in gp for t in positive_gap_terms):
            score += 10
        else:
            score -= 8

            score -= min(sum(1 for t in critical_gap_terms if t in gp) * 6, 24)
            score -= min(sum(1 for t in moderate_gap_terms if t in gp) * 3, 12)

    # =========================================================
    # 5. RECOMENDAÇÃO (+0–4)
    # =========================================================
    if rc:
        score += 2
        if len(rc) > 120:
            score += 1
        if any(x in rc for x in ["incluir", "fornecer", "documentar", "apresentar", "attach", "provide", "document"]):
            score += 1

    # =========================================================
    # 6. NOTAS (+0–4)
    # =========================================================
    if nt:
        score += 2
        if len(nt) > 100:
            score += 1
        if any(x in nt for x in ["aligns", "alinha", "rastreabilidade", "traceability", "documented", "documentado"]):
            score += 1

    # =========================================================
    # 7. PENALIZAÇÕES POR EVIDÊNCIA FRACA (-18)
    # =========================================================
    weak_evidence_terms = [
        "generic",
        "unclear",
        "not clear",
        "não identificado",
        "insufficient",
        "insuficiente",
    ]
    score -= min(sum(1 for t in weak_evidence_terms if t in combined) * 3, 12)

    if pe and len(pe) < 50:
        score -= 6

    if mb and len(mb) < 50:
        score -= 3

    # =========================================================
    # 8. LIMITADORES CONTEXTUAIS
    # =========================================================
    # Sem evidência do projeto, score não pode passar de 20
    if not pe:
        score = min(score, 20)

    # Sem base metodológica, score não pode passar de 35
    if not mb:
        score = min(score, 35)

    # Gap crítico impede score alto
    if any(t in gp for t in critical_gap_terms):
        score = min(score, 58)

    # Gap moderado impede score excelente
    if any(t in gp for t in moderate_gap_terms):
        score = min(score, 72)

    # Evidência forte + base metodológica forte + sem lacuna relevante
    pe_strong = len(pe) > 180 and sum(1 for t in evidence_terms if t in pe) >= 3
    mb_strong = len(mb) > 100 and sum(1 for t in method_terms if t in mb) >= 2
    no_material_gap = any(t in gp for t in positive_gap_terms)

    if pe_strong and mb_strong and no_material_gap:
        score = max(score, 78)

    # =========================================================
    # 9. NORMALIZAÇÃO FINAL
    # =========================================================
    return clip_int(score, default=0, min_value=0, max_value=95)

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

  
