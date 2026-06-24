"""
Co2mply — ProjectProfile: schema universal padronizado para avaliação multi-metodologia.

Substitui o project_data dict de texto livre por um dataclass com campos
booleanos explícitos e tipados. Cada campo é respondido com YES/NO pelo
extrator — sem inferência, sem keyword matching nas funções de lógica.

Filosofia:
  - Extração: LLM responde perguntas booleanas com citação do PDD
  - Lógica: funções usam profile.campo diretamente (zero keyword matching)
  - Adapter: profile_to_legacy_dict() converte para project_data para funções legadas
"""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from typing import Optional, Any
import json


# ── Dataclass principal ────────────────────────────────────────────────────────

@dataclass
class ProjectProfile:

    # ── Identidade do projeto ─────────────────────────────────────────────────
    project_name:              str            = ""
    project_description:       str            = ""
    project_country:           str            = ""
    project_locations:         list           = field(default_factory=list)
    country_cpi:               Optional[float]= None   # Corruption Perceptions Index
    participants_listed:       bool           = False
    has_ownership_evidence:    bool           = False
    has_technical_description: bool           = False
    estimated_credits_tco2:    Optional[float]= None

    # ── Feedstock ─────────────────────────────────────────────────────────────
    feedstock_type:            str            = "unknown"
    # "agricultural_residue" | "forest_biomass" | "urban_wood" |
    # "food_waste" | "sewage_sludge" | "mixed" | "other"
    is_forest_biomass:         bool           = False
    uses_mixed_waste:          bool           = False   # fossil + biogênico → Puro inelegível
    uses_coal_ash:             bool           = False   # Puro inelegível (Clarificação 010)

    # Opções de sustentabilidade florestal (Puro Clarificação 006)
    has_fsc_certification:     bool           = False
    has_sfi_certification:     bool           = False
    has_pefc_certification:    bool           = False
    has_isae3000_dossier:      bool           = False   # alternativa Puro — nova!
    has_government_mgmt_plan:  bool           = False   # CPI ≥ 50 + 4 itens
    govt_plan_authority:       bool           = False   # item 1: autoridade local
    govt_plan_requirements:    bool           = False   # item 2: requisitos de sustentabilidade
    govt_plan_oversight:       bool           = False   # item 3: tipo de supervisão
    govt_plan_documents:       bool           = False   # item 4: documentos em inglês/traduzidos

    # Elegibilidade do feedstock agrícola (land clearing)
    from_land_clearing:        bool           = False
    has_land_clearing_permit:  bool           = False
    land_clearing_counterfactual: bool        = False
    land_clearing_non_economic: bool          = False  # só frações não comercializáveis
    land_clearing_not_protected: bool         = False  # fora de áreas protegidas

    # ── Produção e tecnologia ─────────────────────────────────────────────────
    reactor_type:              str            = ""
    storage_pathway:           str            = "soil"
    # "soil" | "built_environment" | "ocean" | "geological" | "other"

    # ── Contabilidade de carbono ──────────────────────────────────────────────
    has_lca:                   bool           = False
    has_system_boundary:       bool           = False
    has_baseline:              bool           = False
    has_leakage_assessment:    bool           = False
    has_uncertainty_analysis:  bool           = False
    has_sensitivity_analysis:  bool           = False
    has_ghg_statement:         bool           = False
    has_models_documented:     bool           = False
    is_net_negative:           bool           = False

    # ── Adicionalidade ────────────────────────────────────────────────────────
    has_financial_additionality:     bool     = False
    additionality_method:            str      = ""
    # "cost_analysis" | "irr_npv" | "barriers" | ""
    is_first_of_its_kind:            bool     = False
    irr_without_carbon:              Optional[float] = None
    financial_additionality_exemption_claimed: bool = False  # alega isenção → flag Puro
    has_common_practice_evidence:    bool     = False
    has_regulatory_additionality:    bool     = False
    has_environmental_additionality: bool     = False

    # ── Permanência ───────────────────────────────────────────────────────────
    durability_option:         str            = ""
    # "200_years" | "1000_years" | ""
    h_c_ratio:                 Optional[float]= None
    o_c_ratio:                 Optional[float]= None
    has_soil_temp_method:      bool           = False
    soil_temp_method:          str            = ""
    # "direct_measurement" | "lembrechts_database" | "other" | ""
    has_reversal_risk_assessment: bool        = False
    buffer_pool_pct:           Optional[float]= None
    has_non_soil_eol_plan:     bool           = False  # built environment end-of-life

    # ── Monitoramento ─────────────────────────────────────────────────────────
    has_monitoring_table:      bool           = False
    has_data_storage_plan:     bool           = False
    data_retention_years:      Optional[int]  = None
    sampling_method:           str            = ""
    # "method_a" | "method_b" | ""
    sample_count_per_batch:    Optional[int]  = None
    sample_age_months:         Optional[int]  = None  # idade máxima ao analisar
    has_iso17025_lab:          bool           = False

    # ── Caracterização do biochar ─────────────────────────────────────────────
    has_characterization_standards: bool      = False
    has_chemical_analysis_plan:     bool      = False
    has_physical_analysis_plan:     bool      = False
    # Valores operacionais (lab results)
    pah_value:                 Optional[float]= None   # mg/kg
    pcb_value:                 Optional[float]= None   # mg/kg
    pcdd_f_value:              Optional[float]= None   # ng/kg
    heavy_metals_documented:   bool           = False
    quality_standard:          str            = ""
    # "local_regulation" | "ibi" | "ebc" | "wbc" | ""

    # ── Ambiental e Social ────────────────────────────────────────────────────
    has_env_compliance:        bool           = False
    has_env_social_assessment: bool           = False
    has_no_net_env_harm:       bool           = False
    has_no_net_social_harm:    bool           = False
    has_pah_analysis:          bool           = False
    has_pollution_prevention:  bool           = False
    has_adaptive_management:   bool           = False
    adaptive_management_triggers: int         = 0     # nº de gatilhos documentados (mín 4)
    has_stakeholder_consultation: bool        = False
    has_grievance_mechanism:   bool           = False
    grievance_ack_days:        Optional[int]  = None  # ≤ 14 dias
    grievance_res_days:        Optional[int]  = None  # ≤ 60 dias
    has_sdg_reporting:         bool           = False  # obrigatório Puro, opcional Isometric
    has_baseline_soil_samples: bool           = False  # solo — operacional
    has_soil_quality_monitoring: bool         = False  # solo — operacional
    has_closure_plan:          bool           = False

    # ── Reator e documentação técnica ─────────────────────────────────────────
    has_engineering_diagram:   bool           = False
    has_gas_sensors:           bool           = False
    gas_sensor_method:         str            = ""
    # "reactor_spec" | "continuous_pressure" | "annual_test" | ""
    has_material_justification: bool          = False
    has_high_pressure:         bool           = False  # > 0.5 Bar → Diretiva 2014/68/EU
    has_maintenance_plan:      bool           = False

    # ── Campos metodologia-específicos ────────────────────────────────────────
    # Isometric
    has_isometric_protocol_justification: bool = False
    uses_lembrechts_database:  bool           = False

    # Puro
    has_puro_sdg_template:     bool           = False
    has_puro_project_description_template: bool = False
    issuance_delay_expected_months: Optional[int] = None  # ≤ 18 para Puro


# ── Extração via LLM ──────────────────────────────────────────────────────────

PROFILE_QUESTIONS = {
    # Projeto
    "project_name":              "What is the official name of the project?",
    "project_country":           "In which country is the project located?",
    "participants_listed":       "Does the PDD include a complete list of project participants with name, role, registration, address, contact and email?",
    "has_ownership_evidence":    "Does the PDD provide evidence of legal ownership over the carbon removal rights?",
    "has_technical_description": "Does the PDD include a technical description of the biochar production process and equipment?",

    # Feedstock
    "feedstock_type":            "What type of feedstock/biomass is used? (agricultural_residue | forest_biomass | urban_wood | food_waste | sewage_sludge | mixed | other)",
    "is_forest_biomass":         "Is the feedstock sourced from forests or forestry operations?",
    "uses_mixed_waste":          "Does the feedstock include any mixture of fossil-derived materials (plastics, synthetic fibers) with biomass?",
    "uses_coal_ash":             "Does the feedstock include coal ash or any by-product of coal combustion?",

    # Sustentabilidade florestal
    "has_fsc_certification":     "Is there an active FSC (Forest Stewardship Council) Forest Management Certification? Answer TRUE only if explicitly stated with a certificate.",
    "has_sfi_certification":     "Is there an active SFI (Sustainable Forestry Initiative) Certification?",
    "has_pefc_certification":    "Is there an active PEFC Sustainable Forest Management Certification?",
    "has_isae3000_dossier":      "Is there a sustainability dossier audited by an independent third party under ISAE 3000?",
    "has_government_mgmt_plan":  "Is there a government-approved forest management plan or logging approval from a local authority?",

    # Land clearing
    "from_land_clearing":        "Is the feedstock sourced from land clearing activities?",
    "has_land_clearing_permit":  "If from land clearing: is there a valid permit or government approval for the land clearing?",

    # Carbon accounting
    "has_lca":                   "Does the PDD include or reference a full Life Cycle Assessment (LCA)?",
    "has_system_boundary":       "Does the PDD define the system boundary (temporal, geographic, GHG sources)?",
    "has_baseline":              "Does the PDD define and evidence a baseline scenario (counterfactual)?",
    "has_leakage_assessment":    "Does the PDD include a leakage assessment with quantification?",
    "has_uncertainty_analysis":  "Does the PDD include an uncertainty analysis or method description?",
    "has_sensitivity_analysis":  "Does the PDD include a sensitivity analysis?",
    "is_net_negative":           "Does the PDD demonstrate that the net climate impact is negative after accounting for all process emissions and leakage?",

    # Adicionalidade
    "has_financial_additionality": "Does the PDD demonstrate financial additionality (project not viable without carbon revenue)?",
    "additionality_method":      "Which method is used for financial additionality? (cost_analysis | irr_npv | barriers | none)",
    "is_first_of_its_kind":      "Does the PDD claim the project is 'first-of-its-kind' or 'innovative/pioneering' as a basis for additionality?",
    "has_common_practice_evidence": "Does the PDD provide evidence that similar projects are NOT common practice?",
    "has_regulatory_additionality": "Does the PDD confirm the project is not required by law or regulation?",

    # Permanência
    "durability_option":         "Which durability threshold is selected? (200_years | 1000_years | not_stated)",
    "h_c_ratio":                 "What is the H/Corg molar ratio of the biochar? (number or null)",
    "o_c_ratio":                 "What is the O/Corg molar ratio of the biochar? (number or null)",
    "has_soil_temp_method":      "Is there a method described for measuring/obtaining mean annual soil temperature?",
    "soil_temp_method":          "Which soil temperature method is used? (direct_measurement | lembrechts_database | other | not_stated)",
    "uses_lembrechts_database":  "Does the PDD specifically reference the Lembrechts et al. global soil temperature database?",
    "buffer_pool_pct":           "What is the buffer pool percentage contribution? (number, e.g. 0.02 for 2%, or null)",

    # Storage
    "storage_pathway":           "What is the primary storage/application pathway? (soil | built_environment | other)",
    "has_non_soil_eol_plan":     "For built environment / non-soil: is there documentation of the end-of-life treatment confirming biochar will not be incinerated?",

    # Monitoramento
    "has_monitoring_table":      "Does the PDD include a monitoring parameter table?",
    "has_data_storage_plan":     "Does the PDD describe a data collection and storage approach with retention period?",
    "sampling_method":           "Which sampling method is described? (method_a = every batch | method_b = 1 per 10 batches | not_described)",
    "sample_count_per_batch":    "What is the minimum number of samples per batch? (integer or null)",
    "has_iso17025_lab":          "Is an ISO 17025 certified laboratory identified for biochar characterization?",

    # Caracterização
    "has_characterization_standards": "Does the PDD list the characterization standards used (ISO, ASTM, EBC, IBI)?",
    "pah_value":                 "What is the PAH content of the biochar in mg/kg? (number or null)",
    "pcb_value":                 "What is the PCB content in mg/kg? (number or null)",
    "pcdd_f_value":              "What is the PCDD/F content in ng/kg? (number or null)",
    "quality_standard":          "Which quality standard applies to PAH limits? (local_regulation | ibi | ebc | wbc | not_stated)",

    # E&S
    "has_env_compliance":        "Does the PDD outline compliance with applicable environmental laws and regulations?",
    "has_no_net_env_harm":       "Does the PDD demonstrate no net environmental harm?",
    "has_no_net_social_harm":    "Does the PDD evaluate and mitigate potential social harms?",
    "has_pah_analysis":          "Does the PDD include PAH analysis or plan for PAH testing?",
    "has_pollution_prevention":  "Does the PDD describe pollution prevention measures for PAHs, heavy metals, PCBs and dioxins?",
    "has_adaptive_management":   "Does the PDD include an adaptive management plan?",
    "adaptive_management_triggers": "How many mandatory stop/pause triggers are documented in the adaptive management plan? (integer)",
    "has_stakeholder_consultation": "Does the PDD document stakeholder consultation with summary of comments?",
    "has_grievance_mechanism":   "Does the PDD describe a grievance mechanism for stakeholders?",
    "grievance_ack_days":        "What is the acknowledgement deadline for grievances in days? (integer or null)",
    "grievance_res_days":        "What is the resolution deadline for grievances in days? (integer or null)",
    "has_sdg_reporting":         "Does the PDD include SDG (Sustainable Development Goals) reporting or alignment documentation?",
    "has_closure_plan":          "Does the PDD describe project closure conditions and a closure plan?",

    # Reator
    "has_engineering_diagram":   "Does the PDD include an engineering design diagram of the pyrolysis reactor?",
    "has_gas_sensors":           "Does the PDD describe sensors or methods to detect/quantify pyrolysis gas leakage?",
    "gas_sensor_method":         "Which leakage detection method? (reactor_spec | continuous_pressure | annual_test | not_stated)",
    "has_material_justification":"Does the PDD justify the material selection for the reactor with thermal/mechanical analysis?",
    "has_maintenance_plan":      "Does the PDD include a reactor maintenance plan?",
}


def build_profile_extraction_prompt(pdd_text: str) -> str:
    questions_json = json.dumps(
        {k: v for k, v in PROFILE_QUESTIONS.items()},
        ensure_ascii=False, indent=2
    )
    return f"""You are auditing a biochar carbon removal project PDD (Project Design Document).

Answer each question based ONLY on explicit evidence in the document.
Rules:
- For boolean fields: return true only if EXPLICITLY stated. When in doubt: false.
- For string fields: use the specified options or return an empty string.
- For numeric fields: return the number or null.
- For each field, also include "evidence": a direct quote (≤50 words) from the document, or "" if false/null.

PDD CONTENT:
{pdd_text[:18000]}

QUESTIONS:
{questions_json}

Return ONLY valid JSON. No markdown. Format:
{{
  "field_name": {{"value": <bool|str|number|null>, "evidence": "<quote or empty>"}},
  ...
}}"""


def parse_profile_response(response_json: dict) -> ProjectProfile:
    """Converts LLM JSON response to ProjectProfile dataclass."""
    valid_fields = {f.name for f in dataclasses.fields(ProjectProfile)}
    kwargs = {}
    for field_name in valid_fields:
        entry = response_json.get(field_name)
        if entry is None:
            continue
        val = entry.get("value") if isinstance(entry, dict) else entry
        if val is not None:
            kwargs[field_name] = val
    return ProjectProfile(**{k: v for k, v in kwargs.items() if k in valid_fields})


async def extract_project_profile(
    pdd_text: str,
    openai_client: Any,
    model: str = "gpt-4.1",
) -> ProjectProfile:
    """Main extraction function — returns a strongly-typed ProjectProfile."""
    prompt = build_profile_extraction_prompt(pdd_text)
    resp = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Carbon project auditor. Return only valid JSON per the schema."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = json.loads(resp.choices[0].message.content)
    return parse_profile_response(raw)


# ── Adapter: profile → legacy project_data dict ────────────────────────────────

def profile_to_legacy_dict(p: ProjectProfile) -> dict:
    """
    Converts ProjectProfile to a project_data-compatible dict for legacy logic functions.
    Allows backward compatibility while migration of logic functions happens gradually.
    """
    cert = (
        "FSC" if p.has_fsc_certification else
        "SFI" if p.has_sfi_certification else
        "PEFC" if p.has_pefc_certification else
        "ISAE3000" if p.has_isae3000_dossier else
        ""
    )
    return {
        "project": {
            "name": p.project_name,
            "description": p.project_description,
            "country": p.project_country,
            "locations": p.project_locations,
        },
        "feedstock": {
            "biomass_type": p.feedstock_type,
            "certification_scheme": cert,
            "source_locations": p.project_locations,
            # Campos para applies_if dos requisitos Puro
            "includes_forest_biomass": p.is_forest_biomass,
            "from_land_clearing":      p.from_land_clearing,
            "uses_mixed_waste":        p.uses_mixed_waste,
            "uses_coal_ash":           p.uses_coal_ash,
        },
        "biochar": {
            "characterization": {
                "h_c_ratio": p.h_c_ratio,
                "o_c_ratio": p.o_c_ratio,
                "pah_mg_kg": p.pah_value,
                "pcb_mg_kg": p.pcb_value,
                "pcdd_f_ng_kg": p.pcdd_f_value,
                "quality_standard": p.quality_standard,
                "lab_accreditation": "ISO 17025" if p.has_iso17025_lab else "",
                "lab_reports": "documented" if p.has_iso17025_lab else None,
                "standards": p.has_characterization_standards,
            }
        },
        "carbon_accounting": {
            "boundary": "defined" if p.has_system_boundary else None,
            "leakage": "assessed" if p.has_leakage_assessment else None,
            "baseline": "documented" if p.has_baseline else None,
            "uncertainty_analysis": "documented" if p.has_uncertainty_analysis else None,
            "sensitivity_analysis": "documented" if p.has_sensitivity_analysis else None,
            "net_negative": p.is_net_negative,
            "net_negative_claim": p.is_net_negative,
            "models": "documented" if p.has_models_documented else None,
            "ghg_methodology": "documented" if p.has_ghg_statement else None,
        },
        "eligibility": {
            "additionality_claim": p.has_financial_additionality,
            "additionality_evidence": [p.additionality_method] if p.additionality_method else [],
            "additionality_method": p.additionality_method,
            "financial_additionality": p.additionality_method if p.has_financial_additionality else None,
            "eligible_pathway": "biochar",
            "net_negative_claim": p.is_net_negative,
            "baseline_scenario": "documented" if p.has_baseline else None,
            "not_required_by_law": p.has_regulatory_additionality,
            # Campos críticos para lógica Puro
            "first_of_its_kind_claim":               p.is_first_of_its_kind,
            "is_first_of_its_kind":                  p.is_first_of_its_kind,
            "financial_additionality_exemption_claimed": p.financial_additionality_exemption_claimed,
            "irr_without_carbon":                    p.irr_without_carbon,
            "common_practice":                       "documented" if p.has_common_practice_evidence else None,
        },
        "permanence": {
            "durability_option": p.durability_option,
            "buffer_pool_pct": p.buffer_pool_pct,
            "reversal_risk": "assessed" if p.has_reversal_risk_assessment else None,
            "temperature_method": p.soil_temp_method,
        },
        "storage": {
            "pathway": p.storage_pathway,
            "soil": {
                "annual_avg_temp_celsius": None,
                "temperature_method": p.soil_temp_method,
                "deployment_methods": [p.storage_pathway] if p.storage_pathway else [],
            },
            "end_of_life": "documented" if p.has_non_soil_eol_plan else None,
        },
        "monitoring": {
            "parameters": "documented" if p.has_monitoring_table else None,
            "data_storage": "documented" if p.has_data_storage_plan else None,
            "baseline_soil": "collected" if p.has_baseline_soil_samples else None,
            "soil_quality": "documented" if p.has_soil_quality_monitoring else None,
        },
        "sampling": {
            "sampling_method": p.sampling_method,
            "method": p.sampling_method,
            "samples_per_batch": p.sample_count_per_batch,
            "sample_count": p.sample_count_per_batch,
        },
        "safeguards": {
            "adaptive_management_plan": "documented" if p.has_adaptive_management else None,
            "stakeholder_consultation": "documented" if p.has_stakeholder_consultation else None,
            "grievance_mechanism": f"ack={p.grievance_ack_days}d res={p.grievance_res_days}d" if p.has_grievance_mechanism else None,
            "pollution_prevention": "documented" if p.has_pollution_prevention else None,
            "sdg_alignment": "documented" if p.has_sdg_reporting else None,
            "permits_documented": p.has_env_compliance,
            "no_environmental_harm": p.has_no_net_env_harm,
            "no_social_harm": p.has_no_net_social_harm,
            "environmental_assessment": "documented" if p.has_env_social_assessment else None,
            "closure_plan": "documented" if p.has_closure_plan else None,
            "regulatory_compliance": p.has_env_compliance,
        },
        "production": {
            "reactor_type": p.reactor_type,
            "system_description": p.reactor_type,
            "reactor_diagram": "present" if p.has_engineering_diagram else None,
            "leakage_sensors": gas_sensor_str(p),
            "maintenance_plan": "documented" if p.has_maintenance_plan else None,
            "reactor_material": "justified" if p.has_material_justification else None,
        },
        "legal": {
            "permits_documented": p.has_env_compliance,
            "applicable_environmental_requirements": p.has_env_compliance,
            "regulatory_compliance": p.has_env_compliance,
            "voluntary_nature": p.has_regulatory_additionality,
            "ownership_evidence": p.has_ownership_evidence,
        },
        "lca": {
            "performed": p.has_lca,
            "boundary": "defined" if p.has_system_boundary else None,
        },
        "methodology": {
            "storage_pathway": p.storage_pathway,
            "durability_threshold": p.durability_option,
            "lca_performed": p.has_lca,
            "ghg_approach": "documented" if p.has_ghg_statement else None,
            "protocol": "Puro.Earth" if p.has_puro_sdg_template else "Isometric",
        },
    }


def gas_sensor_str(p: ProjectProfile) -> Optional[str]:
    if not p.has_gas_sensors:
        return None
    return p.gas_sensor_method or "present"
