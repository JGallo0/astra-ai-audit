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
            "feedstock.biomass_type",
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

        # -----------------------------------------------------
        # INF-QUANT-003
        # Infer LCA performed (robust multi-signal)
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "quantification.lca_performed"):

            has_boundary = bool(get_best_value(updated_fields, "ghg_accounting.system_boundary_defined"))
            has_baseline = bool(get_best_value(updated_fields, "ghg_accounting.baseline_defined"))
            has_storage_accounting = bool(get_best_value(updated_fields, "quantification.storage_emissions_accounted"))

            text = signals.get("project_text", "") or ""

            lca_keywords = [
                "lca",
                "life cycle",
                "lifecycle",
                "ghg statement",
                "carbon accounting",
                "emissions accounting",
                "bcu calculation",
            ]

            has_lca_keyword = project_contains_any(text, lca_keywords)

            strong_structural_signal = (
                has_boundary
                and has_baseline
                and has_storage_accounting
            )

            if strong_structural_signal or (has_lca_keyword and has_boundary):
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="quantification.lca_performed",
                    value=True,
                    evidence=(
                        "Inferred from consistent carbon accounting structure including system boundary, baseline definition, "
                        "and storage emissions accounting, optionally supported by LCA-related terminology."
                    ),
                    source="project",
                    confidence=0.88,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-003",
                    inputs_used=[
                        "ghg_accounting.system_boundary_defined",
                        "ghg_accounting.baseline_defined",
                        "quantification.storage_emissions_accounted",
                        "project_context: carbon accounting / LCA wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-004
        # Infer net-negative claim (structural)
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "eligibility.net_negative_claim"):

            has_boundary = bool(get_best_value(updated_fields, "ghg_accounting.system_boundary_defined"))
            has_baseline = bool(get_best_value(updated_fields, "ghg_accounting.baseline_defined"))
            has_storage_accounting = bool(get_best_value(updated_fields, "quantification.storage_emissions_accounted"))
            has_lca = bool(get_best_value(updated_fields, "quantification.lca_performed"))

            if has_boundary and has_baseline and has_storage_accounting and has_lca:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="eligibility.net_negative_claim",
                    value=True,
                    evidence=(
                        "Inferred from the presence of a complete net-removals accounting structure including "
                        "system boundary, baseline, storage emissions accounting, and LCA-performed evidence."
                    ),
                    source="project",
                    confidence=0.90,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-004",
                    inputs_used=[
                        "ghg_accounting.system_boundary_defined",
                        "ghg_accounting.baseline_defined",
                        "quantification.storage_emissions_accounted",
                        "quantification.lca_performed",
                    ],
                    resolution_action="fill",
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
