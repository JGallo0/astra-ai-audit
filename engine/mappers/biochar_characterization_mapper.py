# engine/mappers/biochar_characterization_mapper.py
"""
Mapper para propriedades químicas do biochar — Phase 3, campos numéricos.
Extrai: H/C ratio, O/C ratio, PCBs, PCDD/F, PAHs.

Estratégia híbrida:
  1. LLM com hints de Requirement ID (R-VGXA-0, R-MY64-0)
  2. Heurísticas regex para valores numéricos explícitos no texto
"""

import re
from typing import Any, Dict, List, Optional

from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.base import (
    build_domain_prompt,
    filter_fields_by_prefixes,
    merge_normalized_fields,
    normalize_domain_fields,
    parse_extraction_payload,
    upsert_field,
)


BIOCHAR_CHAR_PREFIXES = [
    "biochar.characterization.h_c_ratio",
    "biochar.characterization.o_c_ratio",
    "biochar.characterization.pcb_mg_kg",
    "biochar.characterization.pcdd_f_ng_kg",
    "biochar.characterization.pah_epa16_mg_kg",
]


def get_fields() -> List[Dict[str, Any]]:
    return [f for f in EXTRACTION_FIELDS if f["path"] in BIOCHAR_CHAR_PREFIXES]


def _instructions() -> str:
    return """
Focus on biochar chemical characterization results.
You are looking for NUMERIC VALUES from laboratory analysis reports.

Key fields:
- h_c_ratio (H/Corg): molar ratio of hydrogen to organic carbon. Typical values: 0.2–0.8.
  Protocol threshold: MUST be < 0.5 for 200-year durability. Look in biochar characterization appendix.
- o_c_ratio (O/Corg): molar ratio of oxygen to organic carbon. Threshold: < 0.2.
- pcb_mg_kg: polychlorinated biphenyls in mg/kg dry matter. Limit: ≤ 0.2 mg/kg.
- pcdd_f_ng_kg: dioxins/furans in ng/kg dry matter. Limit: ≤ 20 ng/kg.
- pah_epa16_mg_kg: sum of 16 EPA PAHs in mg/kg. Must be declared.

IMPORTANT:
- Extract the numeric VALUE, not a boolean.
- If a table shows H/C = 0.43, return 0.43.
- If a lab report mentions PCB < 0.05 mg/kg, return 0.05.
- Return null only if the value is truly not in the text.
- The PDD may reference an external lab report/annex — in that case return the value if visible,
  or return null if the annex is not in the provided text.
"""


# ── Regex heuristics for numeric values ──────────────────────────────────────

# H/C ratio patterns: "H/C ratio = 0.43", "H/Corg: 0.38", "H/C = 0.43", "H/C of 0.31"
_HC_PATTERNS = [
    r"H\s*/\s*C(?:org)?\s*(?:ratio|molar\s+ratio)?\s*[=:]\s*(\d+\.?\d*)",
    r"H\s*/\s*C(?:org)?\s*(?:ratio|molar\s+ratio)\s+(?:of\s+)?(\d+\.?\d*)",
    r"H\s*/\s*C(?:org)?\s+(?:of\s+)?(\d+\.?\d*)",
    r"hydrogen\s+to\s+(?:organic\s+)?carbon\s+(?:ratio\s+)?(?:of\s+|=\s*|:\s*)?(\d+\.?\d*)",
    r"H/Corg\s*[=:]\s*(\d+\.?\d*)",
    r"Horg\s*/\s*Corg\s*[=:]\s*(\d+\.?\d*)",
]

# O/C ratio patterns
_OC_PATTERNS = [
    r"O\s*/\s*C(?:org)?\s*(?:ratio|molar\s+ratio)?\s*[=:]\s*(\d+\.?\d*)",
    r"O\s*/\s*C(?:org)?\s*(?:ratio|molar\s+ratio)\s+(?:of\s+)?(\d+\.?\d*)",
    r"O\s*/\s*C(?:org)?\s+(?:of\s+)?(\d+\.?\d*)",
    r"oxygen\s+to\s+(?:organic\s+)?carbon\s+(?:ratio\s+)?(?:of\s+|=\s*|:\s*)?(\d+\.?\d*)",
    r"O/Corg\s*[=:]\s*(\d+\.?\d*)",
]

# PCB patterns: "PCB = 0.05 mg/kg", "PCBs < 0.1 mg/kg DM"
_PCB_PATTERNS = [
    r"PCB\s*[s]?\s*[=:<]\s*(\d+\.?\d*)\s*mg",
    r"polychlorinated\s+biphenyls?\s*[=:<]\s*(\d+\.?\d*)\s*mg",
    r"PCB\s*(?:concentration|level)?\s*(?:of\s+)?(\d+\.?\d*)\s*mg",
]

# PCDD/F patterns: "PCDD/F = 15 ng/kg", "dioxins < 20 ng/kg DM"
_PCDD_PATTERNS = [
    r"PCDD/F\s*[=:<]\s*(\d+\.?\d*)\s*ng",
    r"dioxins?\s*(?:and\s+furans?)?\s*[=:<]\s*(\d+\.?\d*)\s*ng",
    r"PCDD\s*[=:<]\s*(\d+\.?\d*)\s*ng",
    r"furans?\s*[=:<]\s*(\d+\.?\d*)\s*ng",
]

# PAH patterns: "PAHs = 0.5 mg/kg", "sum of 16 EPA PAHs: 0.8 mg/kg"
_PAH_PATTERNS = [
    r"PAH\s*s?\s*[=:<]\s*(\d+\.?\d*)\s*mg",
    r"sum\s+of\s+(?:\d+\s+)?EPA\s+PAH\s*s?\s*[=:<]?\s*(\d+\.?\d*)\s*mg",
    r"polycyclic\s+aromatic\s+hydrocarbons?\s*[=:<]\s*(\d+\.?\d*)\s*mg",
    r"EPA\s+16\s+PAH\s*s?\s*[=:<]?\s*(\d+\.?\d*)\s*mg",
]


def _try_regex_patterns(text: str, patterns: List[str]) -> Optional[float]:
    """Try a list of regex patterns and return the first numeric match."""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            try:
                return float(m.group(1))
            except (ValueError, IndexError):
                continue
    return None


def apply_local_heuristics(
    project_context: str,
    normalized_fields: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    text = project_context or ""
    field_map = {item["path"]: dict(item) for item in normalized_fields}

    def _set(path, value, evidence, confidence, strength="moderate"):
        if field_map.get(path, {}).get("value") is None and value is not None:
            upsert_field(
                field_map,
                path=path,
                value=value,
                evidence=evidence,
                extractor="biochar_characterization_mapper",
                fill_method="heuristic",
                confidence=confidence,
                evidence_strength=strength,
                evidence_mode="direct",
            )

    # H/C ratio
    hc = _try_regex_patterns(text, _HC_PATTERNS)
    if hc is not None:
        _set("biochar.characterization.h_c_ratio", hc,
             f"Regex match: H/Corg = {hc}", 0.93, "strong")

    # O/C ratio
    oc = _try_regex_patterns(text, _OC_PATTERNS)
    if oc is not None:
        _set("biochar.characterization.o_c_ratio", oc,
             f"Regex match: O/Corg = {oc}", 0.93, "strong")

    # PCB
    pcb = _try_regex_patterns(text, _PCB_PATTERNS)
    if pcb is not None:
        _set("biochar.characterization.pcb_mg_kg", pcb,
             f"Regex match: PCB = {pcb} mg/kg", 0.90, "strong")

    # PCDD/F
    pcdd = _try_regex_patterns(text, _PCDD_PATTERNS)
    if pcdd is not None:
        _set("biochar.characterization.pcdd_f_ng_kg", pcdd,
             f"Regex match: PCDD/F = {pcdd} ng/kg", 0.90, "strong")

    # PAHs
    pah = _try_regex_patterns(text, _PAH_PATTERNS)
    if pah is not None:
        _set("biochar.characterization.pah_epa16_mg_kg", pah,
             f"Regex match: PAH (EPA 16) = {pah} mg/kg", 0.88, "strong")

    return merge_normalized_fields(list(field_map.values()))


def run_biochar_characterization_mapper(
    ai_client,
    project_context: str,
    methodology_context: str,
) -> Dict[str, Any]:
    fields = get_fields()
    if not fields:
        return {"normalized_fields": [], "raw_extraction": {"fields": []}}

    # 1. Heuristics first (no LLM cost)
    pre = apply_local_heuristics(project_context, [])
    heuristic_paths = {f["path"] for f in pre if f.get("value") is not None}

    # 2. LLM for fields not caught by heuristics
    missing = [f for f in fields if f["path"] not in heuristic_paths]

    llm_normalized = []
    if missing:
        prompt = build_domain_prompt(
            domain_name="biochar_characterization",
            fields=missing,
            project_context=project_context,
            methodology_context=methodology_context,
            domain_instructions=_instructions(),
        )
        raw = ai_client(prompt)
        payload = parse_extraction_payload(raw)
        llm_normalized = normalize_domain_fields(
            extracted_payload=payload,
            fields=missing,
            extractor_name="biochar_characterization_mapper",
            fill_method="llm",
        )
    else:
        payload = {"fields": []}

    # 3. Merge heuristics + LLM (heuristics win on conflict)
    merged = merge_normalized_fields(pre + llm_normalized)

    return {
        "normalized_fields": merged,
        "raw_extraction": payload,
    }
