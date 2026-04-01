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
        "biochar storage",
        "biochar application",
    ]

    REGULATORY_MEASUREMENT_KEYWORDS = [
        "title v",
        "boiler mact",
        "epa",
        "ceqa",
        "regularly tested",
        "emissions testing",
        "periodic stack emissions testing",
        "calibration",
        "calibrated",
        "isometric-approved lab",
    ]

    MONITORING_KEYWORDS = [
        "sampling for required mrv",
        "updated sampling regime",
        "increased sampling frequency",
        "ghg data would be monthly",
        "regularly tested",
        "monitor quality and carbon content",
        "per reporting period",
        "monitoring data",
    ]

    CONTAMINANT_KEYWORDS = [
        "pahs",
        "heavy metals",
        "ash content",
        "volatile matter",
        "fixed carbon",
        "laboratory analysis",
        "isometric-approved lab",
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

        project_text = signals.get("project_text", "") or ""

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
                        "feedstock.biomass_type",
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

        # -----------------------------------------------------
        # INF-QUANT-003
        # Infer LCA performed
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "quantification.lca_performed"):
            has_boundary = bool(get_best_value(updated_fields, "ghg_accounting.system_boundary_defined"))
            has_baseline = bool(get_best_value(updated_fields, "ghg_accounting.baseline_defined"))
            has_storage_accounting = bool(get_best_value(updated_fields, "quantification.storage_emissions_accounted"))

            lca_keywords = [
                "ghg statement",
                "life cycle",
                "lifecycle",
                "carbon source and sink",
                "emissions portfolio",
            ]

            has_lca_keyword = project_contains_any(project_text, lca_keywords)

            if (has_boundary and has_baseline and has_storage_accounting) or has_lca_keyword:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="quantification.lca_performed",
                    value=True,
                    evidence=(
                        "Inferred from system boundary, baseline, storage accounting, and/or explicit GHG statement / lifecycle wording."
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
                        "project_context: GHG statement / lifecycle wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-004
        # Infer net-negative claim
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
                        "Inferred from the presence of a complete net-removals accounting structure including system boundary, baseline, storage emissions accounting, and LCA-performed evidence."
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

        # -----------------------------------------------------
        # INF-QUANT-005
        # Infer legal.regulatory_measurement_methods
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "legal.regulatory_measurement_methods"):
            measurement_signal = (
                project_contains_any(project_text, self.REGULATORY_MEASUREMENT_KEYWORDS)
                or bool(get_best_value(updated_fields, "emissions.stack_monitoring_method"))
                or bool(get_best_value(updated_fields, "emissions.testing_frequency"))
                or bool(get_best_value(updated_fields, "legal.applicable_environmental_requirements"))
            )

            if measurement_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="legal.regulatory_measurement_methods",
                    value=True,
                    evidence=(
                        "Inferred from explicit regulatory measurement/testing references such as Title V, Boiler MACT, EPA-linked requirements, and regular emissions testing."
                    ),
                    source="project",
                    confidence=0.86,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-005",
                    inputs_used=[
                        "emissions.stack_monitoring_method",
                        "emissions.testing_frequency",
                        "legal.applicable_environmental_requirements",
                        "project_context: regulatory/testing wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-006
        # Infer monitoring_reporting.monitoring_plan
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "monitoring_reporting.monitoring_plan"):
            monitoring_signal = (
                project_contains_any(project_text, self.MONITORING_KEYWORDS)
                or bool(get_best_value(updated_fields, "sampling.sampling_plan_defined"))
                or bool(get_best_value(updated_fields, "biochar.characterization.lab_reports"))
            )

            if monitoring_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="monitoring_reporting.monitoring_plan",
                    value=True,
                    evidence=(
                        "Inferred from explicit sampling/MRV/testing cadence and recurring monitoring language in the project documentation."
                    ),
                    source="project",
                    confidence=0.80,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-006",
                    inputs_used=[
                        "sampling.sampling_plan_defined",
                        "biochar.characterization.lab_reports",
                        "project_context: MRV/sampling/testing wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-007
        # Infer biochar.characterization.ongoing_monitoring_plan
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "biochar.characterization.ongoing_monitoring_plan"):
            ongoing_signal = (
                "updated sampling regime" in project_text
                or "increased sampling frequency" in project_text
                or "monitor quality and carbon content" in project_text
                or "composite samples" in project_text
                or "per reporting period" in project_text
                or "separate proximate analysis" in project_text
            )

            if ongoing_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="biochar.characterization.ongoing_monitoring_plan",
                    value=True,
                    evidence=(
                        "Inferred from updated sampling regime, increased sampling frequency, composite sample collection, and recurring proximate analysis language."
                    ),
                    source="project",
                    confidence=0.84,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-007",
                    inputs_used=[
                        "project_context: sampling regime / frequency / proximate analysis wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-008
        # Infer biochar.characterization.contaminant_testing
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "biochar.characterization.contaminant_testing"):
            contaminant_signal = project_contains_any(project_text, self.CONTAMINANT_KEYWORDS)

            if contaminant_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="biochar.characterization.contaminant_testing",
                    value=True,
                    evidence=(
                        "Inferred from explicit contaminant / laboratory parameter references such as PAHs, heavy metals, ash, volatile matter, fixed carbon, and approved lab testing."
                    ),
                    source="project",
                    confidence=0.83,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-008",
                    inputs_used=[
                        "project_context: PAHs / heavy metals / approved-lab wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-009
        # Infer biochar.characterization.contaminant_testing_frequency
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "biochar.characterization.contaminant_testing_frequency"):
            if (
                "increased sampling frequency" in project_text
                or "per reporting period" in project_text
                or "updated sampling regime" in project_text
                or bool(get_best_value(updated_fields, "emissions.testing_frequency"))
            ):
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="biochar.characterization.contaminant_testing_frequency",
                    value="per_reporting_period",
                    evidence=(
                        "Inferred from recurring sampling/testing cadence in the project documentation."
                    ),
                    source="project",
                    confidence=0.78,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-009",
                    inputs_used=[
                        "emissions.testing_frequency",
                        "project_context: recurring sampling/testing wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-010
        # Infer sampling.method as partial protocol evidence
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "sampling.method"):
            if (
                "composite samples" in project_text
                or "updated sampling regime" in project_text
                or "separate proximate analysis" in project_text
            ):
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="sampling.method",
                    value="project_defined_sampling_regime",
                    evidence=(
                        "Inferred from explicit sampling regime / composite sampling / proximate analysis language, though not mapped to Isometric Method A/B verbatim."
                    ),
                    source="project",
                    confidence=0.72,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-010",
                    inputs_used=[
                        "project_context: composite samples / updated sampling regime / proximate analysis wording",
                    ],
                    resolution_action="fill",
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }

        # -----------------------------------------------------
        # INF-QUANT-011
        # Infer biochar.characterization.ongoing_monitoring_plan
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "biochar.characterization.ongoing_monitoring_plan"):
            monitoring_signal = (
                "updated sampling regime" in project_text
                or "increased sampling frequency" in project_text
                or "separate proximate analysis" in project_text
                or "composite samples" in project_text
                or "monitor quality and carbon content" in project_text
                or "per reporting period" in project_text
            )

            if monitoring_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="biochar.characterization.ongoing_monitoring_plan",
                    value=True,
                    evidence=(
                        "Inferred from updated sampling regime, increased sampling frequency, composite sampling, and recurring proximate analysis language."
                    ),
                    source="project",
                    confidence=0.84,
                    evidence_strength="moderate",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-011",
                    inputs_used=[
                        "project_context: updated sampling regime / frequency / proximate analysis wording",
                    ],
                    resolution_action="fill",
                )

        # -----------------------------------------------------
        # INF-QUANT-012
        # Infer monitoring_reporting.data_sharing_plan (weak/partial signal only)
        # -----------------------------------------------------
        if not has_strong_evidence(updated_fields, "monitoring_reporting.data_sharing_plan"):
            record_signal = (
                "chain-of-custody" in project_text
                or "coc tracing" in project_text
                or "signed affidavit" in project_text
                or "appendix" in project_text
                or "byproduct log" in project_text
                or "supporting documents" in project_text
                or "project locations section" in project_text
            )

            if record_signal:
                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="monitoring_reporting.data_sharing_plan",
                    value=True,
                    evidence=(
                        "Inferred from documentary traceability and supporting-record language, treated as partial governance evidence rather than a formal data-sharing plan."
                    ),
                    source="project",
                    confidence=0.68,
                    evidence_strength="weak",
                    extractor="quantification_inference",
                    inference_rule_id="INF-QUANT-012",
                    inputs_used=[
                        "project_context: CoC / appendix / supporting-record wording",
                    ],
                    resolution_action="fill",
                )
