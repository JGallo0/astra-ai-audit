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

    BOUNDARY_KEYWORDS = [
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

    STORAGE_EMISSIONS_KEYWORDS = [
        "storage emissions",
        "post-production emissions",
        "soil emissions",
        "application emissions",
        "transport to field",
        "biochar transport",
        "handling emissions",
    ]

    def _get_signal_bundle(
        self,
        normalized_fields: List[Dict[str, Any]],
        project_context: str,
    ) -> Dict[str, Any]:
        project_boundary_defined = get_best_value(
            normalized_fields,
            "project.project_boundary_defined",
        )

        feedstock_defined = get_best_value(
            normalized_fields,
            "feedstock.feedstock_type",
        )

        production_defined = get_best_value(
            normalized_fields,
            "production.pyrolysis_technology",
        )

        storage_defined = get_best_value(
            normalized_fields,
            "methodology.storage_pathway",
        )

        emissions_defined = get_best_value(
            normalized_fields,
            "emissions.emissions_sources_identified",
        )

        lca_defined = get_best_value(
            normalized_fields,
            "quantification.lca_performed",
        )

        text = normalize_text(project_context)

        boundary_keyword_signal = project_contains_any(text, self.BOUNDARY_KEYWORDS)

        structural_signal = (
            bool(feedstock_defined)
            and bool(production_defined)
            and bool(storage_defined)
            and (bool(emissions_defined) or bool(lca_defined))
        )

        boundary_signal = (
            boundary_keyword_signal
            or bool(project_boundary_defined)
            or structural_signal
        )

        storage_keyword_signal = project_contains_any(
            text,
            self.STORAGE_EMISSIONS_KEYWORDS,
        )

        operational_storage_signal = (
            bool(storage_defined)
            and (
                "transport" in text
                or "application" in text
                or "soil" in text
                or "handling" in text
            )
        )

        storage_signal = storage_keyword_signal or operational_storage_signal

        return {
            "project_boundary_defined": project_boundary_defined,
            "feedstock_defined": feedstock_defined,
            "production_defined": production_defined,
            "storage_defined": storage_defined,
            "emissions_defined": emissions_defined,
            "lca_defined": lca_defined,
            "project_text": text,
            "boundary_keyword_signal": boundary_keyword_signal,
            "structural_signal": structural_signal,
            "boundary_signal": boundary_signal,
            "storage_keyword_signal": storage_keyword_signal,
            "operational_storage_signal": operational_storage_signal,
            "storage_signal": storage_signal,
        }

    def _should_infer_system_boundary(self, signals: Dict[str, Any]) -> bool:
        return signals["boundary_signal"]

    def _should_infer_storage_emissions(self, signals: Dict[str, Any]) -> bool:
        return signals["storage_signal"]

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

        # -----------------------------------------------------
        # INF-QUANT-001
        # Infer system boundary defined
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "ghg_accounting.system_boundary_defined"):
            if self._should_infer_system_boundary(signals):
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="ghg_accounting.system_boundary_defined",
                    value=True,
                    evidence=(
                        "Inferred from the presence of boundary definition language and/or a complete lifecycle structure (feedstock → production → storage → emissions/LCA)."
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
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-002
        # Infer storage emissions accounted
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "quantification.storage_emissions_accounted"):
            if self._should_infer_storage_emissions(signals):
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="quantification.storage_emissions_accounted",
                    value=True,
                    evidence=(
                        "Inferred from quantification language and/or operational signals covering post-production stages such as transport, application, or soil storage."
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
                    resolution_action="fill",
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
