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
    has_pyrolysis_gas_recovery: bool          = False  # gases recuperados/combustados — hard gate Puro
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

    # ── Verra VM0044 ──────────────────────────────────────────────────────────
    # Tecnologia e permanência (driver primário na Verra: temperatura, não H/Corg)
    pyrolysis_temp_c:           Optional[float]= None   # °C — determina PRde,k (Tabela 3)
    verra_tech_class:           str            = ""     # "high" | "low" | ""
    has_continuous_temp_monitoring: bool       = False  # sensor contínuo obrigatório high-tech
    has_temp_calibration_plan:  bool           = False
    # has_gas_recovery é alias de has_pyrolysis_gas_recovery — usar o canônico

    # Feedstock Verra-específico
    is_purpose_grown:           bool           = False  # proibido (AC 4a)
    feedstock_imported:         bool           = False  # proibido (AC 4c)
    verra_feedstock_category:   str            = ""     # Tabela 1: agricultural_residue | food_processing |
                                                        # forestry_wood | recycling_economy |
                                                        # aquaculture | animal_manure | hcfa
    hcfa_fraction:              Optional[float]= None   # fração HCFA — máx 5%
    mineral_additive_fraction:  Optional[float]= None   # aditivos minerais — máx 10%
    # Sustentabilidade por tipo de feedstock
    high_residue_removal:       bool           = False  # agrícola: remoção > 50% dos resíduos do campo
    has_soil_health_docs:       bool           = False  # documentação de saúde do solo (agrícola)
    residue_volume_increased:   bool           = False  # alimentar: volume aumentou para o projeto

    # Baseline e destino do feedstock
    has_baseline_fate_evidence: bool           = False  # evidência AC 4b (decomposição ou queima)
    baseline_evidence_type:     str            = ""     # "govt_records" | "disposal_records" |
                                                        # "literature" | "survey" | "peer_reviewed"

    # Additionality Verra (VT0008)
    vt0008_path:                str            = ""     # "investment_comparison" | "benchmark"
    is_greenfield_facility:     bool           = True   # AC 1-3: instalação nova

    # Aplicação e via de uso
    soil_application:           bool           = True   # aplicação em solo
    used_as_fuel:               bool           = False  # proibido (AC 13)
    used_as_reducing_agent:     bool           = False  # proibido (AC 14)
    non_soil_carbon_loss_pct:   Optional[float]= None   # % C perdido em app não-solo — máx 50%

    # Monitoramento Verra
    has_continuous_weighing:    bool           = False  # Mt,k,p,y contínuo
    has_scale_calibration_plan: bool           = False
    has_invoice_cross_check:    bool           = False  # cross-check com NF
    has_fc_lab_analysis:        bool           = False  # FCp,t,p lab anual
    uses_fc_default_table4:     bool           = False  # usa default da Tabela 4
    methane_emission_factor:    Optional[float]= None   # Fe tCH4/t — default 0.049
    has_energy_lca:             bool           = False  # PED + PEC quantificados
    transport_distance_km:      Optional[float]= None   # km round-trip feedstock+biochar

    # Rastreabilidade
    has_chain_of_custody:       bool           = False  # tracking completo
    tracking_tool:              str            = ""     # "qr_code" | "gps" | "mobile_app" |
                                                        # "blockchain" | "nft" | "records"
    has_application_coordinates: bool          = False  # coordenadas geodésicas (Seção 9.3)
    has_additional_geographic_info: bool       = False

    # Gestão de dados
    has_offsite_backup:         bool           = False  # backup eletrônico offsite
    data_retention_years:       Optional[int]  = None   # mínimo 2 anos pós-crédito

    # Risco de reversão
    has_reversal_risk_assessment_verra: bool   = False  # Seção 8.4


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

    # ── Verra VM0044 — extração específica ───────────────────────────────────
    # Tecnologia e permanência
    "pyrolysis_temp_c":           "What is the average pyrolysis temperature in Celsius? (number or null)",
    "verra_tech_class":           "Is the facility classified as high-tech (automated temperature control) or low-tech (artisanal/simple kilns)? (high | low | not_stated)",
    "has_continuous_temp_monitoring": "Is there continuous temperature monitoring of the pyrolysis process with a recordable electronic signal?",
    "has_temp_calibration_plan":  "Is there a calibration plan for temperature sensors?",
    "has_pyrolysis_gas_recovery": "Are pyrolysis gases recovered or combusted (gas burner, flare, CHP, energy recovery system)? Applies to all standards — Puro.Earth hard gate, Verra PEP=0 classification, Isometric net-negativity. Answer FALSE if gases are vented untreated.",

    # Feedstock Verra
    "is_purpose_grown":           "Is the feedstock purpose-grown biomass (cultivated specifically for this project, not waste)? TRUE only if clearly stated.",
    "feedstock_imported":         "Is the feedstock imported from another country? TRUE only if explicitly stated.",
    "verra_feedstock_category":   "Which Verra VM0044 Table 1 category does the feedstock belong to? (agricultural_residue | food_processing | forestry_wood | recycling_economy | aquaculture | animal_manure | hcfa | not_stated)",
    "hcfa_fraction":              "If high-carbon fly ash (HCFA) is used, what fraction of total feedstock does it represent? (number 0-1 or null)",
    "mineral_additive_fraction":  "What fraction of the biochar mix consists of mineral additives (lime, rock minerals, ash)? (number 0-1 or null)",

    # Baseline e destino do feedstock
    "has_baseline_fate_evidence": "Does the PDD provide evidence of what would happen to the feedstock without the project (decay or combustion)?",
    "baseline_evidence_type":     "What type of evidence is provided for the feedstock baseline fate? (govt_records | disposal_records | literature | survey | peer_reviewed | not_stated)",

    # Additionality Verra
    "vt0008_path":                "Which VT0008 path is used for additionality? (investment_comparison | benchmark | not_stated)",
    "is_greenfield_facility":     "Is this a new (greenfield) biochar production facility, not a retrofit of an existing operation? TRUE if new installation.",

    # Aplicação
    "soil_application":           "Is biochar applied to soil (as opposed to non-soil applications like construction or water filtration)?",
    "used_as_fuel":               "Is biochar used as a fuel or burned for energy? TRUE only if explicitly described.",
    "used_as_reducing_agent":     "Is biochar used as a reducing agent in steel production or similar? TRUE only if explicitly described.",
    "non_soil_carbon_loss_pct":   "For non-soil applications: what percentage of carbon is lost during use? (number 0-100 or null)",

    # Monitoramento Verra
    "has_continuous_weighing":    "Is there a continuous weighing system for biochar production (scales adjusted for moisture)?",
    "has_scale_calibration_plan": "Is there a calibration plan for weighing scales?",
    "has_invoice_cross_check":    "Does the monitoring plan include cross-checking biochar mass with sales receipts or invoices?",
    "has_fc_lab_analysis":        "Is organic carbon content (FCp) determined by laboratory analysis per IBI or EBC guidelines?",
    "uses_fc_default_table4":     "Does the project use default carbon fraction values from VM0044 Table 4 (instead of lab analysis)?",
    "methane_emission_factor":    "For low-tech facilities: what is the measured methane emission factor Fe (tCH4/tonne biochar)? (number or null; default is 0.049)",
    "has_energy_lca":             "Does the PDD quantify energy-related emissions from pre-treatment (PED) and auxiliary energy (PEC) using CDM TOOL03 and TOOL05?",
    "transport_distance_km":      "What is the total round-trip transport distance for feedstock and biochar (km)? (number or null)",

    # Rastreabilidade
    "has_chain_of_custody":       "Does the PDD describe a chain of custody tracking system from feedstock sourcing to biochar application?",
    "tracking_tool":              "What tracking tool is described? (qr_code | gps | mobile_app | blockchain | nft | records | not_stated)",
    "has_application_coordinates":"Does the PDD provide geodetic coordinates for the biochar application sites?",
    "has_additional_geographic_info": "Does the PDD provide additional geographic information about application sites to enable VVB sampling?",

    # Gestão de dados
    "has_offsite_backup":         "Does the monitoring plan describe an offsite electronic backup for all logged data?",
    "data_retention_years":       "How many years of data retention are specified? (integer or null; minimum required is 2 years after crediting period)",

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
            "includes_forest_biomass":  p.is_forest_biomass,
            "from_land_clearing":       p.from_land_clearing,
            "uses_mixed_waste":         p.uses_mixed_waste,
            "uses_coal_ash":            p.uses_coal_ash,
            "high_residue_removal":     p.high_residue_removal,
            "has_soil_health_docs":     p.has_soil_health_docs,
            "residue_volume_increased": p.residue_volume_increased,
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
            # Inferência: LCA implica boundary e GHG statement definidos
            "boundary":             "defined" if (p.has_system_boundary or p.has_lca) else None,
            "system_boundary_defined": p.has_system_boundary or p.has_lca,
            "ghg_sources":          "defined" if (p.has_system_boundary or p.has_ghg_statement) else None,
            "leakage":              "assessed" if p.has_leakage_assessment else None,
            "baseline":             "documented" if p.has_baseline else None,
            "baseline_scenario":    "documented" if p.has_baseline else None,
            "uncertainty_analysis": "documented" if p.has_uncertainty_analysis else None,
            "sensitivity_analysis": "documented" if (p.has_sensitivity_analysis or p.has_uncertainty_analysis) else None,
            "uncertainty_method":   "documented" if p.has_uncertainty_analysis else None,
            "net_negative":         p.is_net_negative,
            "net_negative_claim":   p.is_net_negative,
            "models":               "documented" if p.has_models_documented else None,
            "model_references":     "documented" if p.has_models_documented else None,
            "ghg_methodology":      "documented" if (p.has_ghg_statement or p.has_lca) else None,
            "calculation_methodology": "documented" if (p.has_ghg_statement or p.has_lca) else None,
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
            "durability_option":      p.durability_option,
            "permanence_option":      p.durability_option,
            "durability_threshold":   p.durability_option,
            "buffer_pool_pct":        p.buffer_pool_pct,
            "buffer_contribution":    p.buffer_pool_pct,
            "reversal_risk":          "assessed" if p.has_reversal_risk_assessment else None,
            "risk_assessment":        "assessed" if p.has_reversal_risk_assessment else None,
            "temperature_method":     p.soil_temp_method,
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
            "parameters":       "documented" if p.has_monitoring_table else None,
            "monitoring_plan":  "documented" if p.has_monitoring_table else None,
            "data_storage":     "documented" if p.has_data_storage_plan else None,
            "record_keeping":   "documented" if p.has_data_storage_plan else None,
            "baseline_soil":    "collected" if p.has_baseline_soil_samples else None,
            "soil_quality":     "documented" if p.has_soil_quality_monitoring else None,
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
            "performed":  p.has_lca,
            "boundary":   "defined" if (p.has_system_boundary or p.has_lca) else None,
            "input_variables":  "documented" if p.has_lca else None,
            "input_uncertainties": "documented" if p.has_uncertainty_analysis else None,
        },
        "quantification": {
            "lca_performed": p.has_lca,
            "input_variables":    "documented" if p.has_lca else None,
            "input_uncertainties":"documented" if p.has_uncertainty_analysis else None,
        },
        "ghg_accounting": {
            "system_boundary_defined": p.has_system_boundary or p.has_lca,
        },
        "verra": {
            "technology_class":          p.verra_tech_class,
            "is_greenfield_facility":    p.is_greenfield_facility,
            "is_purpose_grown":          p.is_purpose_grown,
            "feedstock_imported":        p.feedstock_imported,
            "feedstock_category":        p.verra_feedstock_category,
            "hcfa_fraction":             p.hcfa_fraction,
            "has_baseline_fate_evidence":p.has_baseline_fate_evidence,
            "pyrolysis_temp_c":          p.pyrolysis_temp_c,
            "has_continuous_temp_monitoring": p.has_continuous_temp_monitoring,
            "has_gas_recovery":          p.has_pyrolysis_gas_recovery,
            "soil_application":          p.soil_application,
            "used_as_fuel":              p.used_as_fuel,
            "has_continuous_weighing":   p.has_continuous_weighing,
            "has_fc_lab_analysis":       p.has_fc_lab_analysis,
            "transport_distance_km":     p.transport_distance_km,
            "has_chain_of_custody":      p.has_chain_of_custody,
            "has_application_coordinates": p.has_application_coordinates,
            "has_offsite_backup":        p.has_offsite_backup,
            "data_retention_years":      p.data_retention_years,
            "vt0008_path":               p.vt0008_path,
            # Sustentabilidade por tipo de feedstock
            "high_residue_removal":      p.high_residue_removal,
            "has_soil_health_docs":      p.has_soil_health_docs,
            "residue_volume_increased":  p.residue_volume_increased,
        },
        "methodology": {
            "storage_pathway":   p.storage_pathway,
            "durability_threshold": p.durability_option,
            "lca_performed":     p.has_lca,
            "ghg_approach":      "documented" if (p.has_ghg_statement or p.has_lca) else None,
            "protocol":          "Puro.Earth" if p.has_puro_sdg_template else "Isometric",
            "standard":          "Puro.Earth" if p.has_puro_sdg_template else "Isometric",
        },
    }


def gas_sensor_str(p: ProjectProfile) -> Optional[str]:
    if not p.has_gas_sensors:
        return None
    return p.gas_sensor_method or "present"
