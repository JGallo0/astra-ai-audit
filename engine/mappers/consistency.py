# engine/mappers/consistency.py

from typing import Any, Dict, List


def run_consistency_checks(
    project_data: Dict[str, Any],
    normalized_fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    flags: List[Dict[str, Any]] = []
    notes: List[str] = []

    sampling = project_data.get("sampling", {}) or {}
    methodology = project_data.get("methodology", {}) or {}
    storage = project_data.get("storage", {}) or {}
    eligibility = project_data.get("eligibility", {}) or {}

    batch_days = sampling.get("batch_definition_days")
    sampling_method = sampling.get("method")
    storage_pathway = methodology.get("storage_pathway")
    durability_years = eligibility.get("durability_years")
    durability_option = methodology.get("durability_option")

    if sampling_method in {"A", "B"} and batch_days is None:
        flags.append({
            "code": "sampling_method_without_batch_definition",
            "severity": "medium",
            "message": "Sampling method is present, but batch definition is missing.",
        })

    if durability_years and not durability_option:
        flags.append({
            "code": "durability_years_without_option",
            "severity": "medium",
            "message": "Durability years are present, but methodology durability option is missing.",
        })

    if storage_pathway == "soil":
        soil = storage.get("soil", {}) or {}
        deployment_methods = soil.get("deployment_methods")
        if deployment_methods in (None, [], ""):
            flags.append({
                "code": "soil_pathway_without_deployment_method",
                "severity": "medium",
                "message": "Soil storage pathway is present, but deployment methods are missing.",
            })

    if not flags:
        notes.append("No cross-field consistency issues detected in v1 checker.")
    else:
        notes.append("Cross-field consistency issues detected. Review flags.")

    return {
        "consistency_flags": flags,
        "consistency_notes": notes,
    }
