# engine/inference/product_inference.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import (
    BaseInferenceRule,
    append_inference_field,
    get_best_field,
    get_best_value,
    normalize_text,
    safe_float,
)


class ProductInference(BaseInferenceRule):
    rule_set_name = "product_inference"

    FEEDSTOCK_CERT_SCHEMES = {
        "fsc",
        "sbp",
        "pefc",
        "sfi",
    }

    def run(
        self,
        normalized_fields: List[Dict[str, Any]],
        raw_extraction_bundle: Optional[Dict[str, Any]] = None,
        project_context: str = "",
        methodology_context: str = "",
    ) -> Dict[str, Any]:
        updated_fields = list(normalized_fields or [])
        inference_events: List[Dict[str, Any]] = []

        product_cert = get_best_field(updated_fields, "product.certification_scheme")
        feedstock_cert = get_best_value(updated_fields, "feedstock.certification_scheme")

        if product_cert:
            raw_value = product_cert.get("value")
            raw_text = normalize_text(raw_value)

            tokens = {
                x.strip().lower()
                for x in raw_text.replace(";", ",").split(",")
                if x.strip()
            }

            if tokens and tokens.issubset(self.FEEDSTOCK_CERT_SCHEMES):
                product_conf = safe_float(product_cert.get("confidence")) or 0.0
                product_mode = normalize_text(product_cert.get("evidence_mode"))

                if product_mode != "direct" or product_conf < 0.90:
                    updated_fields = append_inference_field(
                        updated_fields,
                        inference_events,
                        path="product.certification_scheme",
                        value=None,
                        evidence=(
                            "Corrected by inference: detected certification schemes are typical biomass/feedstock sourcing certifications, not product-level biochar certification schemes."
                        ),
                        source="project",
                        confidence=0.92,
                        evidence_strength="strong",
                        extractor="product_inference",
                        inference_rule_id="INF-PRODCT-001",
                        inputs_used=[
                            "product.certification_scheme",
                        ],
                        overwrite=True,
                    )

                    if not feedstock_cert:
                        updated_fields = append_inference_field(
                            updated_fields,
                            inference_events,
                            path="feedstock.certification_scheme",
                            value=raw_value,
                            evidence=(
                                "Reclassified from product certification to feedstock certification because the detected schemes are associated with biomass sourcing."
                            ),
                            source="project",
                            confidence=0.91,
                            evidence_strength="strong",
                            extractor="product_inference",
                            inference_rule_id="INF-PRODCT-002",
                            inputs_used=[
                                "product.certification_scheme",
                            ],
                        )

        return {
            "normalized_fields": updated_fields,
            "inference_events": inference_events,
        }
