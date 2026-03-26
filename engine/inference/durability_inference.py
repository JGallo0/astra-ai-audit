# engine/inference/durability_inference.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import (
    BaseInferenceRule,
    append_inference_field,
    count_project_keyword_hits,
    get_best_value,
    has_strong_evidence,
    normalize_text,
    safe_float,
)


class DurabilityInference(BaseInferenceRule):
    rule_set_name = "durability_inference"

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        durability_option = get_best_value(updated_fields, "methodology.durability_option")
        durability_years = get_best_value(updated_fields, "eligibility.durability_years")
        storage_pathway = get_best_value(updated_fields, "methodology.storage_pathway")
        stable_storage = get_best_value(updated_fields, "storage.storage_environment_stable")
        product_use = get_best_value(updated_fields, "product.end_use")
        permanence_claim = get_best_value(updated_fields, "eligibility.permanence_claim")

        project_text = normalize_text(project_context)
        methodology_text = normalize_text(methodology_context)

        durability_signals = [
            "200 years",
            ">200 years",
            "at least 200 years",
            "minimum 200 years",
            "durable carbon storage",
            "permanent carbon storage",
            "long-term storage",
            "permanence",
            "recalcitrant carbon",
            "stable carbon",
            "h/corg",
            "h/c",
        ]

        hit_count = count_project_keyword_hits(project_text, durability_signals)

        strong_storage_signal = (
            normalize_text(storage_pathway) in {"soil", "soil application", "soil storage", "agricultural soil"}
            or normalize_text(product_use) in {"soil application", "soil amendment", "soil use"}
        )

        stable_storage_signal = str(stable_storage).lower() == "true"

        permanence_signal = bool(permanence_claim) or ("permanence" in project_text)

        should_infer_200 = (
            hit_count >= 2
            and (strong_storage_signal or stable_storage_signal or permanence_signal)
        )

        if not has_strong_evidence(updated_fields, "methodology.durability_option"):
            if should_infer_200:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="methodology.durability_option",
                    value="200",
                    evidence=(
                        "Inferred from durability/permanence wording combined with stable biochar storage pathway signals."
                    ),
                    source="project",
                    confidence=0.88,
                    evidence_strength="moderate",
                    extractor="durability_inference",
                    inference_rule_id="INF-DUR-001",
                    inputs_used=[
                        "methodology.storage_pathway",
                        "storage.storage_environment_stable",
                        "product.end_use",
                        "eligibility.permanence_claim",
                        "project_context: durability/permanence wording",
                    ],
                )

        if not has_strong_evidence(updated_fields, "eligibility.durability_years"):
            inferred_option = get_best_value(updated_fields, "methodology.durability_option")
            if normalize_text(inferred_option) == "200" or should_infer_200:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="eligibility.durability_years",
                    value=200,
                    evidence=(
                        "Inferred from the selected durability framing and project permanence language consistent with 200-year storage."
                    ),
                    source="project",
                    confidence=0.86,
                    evidence_strength="moderate",
                    extractor="durability_inference",
                    inference_rule_id="INF-DUR-002",
                    inputs_used=[
                        "methodology.durability_option",
                        "project_context: permanence wording",
                        "storage.storage_environment_stable",
                    ],
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
