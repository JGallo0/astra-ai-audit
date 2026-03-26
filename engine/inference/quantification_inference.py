# engine/inference/quantification_inference.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import (
    BaseInferenceRule,
    append_inference_field,
    get_best_value,
    has_strong_evidence,
    normalize_text,
    project_contains_any,
)


class QuantificationInference(BaseInferenceRule):
    rule_set_name = "quantification_inference"

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        project_boundary_defined = get_best_value(updated_fields, "project.project_boundary_defined")
        feedstock_defined = get_best_value(updated_fields, "feedstock.feedstock_type")
        production_defined = get_best_value(updated_fields, "production.pyrolysis_technology")
        storage_defined = get_best_value(updated_fields, "methodology.storage_pathway")
        emissions_defined = get_best_value(updated_fields, "emissions.emissions_sources_identified")
        lca_defined = get_best_value(updated_fields, "quantification.lca_performed")

        text = normalize_text(project_context)

        boundary_keywords = [
            "system boundary",
            "project boundary",
            "within the boundary",
            "included emissions",
            "excluded emissions",
            "upstream emissions",
            "downstream emissions",
            "scope of accounting",
            "life cycle stages",
            "boundary includes",
        ]

        storage_emissions_keywords = [
            "storage emissions",
            "post-production emissions",
            "soil emissions",
            "application emissions",
            "transport to field",
            "biochar transport",
            "handling emissions",
        ]

        boundary_signal = (
            project_contains_any(text, boundary_keywords)
            or bool(project_boundary_defined)
            or (
                bool(feedstock_defined)
                and bool(production_defined)
                and bool(storage_defined)
                and (bool(emissions_defined) or bool(lca_defined))
            )
        )

        if not has_strong_evidence(updated_fields, "ghg_accounting.system_boundary_defined"):
            if boundary_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="ghg_accounting.system_boundary_defined",
                    value=True,
                    evidence=(
                        "Inferred from the presence of structured lifecycle/accounting elements that together define a functional GHG system boundary."
                    ),
                    source="project",
                    confidence=0.83,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-001",
                    inputs_used=[
                        "project.project_boundary_defined",
                        "feedstock.feedstock_type",
                        "production.pyrolysis_technology",
                        "methodology.storage_pathway",
                        "emissions.emissions_sources_identified",
                        "quantification.lca_performed",
                        "project_context: boundary wording",
                    ],
                )

        storage_signal = (
            project_contains_any(text, storage_emissions_keywords)
            or (
                bool(storage_defined)
                and (
                    "transport" in text
                    or "application" in text
                    or "soil" in text
                    or "handling" in text
                )
            )
        )

        if not has_strong_evidence(updated_fields, "quantification.storage_emissions_accounted"):
            if storage_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="quantification.storage_emissions_accounted",
                    value=True,
                    evidence=(
                        "Inferred from quantification language covering post-production/storage-stage emissions or operational elements directly associated with storage/application."
                    ),
                    source="project",
                    confidence=0.78,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-002",
                    inputs_used=[
                        "methodology.storage_pathway",
                        "project_context: storage/application emissions wording",
                    ],
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
