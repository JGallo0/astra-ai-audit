# engine/inference/product_inference.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .base import (
    BaseInferenceRule,
    append_inference_field,
    get_best_field,
    get_best_value,
    has_strong_evidence,
    normalize_text,
)


class ProductInference(BaseInferenceRule):
    rule_set_name = "product_inference"

    FEEDSTOCK_CERT_SCHEMES: Set[str] = {
        "fsc",
        "sbp",
        "pefc",
        "sfi",
    }

    def _extract_cert_tokens(self, raw_value: Any) -> Set[str]:
        raw_text = normalize_text(raw_value)

        return {
            token.strip().lower()
            for token in raw_text.replace(";", ",").split(",")
            if token.strip()
        }

    def _is_feedstock_certification_misclassified(
        self,
        product_cert_field: Optional[Dict[str, Any]],
    ) -> bool:
        if not product_cert_field:
            return False

        raw_value = product_cert_field.get("value")
        tokens = self._extract_cert_tokens(raw_value)

        if not tokens:
            return False

        return tokens.issubset(self.FEEDSTOCK_CERT_SCHEMES)

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        product_cert_field = get_best_field(
            updated_fields,
            "product.certification_scheme",
        )

        feedstock_cert_value = get_best_value(
            updated_fields,
            "feedstock.certification_scheme",
        )

        if self._is_feedstock_certification_misclassified(product_cert_field):
            raw_value = product_cert_field.get("value")

            if not has_strong_evidence(updated_fields, "feedstock.certification_scheme"):
                if not feedstock_cert_value:
                    updated_fields = append_inference_field(
                        updated_fields,
                        inference_events,
                        path="feedstock.certification_scheme",
                        value=raw_value,
                        evidence=(
                            "Reclassified from product certification to feedstock certification because the detected schemes are associated with biomass sourcing rather than product-level biochar certification."
                        ),
                        source="project",
                        confidence=0.91,
                        evidence_strength="strong",
                        extractor="product_inference",
                        inference_rule_id="INF-PRODCT-001",
                        inputs_used=[
                            "product.certification_scheme",
                        ],
                        resolution_action="reclassify",
                        reclassify_from="product.certification_scheme",
                    )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
