from typing import Any, Dict, List


VALID_AUDIT_STATUSES = [
    "Conforme",
    "Parcialmente conforme",
    "Não conforme",
    "Não evidenciado",
    "Inconsistência documental",
    "Erro de análise",
]

VALID_RISK_LEVELS = [
    "baixo",
    "medio",
    "alto",
]


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clip_int(
    value: Any,
    default: int = 0,
    min_value: int = 0,
    max_value: int = 100,
) -> int:
    try:
        out = int(round(float(value)))
    except Exception:
        out = default
    return max(min_value, min(max_value, out))


def normalize_status(status: str) -> str:
    raw = safe_str(status).lower()

    mapping = {
        "conforme": "Conforme",
        "compliant": "Conforme",
        "parcial": "Parcialmente conforme",
        "partial": "Parcialmente conforme",
        "partially compliant": "Parcialmente conforme",
        "parcialmente conforme": "Parcialmente conforme",
        "não conforme": "Não conforme",
        "nao conforme": "Não conforme",
        "non-compliant": "Não conforme",
        "not compliant": "Não conforme",
        "não evidenciado": "Não evidenciado",
        "nao evidenciado": "Não evidenciado",
        "not evidenced": "Não evidenciado",
        "insufficient evidence": "Não evidenciado",
        "inconsistência documental": "Inconsistência documental",
        "inconsistencia documental": "Inconsistência documental",
        "document inconsistency": "Inconsistência documental",
        "erro de análise": "Erro de análise",
        "erro de analise": "Erro de análise",
        "analysis error": "Erro de análise",
    }

    return mapping.get(raw, "Erro de análise")


def normalize_risk(risk: str) -> str:
    raw = safe_str(risk).lower()

    if raw == "médio":
        return "medio"
    if raw in VALID_RISK_LEVELS:
        return raw
    return "alto"


def evidence_present(project_evidence: str) -> bool:
    text = safe_str(project_evidence)
    if not text:
        return False

    negative_patterns = [
        "não foi possível identificar evidência",
        "nao foi possivel identificar evidencia",
        "nenhuma evidência",
        "nenhuma evidencia",
        "não identificado",
        "nao identificado",
        "not identified",
        "not found",
        "insufficient evidence",
        "sem evidência",
        "sem evidencia",
    ]

    lowered = text.lower()
    return not any(pattern in lowered for pattern in negative_patterns)


def methodology_present(methodology_basis: str) -> bool:
    text = safe_str(methodology_basis)
    if not text:
        return False

    negative_patterns = [
        "não foi possível identificar base metodológica",
        "nao foi possivel identificar base metodologica",
        "nenhuma base metodológica",
        "nenhuma base metodologica",
        "não identificado",
        "nao identificado",
        "not identified",
        "not found",
        "insufficient evidence",
    ]

    lowered = text.lower()
    return not any(pattern in lowered for pattern in negative_patterns)


def count_keyword_hits(text: str, keywords: List[str]) -> int:
    lowered = safe_str(text).lower()
    if not lowered:
        return 0
    return sum(1 for keyword in keywords if keyword in lowered)


def derive_score(
    project_evidence: str,
    methodology_basis: str,
    gap: str,
    recommendation: str,
    notes: str = "",
    weight: int = 1,
) -> int:
    score = 0

    if evidence_present(project_evidence):
        score += 45

    if methodology_present(methodology_basis):
        score += 25

    combined = " ".join(
        [
            safe_str(gap).lower(),
            safe_str(recommendation).lower(),
            safe_str(notes).lower(),
        ]
    )

    negative_markers = [
        "não foi possível",
        "nao foi possivel",
        "ausência",
        "ausencia",
        "insuficiente",
        "falt",
        "missing",
        "not identified",
        "not found",
        "incomplete",
        "inconsist",
        "conflict",
        "não atende",
        "nao atende",
        "não demonstrado",
        "nao demonstrado",
        "não comprovado",
        "nao comprovado",
    ]

    positive_markers = [
        "robusto",
        "consistente",
        "adequado",
        "claro",
        "suficiente",
        "evidenciado",
        "documentado",
        "compatível",
        "compativel",
        "aderente",
        "demonstrado",
        "comprovado",
    ]

    neg_hits = count_keyword_hits(combined, negative_markers)
    pos_hits = count_keyword_hits(combined, positive_markers)

    score += pos_hits * 8
    score -= neg_hits * 10

    weight_value = clip_int(weight, default=1, min_value=1, max_value=10)
    if weight_value > 1:
        score += min(weight_value - 1, 4)

    return clip_int(score, default=0, min_value=0, max_value=100)


def classify_status(
    score: int,
    evidence_found: bool,
    methodology_found: bool,
    confidence: int = 100,
) -> str:
    score = clip_int(score, default=0)
    confidence = clip_int(confidence, default=100)

    if not evidence_found:
        return "Não evidenciado"

    if evidence_found and not methodology_found:
        if score >= 80:
            return "Parcialmente conforme"
        if score >= 1:
            return "Parcialmente conforme"
        return "Não evidenciado"

    if confidence < 20 and score < 50:
        return "Erro de análise"

    if score >= 80:
        return "Conforme"
    if score >= 50:
        return "Parcialmente conforme"
    if score > 0:
        return "Não conforme"
    return "Não evidenciado"


def classify_risk(
    score: int,
    confidence: int,
    status: str,
) -> str:
    score = clip_int(score, default=0)
    confidence = clip_int(confidence, default=0)
    status = normalize_status(status)

    if status in {
        "Não conforme",
        "Não evidenciado",
        "Erro de análise",
        "Inconsistência documental",
    }:
        return "alto"

    if confidence < 50:
        return "medio"

    if score < 80:
        return "medio"

    return "baixo"


def infer_gap(status: str) -> str:
    status = normalize_status(status)

    if status == "Conforme":
        return "Não foi identificada lacuna material relevante com base nos trechos analisados."
    if status == "Parcialmente conforme":
        return "Há evidência parcial, porém ainda faltam elementos documentais e/ou operacionais para robustez metodológica."
    if status == "Não conforme":
        return "A evidência disponível do projeto não atende adequadamente ao critério metodológico recuperado."
    if status == "Não evidenciado":
        return "Não foi possível localizar evidência documental suficiente do projeto para suportar o requisito."
    if status == "Inconsistência documental":
        return "Os trechos recuperados apresentam conflito ou ambiguidade relevante."
    return "Não foi possível estabelecer lacuna com segurança."


def infer_recommendation(status: str) -> str:
    status = normalize_status(status)

    if status == "Conforme":
        return "Manter os registros e evidências organizados para futura verificação."
    if status == "Parcialmente conforme":
        return "Complementar a documentação e fortalecer a rastreabilidade e a robustez da evidência."
    if status == "Não conforme":
        return "Revisar a aderência metodológica e incluir evidências objetivas que atendam ao requisito."
    if status == "Não evidenciado":
        return "Inserir documentação específica e evidência verificável para o requisito."
    if status == "Inconsistência documental":
        return "Reconciliar as inconsistências entre documentos e consolidar uma versão controlada."
    return "Revisar manualmente o item."


def assess_requirement_result(
    requirement: Dict[str, Any],
    project_evidence: str,
    methodology_basis: str,
    gap: str,
    recommendation: str,
    confidence: Any,
    notes: str = "",
) -> Dict[str, Any]:
    weight = requirement.get("weight", 1)
    confidence_value = clip_int(confidence, default=0)

    evidence_found = evidence_present(project_evidence)
    methodology_found = methodology_present(methodology_basis)

    score = derive_score(
        project_evidence=project_evidence,
        methodology_basis=methodology_basis,
        gap=gap,
        recommendation=recommendation,
        notes=notes,
        weight=weight,
    )

    status = classify_status(
        score=score,
        evidence_found=evidence_found,
        methodology_found=methodology_found,
        confidence=confidence_value,
    )

    risk = classify_risk(
        score=score,
        confidence=confidence_value,
        status=status,
    )

    final_gap = safe_str(gap) or infer_gap(status)
    final_recommendation = safe_str(recommendation) or infer_recommendation(status)

    return {
        "requirement_id": safe_str(requirement.get("id", "")),
        "module": safe_str(requirement.get("module", "")),
        "title": safe_str(requirement.get("title", "")),
        "status": status,
        "risk": risk,
        "score": score,
        "confidence": confidence_value,
        "project_evidence": safe_str(project_evidence),
        "methodology_basis": safe_str(methodology_basis),
        "gap": final_gap,
        "recommendation": final_recommendation,
        "notes": safe_str(notes),
    }


def calculate_weighted_overall_score(results: List[Dict[str, Any]]) -> float:
    if not results:
        return 0.0

    total_weighted_score = 0.0
    total_weight = 0.0

    for item in results:
        score = clip_int(item.get("score", 0), default=0)
        weight = item.get("weight", 1)

        try:
            weight_value = float(weight)
        except Exception:
            weight_value = 1.0

        if weight_value <= 0:
            weight_value = 1.0

        total_weighted_score += score * weight_value
        total_weight += weight_value

    if total_weight == 0:
        return 0.0

    return round(total_weighted_score / total_weight, 1)


def calculate_average_confidence(results: List[Dict[str, Any]]) -> float:
    if not results:
        return 0.0

    values = [clip_int(item.get("confidence", 0), default=0) for item in results]
    return round(sum(values) / len(values), 1)


def summarize_status_counts(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in results:
        status = normalize_status(item.get("status", "Erro de análise"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def summarize_risk_counts(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in results:
        risk = normalize_risk(item.get("risk", "alto"))
        counts[risk] = counts.get(risk, 0) + 1
    return counts


def summarize_module_scores(results: List[Dict[str, Any]]) -> Dict[str, float]:
    grouped: Dict[str, List[int]] = {}

    for item in results:
        module = safe_str(item.get("module", "Sem módulo"))
        score = clip_int(item.get("score", 0), default=0)
        grouped.setdefault(module, []).append(score)

    return {
        module: round(sum(scores) / len(scores), 1) if scores else 0.0
        for module, scores in grouped.items()
    }


def summarize_module_confidence(results: List[Dict[str, Any]]) -> Dict[str, float]:
    grouped: Dict[str, List[int]] = {}

    for item in results:
        module = safe_str(item.get("module", "Sem módulo"))
        confidence = clip_int(item.get("confidence", 0), default=0)
        grouped.setdefault(module, []).append(confidence)

    return {
        module: round(sum(values) / len(values), 1) if values else 0.0
        for module, values in grouped.items()
    }


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {
            "total_requirements": 0,
            "overall_score": 0.0,
            "overall_confidence": 0.0,
            "status_counts": {},
            "risk_counts": {},
            "module_scores": {},
            "module_confidence": {},
        }

    return {
        "total_requirements": len(results),
        "overall_score": calculate_weighted_overall_score(results),
        "overall_confidence": calculate_average_confidence(results),
        "status_counts": summarize_status_counts(results),
        "risk_counts": summarize_risk_counts(results),
        "module_scores": summarize_module_scores(results),
        "module_confidence": summarize_module_confidence(results),
    }
