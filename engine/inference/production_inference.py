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

    SYNGAS_COMBUSTION_TERMS = {
        "combusted",
        "flared",
        "burned",
        "burned in furnace",
        "oxidized",
    }

    def _get_signal_bundle(
        self,
        normalized_fields: List[Dict[str, Any]],
        project_context: str,
    ) -> Dict[str, Any]:
        pyrolysis_technology = get_best_value(
            normalized_fields,
            "production.pyrolysis_technology",
        )

        thermal_process = get_best_value(
            normalized_fields,
            "production.thermal_process_type",
        )

        syngas_handling = get_best_value(
            normalized_fields,
            "emissions.syngas_handling",
        )

        system_description = get_best_value(
            normalized_fields,
            "production.system_description",
        )

        text = normalize_text(project_context)

        has_technology_signal = project_contains_any(text, self.TECHNOLOGY_TERMS)
        has_biochar_signal = project_contains_any(text, self.BIOCHAR_TERMS)

        syngas_signal = normalize_text(syngas_handling) in self.SYNGAS_COMBUSTION_TERMS
        thermal_signal = bool(thermal_process) or bool(system_description)

        return {
            "pyrolysis_technology": pyrolysis_technology,
            "thermal_process": thermal_process,
            "syngas_handling": syngas_handling,
            "system_description": system_description,
            "project_text": text,
            "has_technology_signal": has_technology_signal,
            "has_biochar_signal": has_biochar_signal,
            "syngas_signal": syngas_signal,
            "thermal_signal": thermal_signal,
        }

    def _infer_technology_label(self, text: str) -> str:
        """
        Deriva um label mais específico com base no vocabulário do projeto.
        """

        if "retort" in text:
            return "retort-based biochar production system"

        if "kiln" in text:
            return "kiln-based biochar production system"

        if "furnace" in text:
            return "furnace-based biochar production system"

        if "retrofit" in text or "retrofitted" in text:
            return "retrofitted biochar production system"

        return "pyrolysis-based biochar production system"

    def _should_infer_pyrolysis(self, signals: Dict[str, Any]) -> bool:
        return (
            (
                signals["has_technology_signal"]
                and signals["has_biochar_signal"]
            )
            or (
                signals["syngas_signal"]
                and signals["has_biochar_signal"]
            )
            or (
                signals["thermal_signal"]
                and signals["has_biochar_signal"]
            )
        )

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

        should_infer = self._should_infer_pyrolysis(signals)

        # -----------------------------------------------------
        # INF-PROD-001
        # Infer production.pyrolysis_technology
        # -----------------------------------------------------
        current_value = get_best_value(
            updated_fields,
            "production.pyrolysis_technology",
        )

        is_weak_value = normalize_text(current_value) in {
            "",
            "biochar production",
            "production of biochar",
            "biochar system",
            "biochar technology",
            "carbon removal technology",
            "pyrolysis",
        }

        if (
            not has_strong_evidence(updated_fields, "production.pyrolysis_technology")
            or is_weak_value
        ):
            if should_infer:
                inferred_value = self._infer_technology_label(
                    signals["project_text"]
                )

                updated_fields = append_inference_field(
                    updated_fields,
                    inference_events,
                    path="production.pyrolysis_technology",
                    value=inferred_value,
                    evidence=(
                        "Inferred from thermochemical process wording, biochar production context, and system-level signals without relying on the explicit term 'reactor'."
                    ),
                    source="project",
                    confidence=0.84,
                    evidence_strength="moderate",
                    extractor="production_inference",
                    inference_rule_id="INF-PROD-001",
                    inputs_used=[
                        "project_context: thermochemical process wording",
                        "production.thermal_process_type",
                        "production.system_description",
                        "emissions.syngas_handling",
                    ],
                    resolution_action="semantic_override" if is_weak_value else "fill",
                    invalidates_paths=["production.pyrolysis_technology"] if is_weak_value else [],
                    overwrite=is_weak_value,
                )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
