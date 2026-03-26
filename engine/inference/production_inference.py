# engine/inference/production_inference.py

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


class ProductionInference(BaseInferenceRule):
    rule_set_name = "production_inference"

    TECHNOLOGY_TERMS = [
        "pyrolysis",
        "thermochemical conversion",
        "carbonization",
        "carbonisation",
        "retort",
        "kiln",
        "furnace",
        "retrofit",
        "retrofitted",
        "cogeneration-based biochar production",
        "integrated biomass power infrastructure",
        "thermochemical process",
        "syngas combustion",
        "thermal decomposition",
        "oxygen-limited",
        "oxygen limited",
        "limited oxygen",
    ]

    BIOCHAR_TERMS = [
        "biochar",
        "char",
        "carbon-rich solid",
        "carbon rich solid",
    ]

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        pyrolysis_technology = get_best_value(updated_fields, "production.pyrolysis_technology")
        thermal_process = get_best_value(updated_fields, "production.thermal_process_type")
        syngas_handling = get_best_value(updated_fields, "emissions.syngas_handling")
        reactor_or_system_desc = get_best_value(updated_fields, "production.system_description")

        text = normalize_text(project_context)

        has_technology_signal = project_contains_any(text, self.TECHNOLOGY_TERMS)
        has_biochar_signal = project_contains_any(text, self.BIOCHAR_TERMS)

        syngas_signal = normalize_text(syngas_handling) in {
            "combusted",
            "flared",
            "burned",
            "burned in furnace",
            "oxidized",
        }

        thermal_signal = bool(thermal_process) or bool(reactor_or_system_desc)

        if not has_strong_evidence(updated_fields, "production.pyrolysis_technology"):
            if (has_technology_signal and has_biochar_signal) or (syngas_signal and has_biochar_signal) or (thermal_signal and has_biochar_signal):
                inferred_value = "pyrolysis-based biochar production system"

                if "retort" in text:
                    inferred_value = "retort-based biochar production system"
                elif "kiln" in text:
                    inferred_value = "kiln-based biochar production system"
                elif "furnace" in text:
                    inferred_value = "furnace-based biochar production system"
                elif "retrofit" in text or "retrofitted" in text:
                    inferred_value = "retrofitted biochar production system"

                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="production.pyrolysis_technology",
                    value=inferred_value,
                    evidence=(
                        "Inferred from technology/process wording indicating biochar production through thermochemical conversion, without relying on the exact term 'reactor'."
                    ),
                    source="project",
                    confidence=0.84,
                    evidence_strength="moderate",
                    extractor="production_inference",
                    inference_rule_id="INF-PROD-001",
                    inputs_used=[
                        "project_context: process wording",
                        "production.thermal_process_type",
                        "production.system_description",
                        "emissions.syngas_handling",
                    ],
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
