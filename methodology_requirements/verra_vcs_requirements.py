"""
Verra VCS VM0044 v1.2 — Requirements (Protocol-native, engine v1)

Fonte: VM0044 v1.2 — "Methodology for Biochar Utilization in Soil and
Non-Soil Applications", Verra VCS Program.

26 requisitos organizados em 8 módulos.
IDs no formato V-XXXX-0 (V = Verra).

Diferenças estruturais em relação a Isometric e Puro.Earth:
  - Permanência: determinada por TEMPERATURA de pirólise (Tabela 3), não H/Corg
  - H/Corg: gate binário de elegibilidade em solo (≤ 0.7), não entra em equações
  - Baseline: ERSS,y = 0 (conservador) — sempre zero para feedstock residual
  - N₂O/CH₄ do solo: explicitamente excluídos (negligíveis)
  - Low-tech: PRde default 0.56, Fe default 0.049 tCH4/t (Cornelissen et al. 2016)
  - Leakage: zero se transporte < 200 km (CDM TOOL12 apenas se > 200 km)
  - Additionality: 3 etapas obrigatórias (reg. surplus + positive list + VT0008)
  - Aplicações: solo E não-solo (construção, filtração) — mais amplo que Iso/Puro
"""

_VM0044_BASE = "https://verra.org/methodologies/vm0044-methodology-for-biochar-utilization-in-soil-and-non-soil-applications/"


def _design(description, hard_gate=False):
    return {"type": "plan", "description": description, "is_hard_gate": hard_gate}

def _design_only(description, hard_gate=True):
    return {
        "development": _design(description, hard_gate),
        "operational":  _design(description, hard_gate),
    }


VERRA_VCS_REQUIREMENTS = [

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: applicability — Condições de Aplicabilidade (AC 1-15)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-APPL-0",
        "title": "Applicability — greenfield facility and scope",
        "module": "applicability",
        "subcategory": "applicability:scope",
        "requirement_text": (
            "The project must install and operate a new (greenfield) biochar production facility "
            "that thermochemically converts eligible waste biomass to biochar. "
            "The methodology applies to soil and non-soil applications of biochar "
            "as a long-lived carbon sink. (AC 1-3)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_applicability_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC1", "AC2", "AC3"],
        "evidence_timing": _design_only(
            "Descrição da instalação nova e fronteira do sistema definida no PDD",
            hard_gate=True,
        ),
    },

    {
        "id": "V-FEED-0",
        "title": "Feedstock eligibility — waste biogenic, non-imported",
        "module": "applicability",
        "subcategory": "applicability:feedstock",
        "requirement_text": (
            "Feedstock must be: (a) purely biogenic waste biomass, not purpose-grown; "
            "(b) waste that would otherwise be left to decay or combusted without energy use; "
            "(c) not imported from other countries. (AC 4a-4c)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_feedstock_eligibility_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC4a", "AC4b", "AC4c"],
        "evidence_timing": _design_only(
            "Declaração de tipo e origem do feedstock com evidência do destino alternativo",
            hard_gate=True,
        ),
    },

    {
        "id": "V-FCAT-0",
        "title": "Feedstock category — Table 1 sustainability criteria",
        "module": "applicability",
        "subcategory": "applicability:feedstock",
        "requirement_text": (
            "Feedstock must belong to one of the 7 eligible categories in Table 1 and meet "
            "category-specific sustainability criteria: agricultural waste, food processing residues, "
            "forestry/wood processing, recycling economy (urban green waste, biosolids), "
            "aquaculture plants, animal manure, or high-carbon fly ash (HCFA ≤ 5%). "
            "Wood-based sources require proof of sustainable origin (PEFC, FSC, or CDM renewable biomass). "
            "(AC 4d and Table 1)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_feedstock_category_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC4d", "Table1"],
        "evidence_timing": _design_only(
            "Categoria de feedstock da Tabela 1 declarada e critérios de sustentabilidade documentados",
            hard_gate=True,
        ),
    },

    {
        "id": "V-TECH-0",
        "title": "Technology class — high-tech vs. low-tech facility",
        "module": "applicability",
        "subcategory": "applicability:technology",
        "requirement_text": (
            "High-tech facilities must have automated process controls and continuous temperature "
            "monitoring; process emissions (PEP,p,y) = 0 for high-tech. "
            "Low-tech facilities use methane emission default Fe = 0.049 tCH4/tonne (AC 5-8). "
            "Temperature monitoring (Tprod) determines the permanence factor PRde,k per Table 3: "
            "> 600°C → 0.89 | 450-600°C → 0.80 | 350-450°C → 0.65 | unknown → 0.56."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_technology_class_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC5", "AC6", "AC7", "AC8", "Table3"],
        "evidence_timing": _design_only(
            "Classificação tecnológica e temperatura de operação documentadas",
            hard_gate=False,
        ),
    },

    {
        "id": "V-HCOR-0",
        "title": "H:Corg ≤ 0.7 — soil application gate",
        "module": "applicability",
        "subcategory": "applicability:biochar_quality",
        "requirement_text": (
            "For any soil application, biochar must have a hydrogen to organic carbon molar ratio "
            "(H:Corg) ≤ 0.7, determined by laboratory analysis per IBI or EBC guidelines. "
            "NOTE: H:Corg is a binary eligibility gate in VM0044 only — it does NOT affect the "
            "permanence factor PRde,k (unlike Isometric and Puro.Earth). "
            "Non-soil applications are not subject to this requirement. (AC 10)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_hcorg_gate_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC10"],
        "evidence_timing": _design_only(
            "Análise laboratorial de H:Corg para aplicações em solo",
            hard_gate=True,
        ),
    },

    {
        "id": "V-APPL-S",
        "title": "Application type — soil/non-soil eligibility",
        "module": "applicability",
        "subcategory": "applicability:application",
        "requirement_text": (
            "Biochar may be applied to soil or used in non-soil applications (construction, "
            "water filtration, etc.) as a long-lived carbon sink. "
            "EXCLUDED: (AC 13) biochar burned as fuel or substitute for charcoal/coke; "
            "(AC 14) biochar used as reducing agent in steel production or activated carbon "
            "with > 50% carbon loss; (AC 15) non-soil applications with > 50% carbon loss."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_application_type_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC11", "AC12", "AC13", "AC14", "AC15"],
        "evidence_timing": _design_only(
            "Via de aplicação documentada — confirmação que biochar não será queimado ou oxidado",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: additionality — 3 etapas obrigatórias (Seção 7)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-REGS-0",
        "title": "Additionality Step 1 — Regulatory surplus",
        "module": "additionality",
        "subcategory": "additionality:regulatory",
        "requirement_text": (
            "The project must demonstrate regulatory surplus — the project activity is not required "
            "by any existing law, regulation, or mandatory standard. "
            "Demonstrated per VCS Standard requirements. (Section 7, Step 1)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_regulatory_surplus_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S7-Step1"],
        "evidence_timing": _design_only(
            "Declaração de surplus regulatório com referência às leis/regulações locais",
            hard_gate=True,
        ),
    },

    {
        "id": "V-PLST-0",
        "title": "Additionality Step 2 — Positive list (applicability conditions)",
        "module": "additionality",
        "subcategory": "additionality:positive_list",
        "requirement_text": (
            "Compliance with all VM0044 Applicability Conditions constitutes the positive list. "
            "The activity penetration option (Option A per VCS Methodology Requirements) was used "
            "to establish the positive list. No further positive list demonstration required "
            "if all ACs are met. (Section 7, Step 2)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_positive_list_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S7-Step2"],
        "evidence_timing": _design_only(
            "Cumprimento de todas as Applicability Conditions documentado no PDD",
            hard_gate=True,
        ),
    },

    {
        "id": "V-VT08-0",
        "title": "Additionality Step 3 — VT0008 investment analysis",
        "module": "additionality",
        "subcategory": "additionality:financial",
        "requirement_text": (
            "Projects must apply VCS tool VT0008 Additionality Assessment for the investment "
            "analysis step: Option 1 (investment comparison — demonstrate IRR/NPV not viable "
            "without carbon revenue) OR Option 2 (benchmark analysis — compare with sector "
            "performance benchmark). One of the two options is mandatory. (Section 7, Step 3)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_vt0008_investment_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S7-Step3", "VT0008"],
        "evidence_timing": _design_only(
            "Análise de investimento conforme VT0008 (Option 1 ou 2) documentada no PDD",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: baseline — Seção 6
    # ERSS,y = 0 (conservador). Apenas evidência do destino do feedstock.
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-BASE-0",
        "title": "Baseline scenario — zero sourcing emissions (conservative)",
        "module": "baseline",
        "subcategory": "baseline:scenario",
        "requirement_text": (
            "The baseline scenario is that waste biomass would otherwise decay or be combusted "
            "without energy use. Per VM0044 Section 6, baseline emissions at the sourcing stage "
            "(ERSS,y = BESS,y - PESS,y) are set to ZERO under the conservative approach. "
            "Credits derive only from carbon removed in biochar minus process emissions."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_baseline_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S6"],
        "evidence_timing": _design_only(
            "Seção de baseline no PDD com declaração de ERSS,y = 0",
            hard_gate=False,
        ),
    },

    {
        "id": "V-BFED-0",
        "title": "Baseline feedstock fate — evidence of decay or combustion",
        "module": "baseline",
        "subcategory": "baseline:feedstock_fate",
        "requirement_text": (
            "Project proponent must provide credible evidence of the baseline fate of feedstock: "
            "government records, waste disposal facility records, existing literature, "
            "regional survey data, or own survey. (AC 4b and Appendix 2)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_baseline_feedstock_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC4b", "Appendix2"],
        "evidence_timing": _design_only(
            "Evidência documentada do destino alternativo do feedstock (registros ou literatura)",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: permanence — Temperatura de pirólise (Tabela 3)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-PERM-0",
        "title": "Permanence factor PRde,k — pyrolysis temperature (Table 3)",
        "module": "permanence",
        "subcategory": "permanence:stability",
        "requirement_text": (
            "The permanence adjustment factor (PRde,k) is determined by pyrolysis temperature "
            "per VM0044 Table 3: "
            "> 600°C → PRde = 0.89 (high temperature / gasification); "
            "450-600°C → PRde = 0.80 (medium temperature); "
            "350-450°C → PRde = 0.65 (low temperature); "
            "Unknown / not measured → PRde = 0.56 (default, Figure 4Ap.1(b) IPCC 2019). "
            "CRITICAL DIFFERENCE from Isometric/Puro.Earth: H:Corg does NOT affect PRde,k. "
            "Temperature is the sole driver of permanence in VM0044."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_permanence_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["Table3", "Eq2", "Eq6"],
        "evidence_timing": _design_only(
            "Temperatura de pirólise documentada e PRde,k correspondente calculado",
            hard_gate=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: carbon_accounting — Equações 1-13 + contaminantes
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-TEMP-0",
        "title": "Temperature monitoring — continuous Tprod measurement",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:monitoring",
        "requirement_text": (
            "For high-tech facilities: Tprod must be monitored continuously using electronic "
            "instruments (thermocouple or thermoresistor with recordable signal), calibrated "
            "periodically against a primary independent device per manufacturer specifications. "
            "Aggregated to annual averages for reporting. "
            "Low-tech: temperature measurement not required, but PRde = 0.56 applies. (Section 9.2)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_temperature_monitoring_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.2-Tprod"],
        "evidence_timing": _design_only(
            "Sistema de monitoramento contínuo de temperatura com plano de calibração",
            hard_gate=False,
        ),
    },

    {
        "id": "V-CARB-0",
        "title": "Carbon content FCp,t,p — lab analysis or Table 4 defaults",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:measurement",
        "requirement_text": (
            "Organic carbon content (FCp,t,p) must be determined annually by lab analysis "
            "per IBI Biochar Testing Guidelines or EBC Production Guidelines, "
            "OR after any material change in feedstock or production parameters (whichever is more frequent). "
            "Low-tech / low-data alternative: Table 4 default values by feedstock category "
            "(e.g., wood → 0.77; agricultural → 0.65; manure → 0.38; biosolids → 0.35). (Section 9.2)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_carbon_content_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.2-FCp", "Table4"],
        "evidence_timing": _design_only(
            "Protocolo de análise laboratorial de carbono ou justificativa para uso de defaults da Tabela 4",
            hard_gate=True,
        ),
    },

    {
        "id": "V-MASS-0",
        "title": "Mass monitoring Mt,k,p,y — continuous weighing",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:measurement",
        "requirement_text": (
            "Total biochar mass (Mp,y) and mass by type and application (Mt,k,p,y) must be "
            "continuously recorded on a monthly basis using weighing scales adjusted for moisture. "
            "Scales must be calibrated per manufacturer specifications (or every 3 years minimum) "
            "and cross-checked annually against sales receipts or invoices. (Section 9.2)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_mass_monitoring_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.2-Mt"],
        "evidence_timing": _design_only(
            "Sistema de pesagem contínua com plano de calibração e cross-check descrito",
            hard_gate=True,
        ),
    },

    {
        "id": "V-PEPS-0",
        "title": "Process emissions PEPS,p,y — high-tech PEP=0 or low-tech Fe default",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:emissions",
        "requirement_text": (
            "Project emissions at production stage: "
            "High-tech facilities: PEP,p,y = 0 (de minimis, Eq. 3); "
            "still must quantify PED (pre-treatment) and PEC (auxiliary energy) via CDM TOOL03/TOOL05. "
            "Low-tech facilities: PEP,p,y = Fe × GWPCH4 × biochar_mass; "
            "Fe default = 0.049 tCH4/tonne (Cornelissen et al. 2016); GWPCH4 = 28 (IPCC AR5). "
            "(Equations 3, 7, 9)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_process_emissions_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["Eq3", "Eq7", "Eq9", "CDMTOOL03", "CDMTOOL05"],
        "evidence_timing": _design_only(
            "Classificação high/low-tech e cálculo de emissões de processo conforme metodologia",
            hard_gate=True,
        ),
    },

    {
        "id": "V-LEAK-0",
        "title": "Leakage LEy — transport distance threshold",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:leakage",
        "requirement_text": (
            "Total leakage: LEy = LEas + LEbd + LEts + LEtap. "
            "LEas = 0 (only waste biomass, no activity shift). "
            "LEbd = 0 (only residual biomass, no diversion). "
            "LEts and LEtap = 0 if round-trip transport distance ≤ 200 km; "
            "if > 200 km: apply CDM TOOL12 for freight transportation emissions. "
            "(Equation 13)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_leakage_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["Eq13", "CDMTOOL12"],
        "evidence_timing": _design_only(
            "Distância de transporte informada e leakage calculado (zero se < 200 km)",
            hard_gate=False,
        ),
    },

    {
        "id": "V-APPL-E",
        "title": "Application stage emissions PEAS,y",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:emissions",
        "requirement_text": (
            "Emissions at application stage: PEAS,y = EP,k,y + Eap,k,y. "
            "Eap,k,y (biochar utilization emissions) = 0 — negligible per Section 8. "
            "EP,k,y = processing emissions (electricity via CDM TOOL05, fossil fuels via CDM TOOL03). "
            "Typically near-zero for most projects. (Equations 11-12)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_application_emissions_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["Eq11", "Eq12"],
        "evidence_timing": _design_only(
            "Emissões de aplicação quantificadas ou justificativa de negligibilidade",
            hard_gate=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: biochar_quality — IBI/EBC, contaminantes, aditivos
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-QUAL-0",
        "title": "Biochar quality — IBI or EBC guidelines compliance",
        "module": "biochar_quality",
        "subcategory": "biochar_quality:standards",
        "requirement_text": (
            "Biochar from single or mixed eligible feedstock must comply with: "
            "IBI Biochar Testing Guidelines (for soil applications) OR "
            "EBC Production Guidelines. "
            "Laboratory must be accredited or approved by the relevant national agency. (AC 5-6)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_biochar_quality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC5", "AC6"],
        "evidence_timing": _design_only(
            "Declaração de conformidade com IBI ou EBC com laboratório acreditado identificado",
            hard_gate=True,
        ),
    },

    {
        "id": "V-CONT-0",
        "title": "Contaminants — heavy metals and PAH per IBI/EBC",
        "module": "biochar_quality",
        "subcategory": "biochar_quality:contaminants",
        "requirement_text": (
            "Biochar must meet IBI or EBC contaminant limits for heavy metals, PAH, PCB, and PCDD/F. "
            "IBI Biochar Standard limits (soil application): "
            "PAH ≤ 6 mg/kg (premium) or ≤ 20 mg/kg (basic); PCB ≤ 0.5 mg/kg. "
            "Processed timber for soil must not contain paint residues, solvents, or toxic impurities. "
            "Biosolids must comply with Table 1 recycling economy criteria."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_contaminants_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC5", "AC6", "Table1"],
        "evidence_timing": _design_only(
            "Análise de contaminantes (PAH, PCB, metais pesados) conforme IBI/EBC",
            hard_gate=True,
        ),
    },

    {
        "id": "V-MINE-0",
        "title": "Mineral additives ≤ 10% by mass",
        "module": "biochar_quality",
        "subcategory": "biochar_quality:composition",
        "requirement_text": (
            "Mineral additives (lime, rock minerals, ash) may be added to biochar up to 10% by mass. "
            "If > 10%, the final material must meet IBI/EBC contaminant testing guidelines. (AC 7)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_mineral_additives_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["AC7"],
        "evidence_timing": _design_only(
            "Fração de aditivos minerais declarada e conformidade com limite de 10%",
            hard_gate=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: monitoring — Seção 9
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-MONI-0",
        "title": "Monitoring plan — parameters and frequencies",
        "module": "monitoring",
        "subcategory": "monitoring:plan",
        "requirement_text": (
            "The PDD must include a monitoring plan covering the three stages: "
            "sourcing, production, and application. "
            "Required parameters (Section 9.2): "
            "Mp,y (total mass — continuous/monthly); "
            "Mt,k,p,y (mass by type/application — continuous/monthly); "
            "FCp,t,p (carbon content — annual or after material change); "
            "Tprod (temperature — continuous/annual average); "
            "H:Corg (per batch — for soil applications); "
            "feedstock types and quantities (continuous/monthly)."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_monitoring_plan_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9", "S9.2"],
        "evidence_timing": _design_only(
            "Tabela de parâmetros de monitoramento com frequências e QA/QC",
            hard_gate=True,
        ),
    },

    {
        "id": "V-TRCK-0",
        "title": "Chain of custody — feedstock to application tracking",
        "module": "monitoring",
        "subcategory": "monitoring:traceability",
        "requirement_text": (
            "Project must verify that biochar is applied in eligible soil or non-soil applications "
            "using tracking tools: QR code, mobile/desktop app, blockchain technology, NFT, "
            "GPS location coordinates, or any tracking software that generates chain of custody "
            "records from sourcing to end-use application. (Section 9.3)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_chain_of_custody_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.3"],
        "evidence_timing": _design_only(
            "Sistema de rastreabilidade feedstock → aplicação documentado com ferramenta específica",
            hard_gate=True,
        ),
    },

    {
        "id": "V-GEOG-0",
        "title": "Geographic information — application site coordinates",
        "module": "monitoring",
        "subcategory": "monitoring:geographic",
        "requirement_text": (
            "To prevent double counting, at least one geodetic coordinate must be provided "
            "per application site, with sufficient additional geographic information to enable "
            "sampling by the validation/verification body (VVB). "
            "Applies to both soil and non-soil applications. (Section 9.3)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_geographic_info_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.3-Geographic"],
        "evidence_timing": _design_only(
            "Coordenadas geodésicas dos locais de aplicação incluídas no PDD",
            hard_gate=True,
        ),
    },

    {
        "id": "V-DATA-0",
        "title": "Data management — offsite backup and 2-year retention",
        "module": "monitoring",
        "subcategory": "monitoring:data",
        "requirement_text": (
            "All monitoring data must be centrally stored and accessible to the VVB at any time. "
            "An offsite electronic backup of all logged data is mandatory. "
            "Documents and records must be retained for at least 2 years after the end of the "
            "project crediting period. (Section 9.3)"
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_data_management_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S9.3-DataMgmt"],
        "evidence_timing": _design_only(
            "Plano de gestão de dados com backup offsite e período de retenção ≥ 2 anos",
            hard_gate=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: permanence_risk — Reversal risk assessment (Seção 8.4)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "V-REVR-0",
        "title": "Reversal risk — negligible for soil-applied biochar",
        "module": "permanence_risk",
        "subcategory": "permanence_risk:assessment",
        "requirement_text": (
            "VM0044 Section 8.4 considers reversal risk negligible for biochar incorporated into soil, "
            "due to: biochar stability post-application; independence from annual management activities; "
            "protection against fire and erosion when subsurface incorporated. "
            "Non-soil applications (construction, water filtration) may have end-of-life reversal risk "
            "if the biochar is later incinerated — this must be addressed in the PDD. "
            "The VCS buffer pool percentage is determined by the VCS Standard non-permanence risk tool, "
            "not by VM0044 directly."
        ),
        "source_url": _VM0044_BASE,
        "logic": "eval_verra_reversal_risk_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Verra VCS"},
        "guidance_ids": ["S8.4"],
        "evidence_timing": _design_only(
            "Avaliação de risco de reversão para via de aplicação escolhida",
            hard_gate=False,
        ),
    },
]
