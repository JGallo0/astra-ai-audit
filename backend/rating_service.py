"""
CO2mply — Project Readiness Score

Methodology-aware: detecta automaticamente R-XXXX (Isometric) vs P-XXXX (Puro)
e usa o mapa de dimensões correto.

Rating scale: A+ / A / B+ / B / C
"""

from typing import Any, Dict, List

# ── Requirement → Dimension mapping ───────────────────────────────────────────

DIMENSION_MAP = {
    # ── CARBON — accuracy of carbon accounting ────────────────────────────────
    "carbon": {
        "label": "Carbon Accounting",
        "requirements": {
            "R-PGFH-0",   # Baseline scenario
            "R-HF2G-0",   # Leakage assessment
            "R-VHWJ-0",   # Temporal/geographic boundary
            "R-2VKW-0",   # GHG system boundary
            "R-TGBM-0",   # GHG statement approach
            "R-2AVD-0",   # Sensitivity analysis
            "R-K6MA-0",   # Uncertainty treatment
            "R-Z106-0",   # Uncertainty analysis
            "R-NZQ2-0",   # Models/proxies
            "R-XT6V-0",   # Net CDR estimate
            "R-V143-0",   # Reversal risk / buffer
        },
        "weight": 0.25,
    },

    # ── ADDITIONALITY ─────────────────────────────────────────────────────────
    "additionality": {
        "label": "Additionality",
        "requirements": {
            "R-NK7R-0",   # Protocol eligibility
            "R-53Y5-0",   # Financial additionality
            "R-RRST-0",   # Common practice
            "R-CDNF-0",   # Environmental additionality
            "R-983D-0",   # Regulatory additionality
            "R-KQCS-0",   # Regulatory compliance
        },
        "weight": 0.25,
    },

    # ── PERMANENCE ────────────────────────────────────────────────────────────
    "permanence": {
        "label": "Permanência",
        "requirements": {
            "R-7C8E-0",   # Durability threshold selected
            "R-1T2Y-0",   # Durability demonstrated (N/A in dev)
            "R-F5RZ-0",   # Soil temperature (N/A in dev)
            "R-GYA1-0",   # Data retention (5 years)
        },
        "weight": 0.20,
    },

    # ── SAFEGUARDS ────────────────────────────────────────────────────────────
    "safeguards": {
        "label": "Salvaguardas",
        "requirements": {
            "R-9MJQ-0",   # Environmental regulatory compliance
            "R-X9EC-0",   # E&S impact assessment
            "R-4K5P-0",   # No net environmental harm
            "R-R81B-0",   # No net social harm
            "R-BWX0-0",   # SDGs alignment
            "R-6VFZ-0",   # Project closure plan
            "R-BC4H-0",   # Adaptive management
            "R-MY64-0",   # Pollution prevention (PAHs, metals)
            "R-ZHRN-0",   # Stakeholder consultation
            "R-E579-0",   # Grievance mechanism
            "R-5KQC-0",   # Productivity monitoring (N/A in dev)
            "R-M760-0",   # Soil samples (N/A in dev)
            "R-1YC3-0",   # Co-benefits (N/A in dev)
        },
        "weight": 0.15,
    },

    # ── PROJECT INTEGRITY — PDD completeness ──────────────────────────────────
    "integrity": {
        "label": "Integridade do PDD",
        "requirements": {
            "R-M858-0",   # Ownership
            "R-7X0X-0",   # Technical description
            "R-F6R7-0",   # Project participants
            "R-A5B6-0",   # Locations / geo-coordinates
            "R-ENZR-0",   # Monitoring parameter table
            "R-6AQG-0",   # Reactor design diagram
            "R-SZK5-0",   # Gas leakage sensors
            "R-DMET-0",   # Material selection
            "R-19AF-0",   # Maintenance plan
            "R-S8K1-1",   # Sampling procedure (N/A in dev)
            "R-CXEP-0",   # Characterization standards (N/A in dev)
            "R-VGXA-0",   # Chemical properties (N/A in dev)
            "R-2TMM-0",   # Laboratory (N/A in dev)
        },
        "weight": 0.15,
    },
}

# ── Letter grade ───────────────────────────────────────────────────────────────

GRADE_SCALE = [
    (90, "A+", "Pronto para Submissão",
     "O projeto demonstra alta conformidade com o protocolo. "
     "Os gaps identificados são menores e não bloqueiam a submissão."),
    (80, "A",  "Sólido",
     "Boa aderência ao protocolo com gaps documentais pontuais. "
     "Recomendamos resolver os itens parciais antes da submissão."),
    (70, "B+", "Em Desenvolvimento",
     "Estrutura adequada mas com seções importantes incompletas. "
     "Ação prioritária necessária nas dimensões abaixo de 70%."),
    (60, "B",  "Desenvolvimento Inicial",
     "O projeto possui fundamentos mas requer revisão substantiva "
     "antes de estar pronto para submissão."),
    (0,  "C",  "Fase Inicial",
     "O PDD necessita de desenvolvimento significativo. "
     "Recomendamos uma revisão fundamental antes de prosseguir."),
]

def _letter_grade(score: float) -> Dict[str, str]:
    for threshold, grade, label, description in GRADE_SCALE:
        if score >= threshold:
            return {"grade": grade, "label": label, "description": description}
    return {"grade": "C", "label": "Fase Inicial", "description": GRADE_SCALE[-1][3]}

# ── Dimensional score calculation ──────────────────────────────────────────────

def _dimension_score(dim_reqs: set, results_by_id: Dict[str, dict]) -> Dict[str, Any]:
    """Compute score for a dimension from applicable (non-N/A) requirements."""
    scores = []
    applicable = []
    not_applicable = []

    for req_id in dim_reqs:
        r = results_by_id.get(req_id)
        if not r:
            continue
        status = r.get("status", "")
        if status == "not_applicable":
            not_applicable.append(req_id)
            continue
        score = r.get("requirement_score")
        if score is not None:
            try:
                scores.append(float(score))
                applicable.append(req_id)
            except (TypeError, ValueError):
                pass

    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    return {
        "score": avg,
        "applicable_count": len(applicable),
        "na_count": len(not_applicable),
    }

# ── Main entry point ──────────────────────────────────────────────────────────

def _detect_methodology(results: List[dict]) -> str:
    """Detecta a metodologia pelos IDs dos requisitos."""
    for r in results:
        rid = r.get("requirement_id", "")
        if rid.startswith("P-"):
            return "puro_earth"
    return "isometric"


def compute_readiness_rating(
    results: List[dict],
    overall_score: float,
    audit_mode: str = "development",
) -> Dict[str, Any]:
    """
    Compute the Project Readiness Score from audit results.
    Detecta automaticamente a metodologia pelos IDs dos requisitos
    e usa o mapa de dimensões correto (Isometric ou universal Puro).
    """
    methodology = _detect_methodology(results)

    # ── Puro.Earth: usa dimensões universais do dimension_map.py ──────────────
    if methodology == "puro_earth":
        try:
            from engine.dimension_map import (
                compute_dimension_scores, compute_weighted_score,
                UNIVERSAL_DIMENSIONS,
            )
            dim_scores = compute_dimension_scores(results, "puro_earth")
            # Reconstrói no formato esperado pelo frontend
            dimensions = {}
            for dim_key, cfg in UNIVERSAL_DIMENSIONS.items():
                score = dim_scores.get(dim_key)
                # Conta N/A para esta dimensão
                from engine.dimension_map import PURO_DIMENSION_MAP
                dim_req_ids = {k for k, v in PURO_DIMENSION_MAP.items() if v == dim_key}
                results_by_id = {r.get("requirement_id", ""): r for r in results}
                na_count = sum(
                    1 for rid in dim_req_ids
                    if results_by_id.get(rid, {}).get("status") == "not_applicable"
                )
                dimensions[dim_key] = {
                    "label":            cfg["label"],
                    "score":            score,
                    "weight":           cfg["weight"],
                    "applicable_count": len([r for r in results
                                            if PURO_DIMENSION_MAP.get(r.get("requirement_id","")) == dim_key
                                            and r.get("status") != "not_applicable"]),
                    "na_count":         na_count,
                }
            # Recalcula overall com pesos universais
            weighted = compute_weighted_score(dim_scores)
            if weighted > 0:
                overall_score = weighted
        except Exception as e:
            print(f"[rating] Puro dimension_map error: {e}")
            dimensions = {k: {"label": k, "score": None, "weight": 0, "applicable_count": 0, "na_count": 0}
                         for k in ["feedstock_eligibility", "carbon_accounting", "additionality",
                                   "permanence", "monitoring", "environmental_social"]}

    # ── Isometric: usa o mapa original hardcoded ───────────────────────────────
    else:
        results_by_id: Dict[str, dict] = {
            r.get("requirement_id", ""): r
            for r in results
            if r.get("requirement_id")
        }
        dimensions = {}
        for dim_key, dim_cfg in DIMENSION_MAP.items():
            dim_result = _dimension_score(dim_cfg["requirements"], results_by_id)
            dimensions[dim_key] = {
                "label":            dim_cfg["label"],
                "score":            dim_result["score"],
                "weight":           dim_cfg["weight"],
                "applicable_count": dim_result["applicable_count"],
                "na_count":         dim_result["na_count"],
            }

    grade_info = _letter_grade(overall_score)

    return {
        "grade":         grade_info["grade"],
        "label":         grade_info["label"],
        "description":   grade_info["description"],
        "overall_score": round(overall_score, 1),
        "dimensions":    dimensions,
        "audit_mode":    audit_mode,
        "phase":         "PDD Audit",
        "methodology":   methodology,
        "version":       "1.0",
    }
