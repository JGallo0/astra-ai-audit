"""
Puro.Earth Biochar Methodology — Requirements (Protocol-native, engine v1)

Fonte: Puro Biochar Methodology Edition 2025 (Approved Version) +
       Clarifications Dec 2024, Oct 2024, Jul 2025.

44 requisitos organizados em 8 módulos.
IDs no formato P-XXXX-0 (P = Puro).

Diferenças-chave em relação ao Isometric:
- Feedstock: proibição explícita de resíduos mistos (fossil + biogênico)
- Sustentabilidade florestal: FSC/SFI/PEFC ou plano de manejo aprovado (CPI ≥ 50)
- PAH testing: obrigatório sem regulação local (IBI/EBC); segue regulação local se existir
- Não-solo: permanência calculada com temperatura do solo local (conservador)
- Adicionalidade financeira: first-of-its-kind NÃO isento — 3 opções obrigatórias
- Buffer pool: 2% para biochar em solo
- Prazo de emissão: 18 meses a partir do recebimento do relatório completo pelo Issuing Body
"""

# ---------------------------------------------------------------------------
# Helpers de evidence_timing (idênticos ao Isometric)
# ---------------------------------------------------------------------------

def _design(description, hard_gate=False):
    return {"type": "plan", "description": description, "is_hard_gate": hard_gate}

def _results(description, hard_gate=True):
    return {"type": "results", "description": description, "is_hard_gate": hard_gate}

def _both(dev_desc, op_desc, dev_hard=False, op_hard=True):
    return {
        "development": _design(dev_desc, dev_hard),
        "operational":  _results(op_desc, op_hard),
    }

def _design_only(description, hard_gate=True):
    return {
        "development": _design(description, hard_gate),
        "operational":  _design(description, hard_gate),
    }

_PURO_BASE = "https://puro.earth/methodology/biochar-2025"


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------

PURO_BIOCHAR_V2025 = [

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: project_data
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-PROT-0",
        "title": "Protocol eligibility justification",
        "module": "project_data",
        "subcategory": "project_data:protocol_requirements",
        "requirement_text": (
            "Projects must provide a brief explanation for why they are eligible under the "
            "Puro.Earth Biochar Methodology (Edition 2025), including feedstock type, "
            "pyrolysis process, and storage pathway."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_protocol_eligibility_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Justificativa de elegibilidade no PDD — tipo de feedstock, processo e via de armazenamento",
            hard_gate=True,
        ),
    },

    {
        "id": "P-OWNR-0",
        "title": "Legal ownership over removal rights",
        "module": "project_data",
        "subcategory": "project_data:ownership",
        "requirement_text": (
            "Projects must provide reasoning and evidence for legal ownership over the rights "
            "to all removals that will be claimed under Puro.Earth."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_project_ownership_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Raciocínio e evidência de propriedade legal sobre os créditos de carbono",
            hard_gate=True,
        ),
    },

    {
        "id": "P-TECH-0",
        "title": "Technical description of carbon removal activity",
        "module": "project_data",
        "subcategory": "project_data:technical_description",
        "requirement_text": (
            "Projects must provide a technical description of the biochar production process, "
            "including facilities, equipment (reactor type, capacity), feedstock origin, "
            "and intended storage/application pathway."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_technical_description_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Descrição técnica completa do processo de produção de biochar e equipamentos",
            hard_gate=True,
        ),
    },

    {
        "id": "P-PART-0",
        "title": "Complete list of project participants",
        "module": "project_data",
        "subcategory": "project_data:project_participants",
        "requirement_text": (
            "Projects must provide a complete list of organizations participating in the project "
            "including name, role, registration number, address, contact person, email and phone."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_project_participants_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Lista completa de participantes com todos os campos obrigatórios",
            hard_gate=True,
        ),
    },

    {
        "id": "P-GEOS-0",
        "title": "Project address and geo-coordinates",
        "module": "project_data",
        "subcategory": "project_data:project_location",
        "requirement_text": (
            "Projects must provide the address and/or GPS coordinates of the production facility "
            "and of the biochar application/storage site(s)."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_project_locations_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Endereço e coordenadas GPS da facility e do(s) local(is) de aplicação",
            hard_gate=True,
        ),
    },

    {
        "id": "P-NETC-0",
        "title": "Net carbon removal capacity estimate",
        "module": "project_data",
        "subcategory": "project_data:removal_capacity",
        "requirement_text": (
            "Projects must provide an estimate of the net carbon removal capacity per year, "
            "including all GHG emissions from the production process (scope 1, 2 and 3) "
            "and any counterfactual baseline emissions."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_removal_capacity_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Estimativa de capacidade líquida de remoção de carbono por ano",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: feedstock_and_production
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-FELI-0",
        "title": "Feedstock eligibility — sustainable biomass, no mixed waste",
        "module": "feedstock_and_production",
        "subcategory": "feedstock_and_production:feedstock_eligibility",
        "requirement_text": (
            "Biochar must be produced exclusively from sustainable biomass. Mixed waste containing "
            "both fossil and biogenic carbon (e.g., plastics + biomass) is NOT eligible. "
            "Eligible feedstocks include agricultural waste, biodegradable waste, urban wood waste, "
            "and food waste. (Clarification 001 BCH)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_feedstock_eligibility_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": ["clarification_001_BCH"],
        "evidence_timing": _design_only(
            "Documentação de origem do feedstock confirmando 100% biomassa — sem resíduo misto",
            hard_gate=True,
        ),
    },

    {
        "id": "P-FFOR-0",
        "title": "Forest biomass sustainability certification",
        "module": "feedstock_and_production",
        "subcategory": "feedstock_and_production:forest_sustainability",
        "requirement_text": (
            "If feedstock includes forest biomass, sustainability must be demonstrated via: "
            "(a) FSC Forest Management Certification, OR (b) SFI Certification, OR "
            "(c) PEFC Standard, OR (d) Government-approved forest management plan "
            "(for countries with CPI ≥ 50 — must document local authority, sustainability "
            "requirements and oversight type). (Clarification 006 BCH)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_forest_sustainability_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "feedstock.includes_forest_biomass": True,
        },
        "guidance_ids": ["clarification_006_BCH"],
        "evidence_timing": _design_only(
            "Certificado FSC/SFI/PEFC ou plano de manejo florestal aprovado por autoridade governamental (CPI ≥ 50)",
            hard_gate=True,
        ),
    },

    {
        "id": "P-FLAN-0",
        "title": "Agricultural land clearing feedstock eligibility",
        "module": "feedstock_and_production",
        "subcategory": "feedstock_and_production:land_clearing",
        "requirement_text": (
            "Biomass from land clearing is eligible ONLY if: (i) land clearing would occur "
            "regardless of the project (counterfactual), (ii) valid permit/approval exists, "
            "(iii) only economically non-usable fractions are used, and (iv) land is not in "
            "protected areas, high-value ecosystems, or primary/old-growth forests. "
            "(Rule 4.1.6(e), Clarification 004 TSB)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_land_clearing_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "feedstock.from_land_clearing": True,
        },
        "guidance_ids": ["clarification_004_TSB"],
        "evidence_timing": _design_only(
            "Permissão de desmatamento + confirmação de não-elegibilidade da fração econômica + confirmação de área não protegida",
            hard_gate=True,
        ),
    },

    {
        "id": "P-QUAL-0",
        "title": "Biochar product quality — PAH and contaminant limits",
        "module": "feedstock_and_production",
        "subcategory": "feedstock_and_production:product_quality",
        "requirement_text": (
            "Biochar must meet applicable quality requirements: (1) Follow local regulation if "
            "it exists — it prevails over all other standards. (2) If no local regulation: "
            "meet IBI or EBC quality thresholds for PAHs, heavy metals. (3) If PAH levels "
            "exceed IBI/EBC limits: acceptable only if customers explicitly informed and "
            "acknowledged. PAH testing is mandatory for soil amendments or animal feed in "
            "jurisdictions without regulations. (Clarifications 002 & 003 BCH)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_product_quality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": ["clarification_002_BCH", "clarification_003_BCH"],
        "evidence_timing": _both(
            dev_desc="Padrão de qualidade selecionado (regulação local ou IBI/EBC); plano de análise PAH",
            op_desc="Laudos laboratoriais (ISO 17025) com PAH, metais pesados dentro dos limites — por batch",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-NONS-0",
        "title": "Non-soil applications — end-of-life documentation",
        "module": "feedstock_and_production",
        "subcategory": "feedstock_and_production:application_pathway",
        "requirement_text": (
            "For biochar applied to non-soil pathways (built environment, construction materials), "
            "end-of-life treatment must be documented. Biochar must NOT end up in waste "
            "incineration. Permanence is calculated using local average soil temperature "
            "as conservative estimate until specific research is available. "
            "(Clarification 008 BCH)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_non_soil_application_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "storage.pathway": "built_environment",
        },
        "guidance_ids": ["clarification_008_BCH"],
        "evidence_timing": _both(
            dev_desc="Plano de uso final documentado — biochar não irá para incineração; temperatura do solo local para permanência",
            op_desc="Contratos com clientes confirmando via de aplicação; confirmação de não incineração",
            dev_hard=True, op_hard=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: carbon_accounting
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-BOUN-0",
        "title": "System boundary — temporal, geographic and GHG sources",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:system_boundary",
        "requirement_text": (
            "Projects must define the temporal, geographic, and GHG source boundaries, "
            "including all sources, sinks, and reservoirs (SSRs). All included and excluded "
            "GHG sources must be listed with justification."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_system_boundary_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Diagrama de fronteiras temporais, geográficas e fontes de GHG com justificativas de inclusão/exclusão",
            hard_gate=True,
        ),
    },

    {
        "id": "P-GHGS-0",
        "title": "GHG statement approach and calculation methodology",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:ghg_accounting",
        "requirement_text": (
            "Projects must describe the approach and calculation methodology for the GHG statement, "
            "including all emission factors, conversion parameters, and the LCA boundary."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_ghg_statement_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Abordagem e metodologia de cálculo do balanço de GHG incluindo todos os fatores de emissão e fronteiras LCA",
            hard_gate=True,
        ),
    },

    {
        "id": "P-BASE-0",
        "title": "Baseline scenario reasoned and evidenced",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:baseline",
        "requirement_text": (
            "Projects must define and evidence the baseline scenario (counterfactual) — the most "
            "likely activity that would have occurred without the project. Baseline parameters "
            "must be conservative, with sources documented."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_baseline_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Cenário de referência (counterfactual) fundamentado e evidenciado com parâmetros conservadores",
            hard_gate=True,
        ),
    },

    {
        "id": "P-LEAK-0",
        "title": "Leakage assessment",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:leakage",
        "requirement_text": (
            "Projects must provide a robust assessment and quantification of potential GHG "
            "increases outside the project boundary due to the project activity. Leakage must "
            "be deducted from claimed removals."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_leakage_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Quantificação de vazamentos fora da fronteira do projeto; dedução das remoções reivindicadas",
            hard_gate=True,
        ),
    },

    {
        "id": "P-UNCR-0",
        "title": "Uncertainty analysis and sensitivity analysis",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:uncertainty",
        "requirement_text": (
            "Projects must conduct a sensitivity analysis demonstrating the impact of each "
            "parameter's uncertainty on the final net CO₂e. Methods include conservative estimates, "
            "variance propagation, and/or Monte Carlo simulations. "
            "Development: method described (reproducible). "
            "Operational: executed with real measurement data, min/max values per variable."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_uncertainty_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Método de análise de incerteza descrito (propagação de variância, Monte Carlo ou estimativas conservadoras)",
            op_desc="Análise de sensibilidade executada com dados reais; valores min/max por variável com fontes",
            dev_hard=False, op_hard=True,
        ),
    },

    {
        "id": "P-MODL-0",
        "title": "Models and proxies described and justified",
        "module": "carbon_accounting",
        "subcategory": "carbon_accounting:models",
        "requirement_text": (
            "Any models or proxies used in the GHG calculation must be described and justified, "
            "including their source, key parameters, and empirical validation data."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_models_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Modelos utilizados documentados com fonte, parâmetros-chave e validação empírica",
            hard_gate=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: additionality
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-FADD-0",
        "title": "Financial additionality demonstrated",
        "module": "additionality",
        "subcategory": "additionality:financial",
        "requirement_text": (
            "Financial additionality must be demonstrated using one of three options: "
            "(a) Simple cost analysis, (b) Investment analysis (IRR/NPV), or "
            "(c) Barrier analysis. Note: first-of-its-kind facilities are NOT exempt — "
            "must apply one of the three methods. (Clarification 005 ADD)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_financial_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": ["clarification_005_ADD"],
        "evidence_timing": _design_only(
            "Análise de adicionalidade financeira via: (a) análise de custo, (b) IRR/VPL, ou (c) análise de barreiras",
            hard_gate=True,
        ),
    },

    {
        "id": "P-CADD-0",
        "title": "Common practice additionality demonstrated",
        "module": "additionality",
        "subcategory": "additionality:common_practice",
        "requirement_text": (
            "Projects must demonstrate that activities similar to the proposed project are not "
            "common practice in the sector/region, through market analysis or literature review."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_common_practice_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Análise de mercado ou revisão de literatura demonstrando que atividades similares não são prática comum",
            hard_gate=True,
        ),
    },

    {
        "id": "P-NADD-0",
        "title": "Net negative environmental impact (additionality)",
        "module": "additionality",
        "subcategory": "additionality:environmental",
        "requirement_text": (
            "Climate impact must be net negative after subtracting the counterfactual CO₂ removal "
            "AND all project GHG emissions including leakage. Full LCA boundary required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_environmental_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Modelo de cálculo de GHG confirmando impacto líquido negativo; quantificação de leakage",
            hard_gate=True,
        ),
    },

    {
        "id": "P-RADD-0",
        "title": "Regulatory additionality demonstrated",
        "module": "additionality",
        "subcategory": "additionality:regulatory",
        "requirement_text": (
            "Projects must demonstrate they are not required by existing laws, regulations, "
            "policies, or binding obligations. A legal analysis confirming voluntary nature is required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_regulatory_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Análise jurídica confirmando que o projeto não é exigido por lei ou regulação",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: permanence
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-DSEL-0",
        "title": "Durability threshold selected from protocol",
        "module": "permanence",
        "subcategory": "permanence:durability_selection",
        "requirement_text": (
            "Projects must select and justify the applicable durability threshold from "
            "Puro protocol options: 200 years OR 1000 years. Selection must be based on "
            "quantification per Woolf et al. (2021) methodology."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_durability_selection_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Limiar de durabilidade selecionado (200 ou 1000 anos) com justificativa via Woolf et al. (2021)",
            hard_gate=True,
        ),
    },

    {
        "id": "P-DDEM-0",
        "title": "Durability in excess of threshold demonstrated",
        "module": "permanence",
        "subcategory": "permanence:durability_demonstration",
        "requirement_text": (
            "Projects must demonstrate that biochar durability exceeds the selected threshold. "
            "Requires H/Corg < 0.5 and O/Corg < 0.2 as measured per ISO 17025 certified lab. "
            "Development: scientific justification. Operational: lab reports per batch."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_durability_demonstration_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Justificativa científica de durabilidade; especificação de H/Corg < 0,5 e O/Corg < 0,2",
            op_desc="Laudos laboratoriais por batch confirmando H/Corg < 0,5 e O/Corg < 0,2 (ISO 17025)",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-STMP-0",
        "title": "Annual average soil temperature method (200-year option)",
        "module": "permanence",
        "subcategory": "permanence:soil_temperature",
        "requirement_text": (
            "If the 200-year durability option is selected, projects must specify the method "
            "for determining mean annual soil temperature (MAST) at the application site. "
            "Options: (a) Direct measurement ≥ 10 samples/site/month, OR "
            "(b) Global database (Lembrechts et al. or equivalent). "
            "For non-soil applications: use local average soil temperature (conservative)."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_soil_temp_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "methodology.durability_option": "200_years",
        },
        "guidance_ids": ["clarification_008_BCH"],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Método de medição de temperatura do solo descrito (medição direta ≥10 amostras/mês ou banco de dados global)",
            op_desc="Dados reais de temperatura do solo com mínimo de 10 medições/site/mês do ano anterior",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-RREV-0",
        "title": "Reversal risk assessment and buffer pool",
        "module": "permanence",
        "subcategory": "permanence:reversal_risk",
        "requirement_text": (
            "Projects must complete the Puro protocol reversal risk questionnaire and determine "
            "the buffer pool contribution. Standard buffer pool for biochar in soil: 2%."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_reversals_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Questionário de risco de reversão preenchido; buffer pool calculado (padrão: 2% para biochar em solo)",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: monitoring
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-DATA-0",
        "title": "Data collection and storage approach described",
        "module": "monitoring",
        "subcategory": "monitoring:data_management",
        "requirement_text": (
            "Projects must describe their approach to data transmission, collection, storage, "
            "retention (minimum 5 years), backup, and responsibility. "
            "Development: SOP written. Operational: system implemented."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_data_collection_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Procedimento operacional padrão (SOP) de gestão de dados com retenção ≥ 5 anos",
            op_desc="Sistema de armazenamento implementado com evidência de ≥ 5 anos de retenção",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-MPRT-0",
        "title": "Monitoring parameter table provided",
        "module": "monitoring",
        "subcategory": "monitoring:parameters",
        "requirement_text": (
            "Projects must provide a complete table of all monitored parameters, including: "
            "data source, measurement frequency, QA/QC procedures, and evidence provisions. "
            "Development: planned table. Operational: actual data collected."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_monitoring_parameters_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Tabela de parâmetros monitorados com frequência planejada e procedimentos de QA/QC",
            op_desc="Tabela atualizada com dados reais; registros de QA/QC com materiais de referência certificados",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-SPRP-0",
        "title": "Sampling procedure described and justified",
        "module": "monitoring",
        "subcategory": "monitoring:sampling",
        "requirement_text": (
            "Projects must describe and justify their sampling procedure. Options: "
            "Method A (every batch) or Method B (1 per 10 batches, after ≥30 baseline samples). "
            "Minimum: ≥3 samples per batch. Sample age at analysis: ≤6 months. "
            "Development: plan. Operational: actual records."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_sampling_procedure_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Plano de amostragem com método escolhido (A ou B), justificativa e frequência",
            op_desc="Registros de amostragem com datas, quantidades, resultados e cadeia de custódia (amostras ≤ 6 meses)",
            dev_hard=True, op_hard=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: environmental_and_social_impact
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-ENVC-0",
        "title": "Environmental regulatory compliance outlined",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:compliance",
        "requirement_text": (
            "Projects must outline compliance with all applicable environmental national and "
            "local laws and regulations, including obtaining and maintaining required licenses "
            "and authorizations. (Rule R-KQCS-0 equivalent)"
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_regulatory_compliance_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Lista de regulações aplicáveis e método de conformidade descrito",
            op_desc="Licenças e autorizações vigentes com evidências de renovação",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-EISA-0",
        "title": "Environmental and social impact assessment",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:impact_assessment",
        "requirement_text": (
            "Projects must provide an overall assessment of potential material environmental "
            "and social impacts within and beyond the project boundary."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_env_social_impact_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Avaliação de impactos ambientais e sociais materiais dentro e além da fronteira do projeto",
            hard_gate=False,
        ),
    },

    {
        "id": "P-NNEH-0",
        "title": "No net environmental harm demonstrated",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:environmental_harm",
        "requirement_text": (
            "Projects must demonstrate no net environmental harm including resource efficiency, "
            "pollution prevention, and biodiversity conservation."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_no_net_env_harm_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Avaliação de impacto ambiental com foco em eficiência de recursos, poluição e biodiversidade",
            hard_gate=True,
        ),
    },

    {
        "id": "P-NNSH-0",
        "title": "No net social harm demonstrated",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:social_harm",
        "requirement_text": (
            "Projects must evaluate potential negative social risks including labour rights, "
            "human rights, and indigenous community impacts, with mitigation measures identified."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_no_net_social_harm_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Avaliação de riscos sociais (trabalho, direitos humanos, comunidades indígenas) com medidas de mitigação",
            hard_gate=True,
        ),
    },

    {
        "id": "P-PLUT-0",
        "title": "Pollution prevention — PAHs, heavy metals, PCBs, dioxins",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:pollution",
        "requirement_text": (
            "Projects must describe and evidence pollution prevention measures against: "
            "PAHs (≤ WBC limits), PCBs (≤ 0.2 mg/kg), PCDD/F (≤ 20 ng/kg), "
            "heavy metals (≤ EU/EPA limits). "
            "Development: risk assessment and mitigation plan. "
            "Operational: ISO 17025 lab reports per batch."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_pollution_prevention_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Avaliação de risco PAH/metais pesados/PCB/dioxinas; plano de mitigação documentado",
            op_desc="Laudos ISO 17025 por batch: PAH ≤ WBC, PCB ≤ 0,2 mg/kg, PCDD/F ≤ 20 ng/kg, metais ≤ EU/EPA",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-ADPT-0",
        "title": "Adaptive management plan",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:adaptive_management",
        "requirement_text": (
            "Projects must provide a plan covering information sharing, emergency response, "
            "and conditions for pause/stop. Mandatory stop/pause triggers include: "
            "instrument failure, pollutants exceeding thresholds, non-compliance with regulation, "
            "health/safety risk."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_adaptive_management_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Plano de gestão adaptativa com 4 gatilhos obrigatórios de pausa/parada",
            hard_gate=True,
        ),
    },

    {
        "id": "P-SOIL-0",
        "title": "Baseline soil samples collected prior to biochar spreading",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:soil_baseline",
        "requirement_text": (
            "For soil application pathway: baseline soil samples must be collected prior to "
            "biochar application (pH, moisture, density, soil type, nutrients, SOC) to depth "
            "of 30 cm or plow depth."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_baseline_soil_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "storage.pathway": "soil",
        },
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Plano de coleta de amostras de solo baseline (parâmetros, profundidade, frequência)",
            op_desc="Resultados laboratoriais das amostras de solo baseline pré-aplicação",
            dev_hard=False, op_hard=False,
        ),
    },

    {
        "id": "P-AGPM-0",
        "title": "Agricultural productivity and soil quality monitoring",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:soil_monitoring",
        "requirement_text": (
            "For soil application pathway: projects must document monitoring approach for "
            "agricultural productivity and soil quality (pH, moisture, density, SOC, nutrients). "
            "Development: plan. Operational: actual results."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_soil_quality_monitoring_v1",
        "type": "requirement",
        "applies_if": {
            "methodology.standard": "Puro.Earth",
            "storage.pathway": "soil",
        },
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Plano de monitoramento de produtividade agrícola e qualidade do solo",
            op_desc="Resultados reais de monitoramento do solo (pH, SOC, nutrientes)",
            dev_hard=True, op_hard=False,
        ),
    },

    {
        "id": "P-COBP-0",
        "title": "Co-benefits related to soil health reported (optional)",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_and_social_impact:co_benefits",
        "requirement_text": (
            "Optional: Projects may report co-benefits related to soil health improvement, "
            "biodiversity, or other SDG-related outcomes when biochar is applied to soil."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_co_benefits_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Documentação opcional de co-benefícios esperados (SDGs, saúde do solo)",
            op_desc="Resultados de co-benefícios observados documentados",
            dev_hard=False, op_hard=False,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: stakeholder_input_process
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-STKS-0",
        "title": "Stakeholder consultation documented",
        "module": "stakeholder_input_process",
        "subcategory": "stakeholder_input_process:consultation",
        "requirement_text": (
            "Projects must document how comments from local stakeholders were invited and "
            "compiled, a summary of comments received, and how due account was taken of "
            "those comments in the project design."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_stakeholder_consultation_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Registros de consulta pública; lista de stakeholders; resumo de comentários e respostas",
            hard_gate=True,
        ),
    },

    {
        "id": "P-GRVN-0",
        "title": "Grievance mechanism outlined",
        "module": "stakeholder_input_process",
        "subcategory": "stakeholder_input_process:grievance",
        "requirement_text": (
            "Projects must outline a mechanism for stakeholders to voice, process, and resolve "
            "grievances. Required timelines: acknowledgement ≤ 14 days, resolution ≤ 60 days."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_grievance_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Procedimento de reclamações documentado com prazos: reconhecimento ≤ 14 dias, resolução ≤ 60 dias",
            hard_gate=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: appendix (reactor, characterization, lab)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-RDES-0",
        "title": "Engineering design diagram of pyrolysis reactor",
        "module": "appendix",
        "subcategory": "appendix:reactor_design",
        "requirement_text": (
            "Projects must provide an engineering diagram of the pyrolysis reactor including "
            "dimensions, inflow/outflow streams, sensor positioning, and internal equipment."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_reactor_design_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Diagrama de engenharia do reator com dimensões, fluxos, posicionamento de sensores e equipamentos internos",
            hard_gate=True,
        ),
    },

    {
        "id": "P-GSEN-0",
        "title": "Pyrolysis gas leakage sensors described",
        "module": "appendix",
        "subcategory": "appendix:gas_sensors",
        "requirement_text": (
            "Projects must describe and evidence sensors to quantify pyrolysis gas leakage. Options: "
            "(a) Reactor specification model, OR "
            "(b) Continuous pressure measurement (±2%, ≥1 min interval), OR "
            "(c) Annual leak test (ISO/ASTM standard). "
            "Operational: logs or annual test reports required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_gas_sensors_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Método de detecção de vazamento descrito (especificação do reator, pressão contínua, ou teste anual)",
            op_desc="Registros de medição de pressão ou relatório de teste anual de vazamento (ISO/ASTM)",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-RMAT-0",
        "title": "Reactor material selection justified",
        "module": "appendix",
        "subcategory": "appendix:reactor_materials",
        "requirement_text": (
            "Materials used in the reactor must be selected with justification for thermal and "
            "mechanical resilience. If operating at high pressure (> 0.5 Bar), must comply with "
            "Directive 2014/68/EU or equivalent regional standard."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_reactor_material_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Especificações de materiais com justificativa de resiliência térmica e mecânica; conformidade 2014/68/EU se pressão > 0,5 Bar",
            hard_gate=True,
        ),
    },

    {
        "id": "P-RMNT-0",
        "title": "Reactor maintenance plan evidenced",
        "module": "appendix",
        "subcategory": "appendix:maintenance",
        "requirement_text": (
            "Projects must document a maintenance plan including monitoring and mitigation for "
            "mechanical/thermal degradation, with scope, frequency, and responsible parties. "
            "Operational: maintenance records required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_maintenance_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _both(
            dev_desc="Plano de manutenção documentado com escopo, frequência e responsáveis",
            op_desc="Registros de manutenção executada e integridade estrutural do reator",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-CHAR-0",
        "title": "Biochar characterization standards listed",
        "module": "appendix",
        "subcategory": "appendix:characterization_standards",
        "requirement_text": (
            "Projects must provide a detailed list of relevant standards used for biochar "
            "characterization. Common standards include ISO 29541, ASTM D5373 (chemical), "
            "ISO 18122, ISO 17828 (physical)."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_characterization_standards_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _design_only(
            "Lista de padrões de caracterização do biochar com referências (ISO, ASTM ou equivalentes)",
            hard_gate=True,
        ),
    },

    {
        "id": "P-CHEM-0",
        "title": "Biochar chemical properties measured",
        "module": "appendix",
        "subcategory": "appendix:chemical_properties",
        "requirement_text": (
            "Projects must document measurements of chemical properties: H/Corg (< 0.5), "
            "O/Corg (< 0.2), Total Carbon, Inorganic Carbon, Nitrogen, Ash, Moisture, "
            "PAHs, heavy metals. ISO 17025 certified laboratory required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_biochar_chemical_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Descrição do plano de análise química com parâmetros e laboratório ISO 17025 identificado",
            op_desc="Laudos laboratoriais (ISO 17025): H/Corg < 0,5 e O/Corg < 0,2 por batch — hard gate",
            dev_hard=True, op_hard=True,
        ),
    },

    {
        "id": "P-PHYS-0",
        "title": "Biochar physical properties measured",
        "module": "appendix",
        "subcategory": "appendix:physical_properties",
        "requirement_text": (
            "Projects must document measurements of physical properties: porosity, "
            "specific surface area (BET via ISO 9277), particle size distribution (ISO 565). "
            "Laboratory results per batch required in operational phase."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_biochar_physical_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Descrição das propriedades físicas a medir (porosidade, BET, granulometria)",
            op_desc="Laudos laboratoriais com porosidade, superfície BET (ISO 9277), granulometria (ISO 565)",
            dev_hard=False, op_hard=False,
        ),
    },

    {
        "id": "P-LABN-0",
        "title": "Analytical laboratory identified and qualified",
        "module": "appendix",
        "subcategory": "appendix:laboratory",
        "requirement_text": (
            "The analytical laboratory must be identified and qualified via ISO 17025 "
            "certification or equivalent external validation. "
            "Operational: calibration and QA/QC records with certified reference materials required."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_laboratory_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "mode_applicability": "operational_only",
        "evidence_timing": _both(
            dev_desc="Laboratório identificado com certificado ISO 17025 em vigor",
            op_desc="Registros de calibração e QA/QC com materiais de referência certificados",
            dev_hard=True, op_hard=True,
        ),
    },

    # ══════════════════════════════════════════════════════════════════════
    # MODULE: project_management (opcional)
    # ══════════════════════════════════════════════════════════════════════

    {
        "id": "P-CLOS-0",
        "title": "Project closure plan described",
        "module": "project_management",
        "subcategory": "project_management:closure",
        "requirement_text": (
            "Projects must describe the conditions for project closure and provide "
            "a closure plan including post-closure management."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_closure_plan_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Condições de encerramento e plano de pós-encerramento documentados",
            hard_gate=False,
        ),
    },

    {
        "id": "P-ALIGN-0",
        "title": "SDG alignment demonstrated",
        "module": "project_management",
        "subcategory": "project_management:sdg",
        "requirement_text": (
            "Projects must demonstrate alignment with relevant Sustainable Development Goals (SDGs). "
            "Puro requires SDG reporting as part of the project documentation."
        ),
        "source_url": _PURO_BASE,
        "logic": "eval_puro_sdg_alignment_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Puro.Earth"},
        "guidance_ids": [],
        "evidence_timing": _design_only(
            "Alinhamento com ODS relevantes documentado no PDD ou relatório SDG",
            hard_gate=False,
        ),
    },

]
