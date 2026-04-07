import re
from typing import Any, Dict, List

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    filter_fields_by_paths,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


QUANT_PREFIXES = [
    "quantification.",
    "biochar.characterization.",
    "product.",
    "legal.",
]


QUANT_EXTRA_PATHS = [
    "ghg_accounting.system_boundary_defined",
    "ghg_accounting.baseline_defined",
    "monitoring_reporting.uncertainty_method",
]


def get_fields() -> List[Dict[str, Any]]:
    prefixed = filter_fields_by_prefixes(EXTRACTION_FIELDS, QUANT_PREFIXES)
    extra = filter_fields_by_paths(EXTRACTION_FIELDS, QUANT_EXTRA_PATHS)

    merged = {f["path"]: f for f in prefixed}
    for f in extra:
        merged[f["path"]] = f

    return list(merged.values())


def _instructions() -> str:
    return """
Focus on quantification, boundaries, uncertainty, product standards, laboratory evidence,
and legal / measurement references.

Important interpretation rules:
- Count quantification.crediting_activity_boundaries when the project explicitly describes
  construction/manufacturing, operations, closure/disposal, included SSRs, or equivalent
  crediting activity boundaries.
- Count quantification.storage_emissions_accounted when the text explicitly states that
  storage emissions, soil application emissions, or storage pathway emissions are included
  in the boundary / LCA / accounting statement.
- Count quantification.input_variables when the project discloses key quantification inputs,
  assumptions, or parameters (e.g. yield, residues %, soil temperature, collection efficiency).
- Count quantification.input_uncertainties when the project discloses Monte Carlo,
  variance propagation, conservative parameter selection, min/max values, or explicit
  uncertainty treatment.
- Count ghg_accounting.system_boundary_defined when the project explicitly defines the
  system boundary or project boundary.
- Count ghg_accounting.baseline_defined when the project explicitly defines the baseline
  or counterfactual scenario.
- Count product.standard_compliance when compliance with ASTM/EPA/EN/Isometric-type
  product or testing standards is evidenced.
- Count product.certification_scheme when named schemes or standard references are listed.
- Count biochar.characterization.ongoing_monitoring_plan when the project explicitly describes
  recurring post-baseline monitoring/testing for biochar characterization (e.g., periodic or annual
  lab analysis plan, defined recurring monitoring cadence, or ongoing characterization protocol).
  Do not mark true for one-time baseline testing only.

Prefer null over false if the evidence is unclear.
"""


def apply_local_heuristics(
    project_context: str,
    methodology_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    project_text = (project_context or "").lower()
    methodology_text = (methodology_context or "").lower()
    combined_text = f"{project_text}\n{methodology_text}"

    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------
    # quantification.crediting_activity_boundaries
    # ------------------------------------------------------------
    current = field_map.get("quantification.crediting_activity_boundaries", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"construction/manufacturing boundaries", combined_text)
            or re.search(r"operation boundaries", combined_text)
            or re.search(r"closure/disposal boundaries", combined_text)
            or re.search(r"activities leading to credits", combined_text)
            or re.search(r"all ghg ssrs inclusion", combined_text)
        ):
            upsert_field(
                field_map,
                path="quantification.crediting_activity_boundaries",
                value=True,
                evidence="Heuristic match: construction, operation, closure, and credited-activity boundaries are explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.95,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # quantification.storage_emissions_accounted
    # ------------------------------------------------------------
    current = field_map.get("quantification.storage_emissions_accounted", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"biochar soil application", combined_text)
            and (
                re.search(r"included", combined_text)
                or re.search(r"accounted", combined_text)
                or re.search(r"system boundary", combined_text)
            )
        ):
            upsert_field(
                field_map,
                path="quantification.storage_emissions_accounted",
                value=True,
                evidence="Heuristic match: storage / soil-application emissions are explicitly included or accounted for in the boundary.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.88,
                evidence_strength="moderate",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # quantification.input_variables
    # ------------------------------------------------------------
    current = field_map.get("quantification.input_variables", {}).get("value")
    if current in (None, False, "", []):
        variable_markers = [
            "residues: 6% of commercial wood mass",
            "collection efficiency",
            "biochar yield",
            "soil temperature",
            "yield 30-35%",
            "key assumptions",
            "minimum and maximum values",
        ]
        if any(marker in combined_text for marker in variable_markers):
            upsert_field(
                field_map,
                path="quantification.input_variables",
                value=True,
                evidence="Heuristic match: key quantification variables and assumptions are explicitly disclosed.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # quantification.input_uncertainties
    # ------------------------------------------------------------
    current = field_map.get("quantification.input_uncertainties", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"monte carlo", combined_text)
            or re.search(r"variance propagation", combined_text)
            or re.search(r"uncertainty analysis", combined_text)
            or re.search(r"conservative parameter selection", combined_text)
            or re.search(r"minimum and maximum values", combined_text)
        ):
            upsert_field(
                field_map,
                path="quantification.input_uncertainties",
                value=True,
                evidence="Heuristic match: uncertainty treatment is explicitly described (Monte Carlo / variance propagation / conservative inputs).",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # ghg_accounting.system_boundary_defined
    # ------------------------------------------------------------
    current = field_map.get("ghg_accounting.system_boundary_defined", {}).get("value")
    if current in (None, False, "", []):
        if re.search(r"system boundary", combined_text) or re.search(r"project boundary", combined_text):
            upsert_field(
                field_map,
                path="ghg_accounting.system_boundary_defined",
                value=True,
                evidence="Heuristic match: project/system boundary is explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # ghg_accounting.baseline_defined
    # ------------------------------------------------------------
    current = field_map.get("ghg_accounting.baseline_defined", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"baseline", combined_text)
            or re.search(r"counterfactual", combined_text)
            or re.search(r"absence of the project", combined_text)
            or re.search(r"open burning of residues", combined_text)
        ):
            upsert_field(
                field_map,
                path="ghg_accounting.baseline_defined",
                value=True,
                evidence="Heuristic match: baseline / counterfactual scenario is explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # monitoring_reporting.uncertainty_method
    # ------------------------------------------------------------
    current = field_map.get("monitoring_reporting.uncertainty_method", {}).get("value")
    if current in (None, False, "", []):
        if re.search(r"monte carlo", combined_text):
            upsert_field(
                field_map,
                path="monitoring_reporting.uncertainty_method",
                value="monte_carlo",
                evidence="Heuristic match: Monte Carlo uncertainty method explicitly referenced.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.95,
                evidence_strength="strong",
                evidence_mode="direct",
            )
        elif re.search(r"variance propagation", combined_text):
            upsert_field(
                field_map,
                path="monitoring_reporting.uncertainty_method",
                value="variance_propagation",
                evidence="Heuristic match: variance propagation explicitly referenced.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.chemical_analysis_performed
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.chemical_analysis_performed", {}).get("value")
    if current in (None, False, "", []):
        if re.search(r"chemical analysis", combined_text) or re.search(r"laboratory analyses", combined_text):
            upsert_field(
                field_map,
                path="biochar.characterization.chemical_analysis_performed",
                value=True,
                evidence="Heuristic match: chemical/laboratory analysis is explicitly documented.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.lab_reports
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.lab_reports", {}).get("value")
    if current in (None, False, "", []):
        if re.search(r"iso/iec 17025", combined_text) or re.search(r"laboratory certificate", combined_text):
            upsert_field(
                field_map,
                path="biochar.characterization.lab_reports",
                value=True,
                evidence="Heuristic match: accredited laboratory/certificate evidence is explicitly documented.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.required_measurements_complete
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.required_measurements_complete", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"total carbon", combined_text)
            and re.search(r"h/corg", combined_text)
            and re.search(r"fixed carbon", combined_text)
        ):
            upsert_field(
                field_map,
                path="biochar.characterization.required_measurements_complete",
                value=True,
                evidence="Heuristic match: permanence-related required measurements are explicitly listed.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.measurement_values
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.measurement_values", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"total carbon", combined_text)
            or re.search(r"h/corg", combined_text)
            or re.search(r"volatile matter", combined_text)
            or re.search(r"fixed carbon", combined_text)
            or re.search(r"ash content", combined_text)
        ):
            upsert_field(
                field_map,
                path="biochar.characterization.measurement_values",
                value=True,
                evidence="Heuristic match: measured biochar properties/values are explicitly listed.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.91,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.approach_description
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.approach_description", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"the project measures and documents all relevant chemical properties", combined_text)
            or re.search(r"durability is demonstrated by", combined_text)
            or re.search(r"analytical methods", combined_text)
        ):
            upsert_field(
                field_map,
                path="biochar.characterization.approach_description",
                value=True,
                evidence="Heuristic match: characterization approach is explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # biochar.characterization.contaminant_testing
    # ------------------------------------------------------------
    current = field_map.get("biochar.characterization.contaminant_testing", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"heavy metals", combined_text)
            or re.search(r"pah", combined_text)
            or re.search(r"organic contaminants", combined_text)
            or re.search(r"epa 8270d", combined_text)
        ):
            upsert_field(
                field_map,
                path="biochar.characterization.contaminant_testing",
                value=True,
                evidence="Heuristic match: heavy metals / PAHs / contaminant testing is explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.94,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # product.standard_compliance
    # ------------------------------------------------------------
    current = field_map.get("product.standard_compliance", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"astm", combined_text)
            or re.search(r"epa 8270d", combined_text)
            or re.search(r"en 16181", combined_text)
            or re.search(r"isometric bicrs", combined_text)
        ):
            upsert_field(
                field_map,
                path="product.standard_compliance",
                value=True,
                evidence="Heuristic match: product/testing compliance standards are explicitly referenced.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.93,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # product.certification_scheme
    # ------------------------------------------------------------
    current = field_map.get("product.certification_scheme", {}).get("value")
    if current in (None, False, "", []):
        schemes = []

        if re.search(r"isometric bicrs", combined_text):
            schemes.append("Isometric BiCRS")
        if re.search(r"astm d1762-84", combined_text):
            schemes.append("ASTM D1762-84")
        if re.search(r"astm d5373", combined_text):
            schemes.append("ASTM D5373")
        if re.search(r"epa 8270d", combined_text):
            schemes.append("EPA 8270D")
        if re.search(r"en 16181", combined_text):
            schemes.append("EN 16181")
        if re.search(r"iso/iec 17025", combined_text):
            schemes.append("ISO/IEC 17025")

        if schemes:
            upsert_field(
                field_map,
                path="product.certification_scheme",
                value=", ".join(schemes),
                evidence="Heuristic match: explicit standards/certification references found.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # legal.applicable_environmental_requirements
    # ------------------------------------------------------------
    current = field_map.get("legal.applicable_environmental_requirements", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"applicable environmental national, state, and local laws", combined_text)
            or re.search(r"environmental permits", combined_text)
            or re.search(r"environmental licensing", combined_text)
        ):
            upsert_field(
                field_map,
                path="legal.applicable_environmental_requirements",
                value=True,
                evidence="Heuristic match: applicable environmental legal requirements are explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.92,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    # ------------------------------------------------------------
    # legal.regulatory_measurement_methods
    # ------------------------------------------------------------
    current = field_map.get("legal.regulatory_measurement_methods", {}).get("value")
    if current in (None, False, "", []):
        if (
            re.search(r"astm", combined_text)
            or re.search(r"epa 8270d", combined_text)
            or re.search(r"en 16181", combined_text)
            or re.search(r"iso/iec 17025", combined_text)
            or re.search(r"analytical methods", combined_text)
        ):
            upsert_field(
                field_map,
                path="legal.regulatory_measurement_methods",
                value=True,
                evidence="Heuristic match: regulatory/standardized measurement methods are explicitly described.",
                extractor="quantification_mapper",
                fill_method="heuristic",
                confidence=0.90,
                evidence_strength="strong",
                evidence_mode="direct",
            )

    return merge_normalized_fields(list(field_map.values()))

# ------------------------------------------------------------
# SANITIZATION
# ------------------------------------------------------------
def sanitize_quantification_fields(
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    # ------------------------------------------------------------
    # REMOVE weak / misleading FALSE values
    # ------------------------------------------------------------
    value = field_map.get("quantification.storage_emissions_accounted", {}).get("value")

    if value is False:
        field_map.pop("quantification.storage_emissions_accounted", None)

    return list(field_map.values())


def run_quantification_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()

    prompt = build_domain_prompt(
        domain_name="quantification",
        fields=fields,
        project_context=project_context,
        methodology_context=methodology_context,
        domain_instructions=_instructions(),
    )

    raw = ai_client(prompt)
    payload = parse_extraction_payload(raw)

    normalized = normalize_domain_fields(
        extracted_payload=payload,
        fields=fields,
        extractor_name="quantification_mapper",
        fill_method="llm",
    )

    normalized = sanitize_quantification_fields(normalized)
    normalized = apply_local_heuristics(
        project_context=project_context,
        methodology_context=methodology_context,
        normalized_fields=normalized,
    )

    return {
        "normalized_fields": normalized,
        "raw_extraction": payload,
    }
