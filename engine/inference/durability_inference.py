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
    safe_bool,
)


class DurabilityInference(BaseInferenceRule):
    rule_set_name = "durability_inference"

    DURABILITY_SIGNAL_KEYWORDS = [
        "200 years",
        ">200 years",
        "at least 200 years",
        "minimum 200 years",
        "minimum durability of 200 years",
        "durable carbon storage",
        "permanent carbon storage",
        "long-term storage",
        "long term storage",
        "permanence",
        "recalcitrant carbon",
        "stable carbon",
        "stable form of carbon",
        "h/corg",
        "h/c",
    ]

    SOIL_STORAGE_TERMS = {
        "soil",
        "soil application",
        "soil storage",
        "agricultural soil",
        "soil amendment",
        "soil use",
    }

    def _get_signal_bundle(
        self,
        normalized_fields: List[Dict[str, Any]],
        project_context: str,
    ) -> Dict[str, Any]:
        storage_pathway = get_best_value(normalized_fields, "methodology.storage_pathway")
        stable_storage = get_best_value(normalized_fields, "storage.storage_environment_stable")
        product_use = get_best_value(normalized_fields, "product.end_use")
        permanence_claim = get_best_value(normalized_fields, "eligibility.permanence_claim")

        project_text = normalize_text(project_context)

        keyword_hits = count_project_keyword_hits(
            project_text,
            self.DURABILITY_SIGNAL_KEYWORDS,
        )

        storage_pathway_norm = normalize_text(storage_pathway)
        product_use_norm = normalize_text(product_use)
        stable_storage_bool = safe_bool(stable_storage)
        permanence_claim_bool = safe_bool(permanence_claim)

        strong_storage_signal = (
            storage_pathway_norm in self.SOIL_STORAGE_TERMS
            or product_use_norm in self.SOIL_STORAGE_TERMS
        )

        stable_storage_signal = stable_storage_bool is True

        permanence_signal = (
            permanence_claim_bool is True
            or "permanence" in project_text
            or "permanent carbon storage" in project_text
        )

        is_biochar_project = "biochar" in project_text

        return {
            "storage_pathway": storage_pathway,
            "stable_storage": stable_storage,
            "product_use": product_use,
            "permanence_claim": permanence_claim,
            "project_text": project_text,
            "keyword_hits": keyword_hits,
            "strong_storage_signal": strong_storage_signal,
            "stable_storage_signal": stable_storage_signal,
            "permanence_signal": permanence_signal,
            "is_biochar_project": is_biochar_project,
        }

    def _should_infer_200_year_durability(self, signals: Dict[str, Any]) -> bool:
        # Caso 1 — evidência explícita (mesmo que fraca)
        if signals["keyword_hits"] >= 1:
            return True

        # Caso 2 — inferência estrutural (biochar + soil)
        if signals["strong_storage_signal"]:
            return True

        # Caso 3 — permanência declarada
        if signals["permanence_signal"]:
            return True

        return False

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        signals = self._get_signal_bundle(
            normalized_fields=updated_fields,
            project_context=project_context,
        )

        should_infer_200 = self._should_infer_200_year_durability(signals)

        # -----------------------------------------------------
        # INF-DUR-001
        # Infer methodology.durability_option = "200"
        # -----------------------------------------------------
        
        if not has_strong_evidence(updated_fields, "methodology.durability_option"):
            if should_infer_200:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="methodology.durability_option",
                    value="200",
                    evidence=(
                        "Inferred from durability/permanence wording combined with stable storage pathway signals consistent with a 200-year durability framing."
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
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-DUR-002
        # Infer eligibility.durability_years = 200
        # -----------------------------------------------------
        
        if not has_strong_evidence(updated_fields, "eligibility.durability_years"):
            inferred_option = get_best_value(updated_fields, "methodology.durability_option")

            if normalize_text(inferred_option) == "200" or should_infer_200:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="eligibility.durability_years",
                    value=200,
                    evidence=(
                        "Inferred from the selected durability framing and project permanence language consistent with a minimum 200-year durability requirement."
                    ),
                    source="project",
                    confidence=0.86,
                    evidence_strength="moderate",
                    extractor="durability_inference",
                    inference_rule_id="INF-DUR-002",
                    inputs_used=[
                        "methodology.durability_option",
                        "storage.storage_environment_stable",
                        "eligibility.permanence_claim",
                        "project_context: permanence wording",
                    ],
                    resolution_action="fill",
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
        
        # -----------------------------------------------------
        # INF-DUR-003
        # Infer storage.storage_environment_stable = True (strong rule)
        # -----------------------------------------------------
        
        if not has_strong_evidence(updated_fields, "storage.storage_environment_stable"):

            storage_pathway = normalize_text(get_best_value(updated_fields, "methodology.storage_pathway"))
            durability_years = get_best_value(updated_fields, "eligibility.durability_years")
            storage_module = normalize_text(get_best_value(updated_fields, "storage.storage_module"))

            strong_structural_signal = (
                storage_pathway == "soil"
                and (
                    durability_years == 200
                    or normalize_text(storage_module) == "biochar storage in soil environments"
                )
            )

            if strong_structural_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="storage.storage_environment_stable",
                    value=True,
                    evidence=(
                        "Inferred from soil storage pathway combined with 200-year durability requirement, "
                        "consistent with stable biochar carbon storage in soil environments under Isometric."
                    ),
                    source="project",
                    confidence=0.93,
                    evidence_strength="strong",
                    extractor="durability_inference",
                    inference_rule_id="INF-DUR-003",
                    inputs_used=[
                        "methodology.storage_pathway",
                        "eligibility.durability_years",
                        "storage.storage_module",
                    ],
                    resolution_action="fill",
                )
