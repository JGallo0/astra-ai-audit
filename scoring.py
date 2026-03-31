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

def get_engine_requirement_score(item: Dict[str, Any]) -> int:
    """
    Prioriza o score estruturado da V2 do requirement_logic.py.
    Fallback:
    1) requirement_score
    2) score
    3) status -> score heurístico simples
    """
    requirement_score = item.get("requirement_score")
    if requirement_score is not None:
        return clip_int(requirement_score, default=0)

    legacy_score = item.get("score")
    if legacy_score is not None:
        return clip_int(legacy_score, default=0)

    status = safe_str(item.get("status", "")).strip().lower()

    # Normaliza ambos padrões (engine + scoring)
    if status in ["compliant", "conforme"]:
        return 100
    if status in ["partial", "parcialmente conforme"]:
        return 50
    if status in ["future_evidence_required"]:
        return 35
    if status in ["not_applicable", "não aplicável", "nao aplicavel"]:
        return 0
    if status in ["non_compliant", "não conforme", "nao conforme"]:
        return 0
    return 0


def get_engine_requirement_score_fraction(item: Dict[str, Any]) -> float:
    """
    Mesmo helper acima, mas em escala 0.0–1.0.
    """
    return round(get_engine_requirement_score(item) / 100.0, 4)
    
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
        status = safe_str(item.get("status", "")).strip().lower()

        if status in ["not_applicable", "não aplicável", "nao aplicavel"]:
            continue

        score = get_engine_requirement_score(item)
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
        status = safe_str(item.get("status", "")).strip().lower()

        if status in ["not_applicable", "não aplicável", "nao aplicavel"]:
            continue

        module = safe_str(item.get("module", "Sem módulo"))
        score = get_engine_requirement_score(item)
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

    compliance_summary = calculate_compliance_score(results)

    return {
        "total_requirements": len(results),
        "overall_score": calculate_weighted_overall_score(results),
        "overall_confidence": calculate_average_confidence(results),
        "status_counts": summarize_status_counts(results),
        "risk_counts": summarize_risk_counts(results),
        "module_scores": summarize_module_scores(results),
        "module_confidence": summarize_module_confidence(results),
        "compliance_score": compliance_summary.get("score", 0.0),
        "compliance_classification": classify_compliance_score(
            compliance_summary.get("score", 0.0)
        ),
    }

# scoring.py

MODULE_WEIGHTS = {
    "Eligibility": 2.0,
    "Ownership": 1.8,
    "MRV": 1.8,
    "Storage/End Use": 1.6,
    "Carbon Accounting": 1.5,
    "System Boundary": 1.4,
    "Durability": 1.4,
    "Traceability": 1.3,
    "Feedstock": 1.2,
    "Technology": 1.1,
    "Biochar Quality": 1.1,
    "Biochar Carbon Quantification": 1.1,
    "Baseline": 1.0,
    "Additionality": 1.0,
    "Leakage": 1.0,
    "Uncertainty": 0.9,
    "LCA": 0.9,
    "Reversal Risk": 0.9,
    "Safeguards": 0.8,
    "Regulatory Compliance": 0.8,
}


def _status_factor(status: str) -> float:
    status = str(status or "").strip().lower()

    if status == "compliant":
        return 1.0
    if status == "partial":
        return 0.5
    if status == "future_evidence_required":
        return 0.65
    if status == "error":
        return 0.2
    if status == "non_compliant":
        return 0.0
    return 0.0


def _safe_req_score(item: dict) -> float:
    raw = item.get("requirement_score_normalized", item.get("requirement_score", 0))
    try:
        raw = float(raw)
    except Exception:
        raw = 0.0
    return max(0.0, min(100.0, raw))


def _combine_status_and_requirement_score(item: dict) -> float:
    """
    Score final do requisito em escala 0–1.
    Dá peso maior ao status do que ao requirement_score,
    para impedir score inflado quando há non-compliance real.
    """
    status_component = _status_factor(item.get("status")) * 100.0
    req_component = _safe_req_score(item)

    combined = (0.70 * status_component) + (0.30 * req_component)
    return max(0.0, min(100.0, combined)) / 100.0


def _compute_module_scores(results):
    module_buckets = {}

    for item in results or []:
        status = str(item.get("status", "")).strip().lower()
        if status == "not_applicable":
            continue

        module = item.get("module") or "Unassigned"

        if module not in module_buckets:
            module_buckets[module] = {
                "weighted_sum": 0.0,
                "weight_sum": 0.0,
            }

        module_weight = MODULE_WEIGHTS.get(module, 1.0)
        item_score = _combine_status_and_requirement_score(item)

        module_buckets[module]["weighted_sum"] += item_score * module_weight
        module_buckets[module]["weight_sum"] += module_weight

    module_scores = {}

    for module, data in module_buckets.items():
        if data["weight_sum"] > 0:
            module_scores[module] = round((data["weighted_sum"] / data["weight_sum"]) * 100.0, 2)
        else:
            module_scores[module] = 0.0

    return module_scores


def _apply_module_penalties(base_score: float, module_scores: dict):
    score = float(base_score)
    penalties_applied = []

    penalty_rules = [
        ("Eligibility", 70.0, 0.75, "Eligibility module below threshold"),
        ("MRV", 60.0, 0.85, "MRV module below threshold"),
        ("Storage/End Use", 60.0, 0.90, "Storage/End Use module below threshold"),
        ("Traceability", 50.0, 0.92, "Traceability module below threshold"),
    ]

    for module_name, threshold, multiplier, reason in penalty_rules:
        module_score = module_scores.get(module_name)
        if module_score is None:
            continue
        if module_score < threshold:
            score *= multiplier
            penalties_applied.append({
                "module": module_name,
                "module_score": module_score,
                "threshold": threshold,
                "multiplier": multiplier,
                "reason": reason,
            })

    return round(max(0.0, min(100.0, score)), 2), penalties_applied


def _apply_eligibility_hard_gate(score: float, results: list):
    """
    Hard gate de elegibilidade.
    Requisitos críticos de elegibilidade não podem permitir score de readiness alto.
    """
    score = float(score)
    eligibility_override = None
    hard_gate_reasons = []

    status_by_id = {
        str(item.get("requirement_id", "")).strip(): str(item.get("status", "")).strip().lower()
        for item in (results or [])
    }

    # Gate 1 — não elegível
    not_eligible_ids = ["ELIG_001", "ELIG_002", "OWN_001"]
    if any(status_by_id.get(req_id) == "non_compliant" for req_id in not_eligible_ids):
        score = min(score, 39.0)
        eligibility_override = "NOT_ELIGIBLE"
        for req_id in not_eligible_ids:
            if status_by_id.get(req_id) == "non_compliant":
                hard_gate_reasons.append(f"{req_id} is non_compliant")

    # Gate 2 — elegibilidade condicional no máximo
    conditional_ids = ["STOR_001", "MRV_001"]
    if eligibility_override != "NOT_ELIGIBLE":
        if any(status_by_id.get(req_id) == "non_compliant" for req_id in conditional_ids):
            score = min(score, 49.0)
            eligibility_override = "CONDITIONALLY_ELIGIBLE"
            for req_id in conditional_ids:
                if status_by_id.get(req_id) == "non_compliant":
                    hard_gate_reasons.append(f"{req_id} is non_compliant")

    return round(max(0.0, min(100.0, score)), 2), eligibility_override, hard_gate_reasons


def calculate_compliance_score(results):
    results = results or []

    status_counts = {
        "compliant": 0,
        "partial": 0,
        "future_evidence_required": 0,
        "non_compliant": 0,
        "error": 0,
        "not_applicable": 0,
    }

    applicable_results = []

    for item in results:
        status = str(item.get("status", "")).strip().lower()
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["error"] += 1

        if status != "not_applicable":
            applicable_results.append(item)

    applicable_requirements = len(applicable_results)

    if applicable_requirements == 0:
        return {
            "score": 0.0,
            "applicable_requirements": 0,
            "compliant": 0,
            "partial": 0,
            "future_evidence_required": 0,
            "non_compliant": 0,
            "error": 0,
            "not_applicable": status_counts["not_applicable"],
            "module_scores": {},
            "module_penalties": [],
            "eligibility_override": None,
            "hard_gate_reasons": [],
        }

    weighted_sum = 0.0
    total_weight = 0.0

    for item in applicable_results:
        module = item.get("module") or "Unassigned"
        module_weight = MODULE_WEIGHTS.get(module, 1.0)
        item_score = _combine_status_and_requirement_score(item)

        weighted_sum += item_score * module_weight
        total_weight += module_weight

    base_score = (weighted_sum / total_weight) * 100.0 if total_weight > 0 else 0.0
    base_score = round(max(0.0, min(100.0, base_score)), 2)

    module_scores = _compute_module_scores(applicable_results)
    penalized_score, module_penalties = _apply_module_penalties(base_score, module_scores)
    final_score, eligibility_override, hard_gate_reasons = _apply_eligibility_hard_gate(
        penalized_score,
        applicable_results,
    )

    return {
        "score": final_score,
        "base_score": base_score,
        "score_after_module_penalties": penalized_score,
        "applicable_requirements": applicable_requirements,
        "compliant": status_counts["compliant"],
        "partial": status_counts["partial"],
        "future_evidence_required": status_counts["future_evidence_required"],
        "non_compliant": status_counts["non_compliant"],
        "error": status_counts["error"],
        "not_applicable": status_counts["not_applicable"],
        "module_scores": module_scores,
        "module_penalties": module_penalties,
        "eligibility_override": eligibility_override,
        "hard_gate_reasons": hard_gate_reasons,
    }
    
def classify_compliance_score(score):
    """
    Classificação executiva alinhada com lógica interna do motor.
    """
    if score >= 90:
        return "Strong"
    if score >= 75:
        return "Good"
    if score >= 50:
        return "Moderate"
    return "Weak"
