"""
Isometric Biochar Standard — Requirements (Protocol-native, engine v1)

IDs mapeados diretamente ao Isometric Registry (R-XXXX format).
Fonte: isometric-validation-requirements.csv exportado da plataforma Certify.
48 requisitos obrigatórios (R-) cobrindo os 31 subcategorias do PROJECT_VALIDATION.

Cada requisito tem `evidence_timing` com perfis distintos para:
  - development: projeto em fase de planejamento/PDD
  - operational: projeto em execução produzindo biochar
"""

# ---------------------------------------------------------------------------
# Helpers de evidence_timing reutilizáveis
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


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------

ISOMETRIC_BIOCHAR_V1 = [

    # ── project_data:protocol_requirements ─────────────────────────────────
    {
        "id": "R-NK7R-0",
        "title": "Protocol eligibility justification",
        "module": "project_data",
        "subcategory": "project_data:protocol_requirements",
        "requirement_text": "Projects must provide a brief explanation for why they are eligible under the selected protocol.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-NK7R-0",
        "logic": "eval_protocol_eligibility_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Justificativa de elegibilidade descrita no PDD", hard_gate=True),
    },

    # ── project_data:ownership ──────────────────────────────────────────────
    {
        "id": "R-M858-0",
        "title": "Legal ownership over removal rights",
        "module": "project_data",
        "subcategory": "project_data:ownership",
        "requirement_text": "Projects must provide reasoning and evidence for legal ownership over the rights to all removals that will be claimed.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-M858-0",
        "logic": "eval_project_ownership_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-0KA1-0", "G-M85P-0", "G-VHX0-0", "G-F6RN-0", "G-2VMA-0", "G-7X1B-0"],
        "evidence_timing": _design_only("Raciocínio e evidência de propriedade legal sobre as remoções", hard_gate=True),
    },

    # ── project_data:technical_description ─────────────────────────────────
    {
        "id": "R-7X0X-0",
        "title": "Technical description of carbon removal activity",
        "module": "project_data",
        "subcategory": "project_data:technical_description",
        "requirement_text": "Projects must provide a brief technical description of the carbon removal Project activity in accessible language, including information on facilities and equipment.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-7X0X-0",
        "logic": "eval_technical_description_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Descrição técnica do processo de remoção de carbono", hard_gate=True),
    },

    # ── project_data:project_participants ──────────────────────────────────
    {
        "id": "R-F6R7-0",
        "title": "Complete list of project participants",
        "module": "project_data",
        "subcategory": "project_data:project_participants",
        "requirement_text": "Projects must provide a complete list of organizations participating in the project including name, role, registration number, address, contact person, email and phone.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-F6R7-0",
        "logic": "eval_project_participants_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Lista completa de participantes com todos os campos obrigatórios", hard_gate=True),
    },

    # ── project_data:project_locations ─────────────────────────────────────
    {
        "id": "R-A5B6-0",
        "title": "Project address and/or geo-coordinates",
        "module": "project_data",
        "subcategory": "project_data:project_locations",
        "requirement_text": "Projects must submit at least one address and/or specific geo-coordinates for the project.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-A5B6-0",
        "logic": "eval_project_locations_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Endereço e/ou coordenadas geográficas do projeto", hard_gate=True),
    },

    # ── project_data:removal_capacity ──────────────────────────────────────
    {
        "id": "R-XT6V-0",
        "title": "Net carbon removal capacity estimate",
        "module": "project_data",
        "subcategory": "project_data:removal_capacity",
        "requirement_text": "Projects must provide an estimate of the net carbon removal capacity for the duration of the project crediting period (metric tonnes).",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-XT6V-0",
        "logic": "eval_removal_capacity_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Estimativa de capacidade de remoção líquida em tCO2 por período de crédito", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:boundaries ─────────────────────────────
    {
        "id": "R-VHWJ-0",
        "title": "Temporal and geographic project boundary defined",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:boundaries",
        "requirement_text": "Projects must define the temporal and geographic project boundary.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-VHWJ-0",
        "logic": "eval_system_boundary_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-PGFZ-0", "G-A5BM-0", "G-XT79-0"],
        "evidence_timing": _design_only("Fronteira temporal e geográfica do projeto definida", hard_gate=True),
    },
    {
        "id": "R-2VKW-0",
        "title": "System boundary with GHG sources defined",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:boundaries",
        "requirement_text": "Projects must define their system boundary and outline all GHGs considered across all sources, sinks and reservoirs (SSRs).",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-2VKW-0",
        "logic": "eval_system_boundary_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-PGFZ-0", "G-A5BM-0", "G-XT79-0"],
        "evidence_timing": _design_only("Boundary GHG com todas as fontes, sumidouros e reservatórios definidos", hard_gate=True),
    },
    {
        "id": "R-TGBM-0",
        "title": "GHG statement approach and calculation methodology",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:boundaries",
        "requirement_text": "Projects must provide a detailed description of the GHG statement approach and methodology in relation to calculations.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-TGBM-0",
        "logic": "eval_system_boundary_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-MY6J-0", "G-19AX-0", "G-8K27-0"],
        "evidence_timing": _design_only("Metodologia de cálculo do GHG statement descrita em detalhe", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:baseline ───────────────────────────────
    {
        "id": "R-PGFH-0",
        "title": "Baseline scenario reasoned and evidenced",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:baseline",
        "requirement_text": "Projects must reason and evidence the baseline scenario of their activities having not taken place. Projects will only be credited for removals above this counterfactual baseline.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-PGFH-0",
        "logic": "eval_baseline_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-53YK-0", "G-HF2Y-0"],
        "evidence_timing": _design_only("Cenário de linha de base razoado e evidenciado com suposições conservadoras", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:leakage ────────────────────────────────
    {
        "id": "R-HF2G-0",
        "title": "Leakage assessment provided",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:leakage",
        "requirement_text": "Projects must evaluate leakage by providing a robust assessment of potential increases in GHG emissions outside the system boundary as a result of the project activity.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-HF2G-0",
        "logic": "eval_leakage_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-RRT8-0"],
        "evidence_timing": _design_only("Avaliação robusta de leakage com quantificação e dedução das remoções", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:financial_additionality ────────────────
    {
        "id": "R-53Y5-0",
        "title": "Financial additionality demonstrated",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:financial_additionality",
        "requirement_text": "Projects must demonstrate financial additionality by evidencing removals are the main purpose and only source of revenue; OR demonstrating economic barriers would prevent project implementation without carbon finance.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-53Y5-0",
        "logic": "eval_financial_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-CDNX-0", "G-02HJ-0"],
        "evidence_timing": _design_only("Adicionalidade financeira demonstrada — remoções como propósito principal OU análise de IRR", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:common_practice_additionality ──────────
    {
        "id": "R-RRST-0",
        "title": "Common practice additionality demonstrated",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:common_practice_additionality",
        "requirement_text": "Projects must demonstrate that activities similar to the proposed project are not common practice.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-RRST-0",
        "logic": "eval_common_practice_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-KQD7-0", "G-7C8W-0"],
        "evidence_timing": _design_only("Análise de prática comum demonstrando que atividades similares não são pratica estabelecida", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:environmental_additionality ────────────
    {
        "id": "R-CDNF-0",
        "title": "Environmental additionality (net negative impact) demonstrated",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:environmental_additionality",
        "requirement_text": "Projects must demonstrate environmental additionality by evidencing the climate impact of the project is net negative after subtracting counterfactual CO2 removal and all project GHG emissions including leakage.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-CDNF-0",
        "logic": "eval_environmental_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Impacto climático líquido negativo demonstrado incluindo leakage", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:regulatory_additionality ───────────────
    {
        "id": "R-983D-0",
        "title": "Regulatory additionality demonstrated",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:regulatory_additionality",
        "requirement_text": "Projects must demonstrate regulatory additionality by evidencing that the project is not required by existing laws, regulations, policies, or other binding obligations.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-983D-0",
        "logic": "eval_regulatory_additionality_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-V14H-0"],
        "evidence_timing": _design_only("Evidência de que o projeto não é exigido por leis ou regulamentos existentes", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:regulatory_compliance ──────────────────
    {
        "id": "R-KQCS-0",
        "title": "Regulatory compliance method asserted",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:regulatory_compliance",
        "requirement_text": "Projects must assert the method(s) for compliance with regulations for all jurisdictions to which the project is beholden.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-KQCS-0",
        "logic": "eval_regulatory_compliance_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _both(
            "Método de conformidade regulatória descrito para todas as jurisdições",
            "Licenças e autorizações em vigor com evidências de renovação",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── protocol_and_monitoring_data:durability ─────────────────────────────
    {
        "id": "R-7C8E-0",
        "title": "Durability threshold selected from protocol",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:durability",
        "requirement_text": "Projects must select from the durability threshold(s) defined in the protocol or module to be the project durability threshold.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-7C8E-0",
        "logic": "eval_durability_selection_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Opção de durabilidade selecionada: 200 anos ou 1000 anos", hard_gate=True),
    },
    {
        "id": "R-1T2Y-0",
        "title": "Durability in excess of threshold demonstrated",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:durability",
        "requirement_text": "Projects must demonstrate a durability in excess of the designated project durability threshold.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-1T2Y-0",
        "logic": "eval_durability_selection_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-Q6GV-0"],
        "evidence_timing": _both(
            "Justificativa científica de durabilidade > threshold selecionado (H/C, O/C, análise)",
            "Laudos laboratoriais com H/Corg < 0.5 e O/Corg < 0.2 por batch",
            dev_hard=True, op_hard=True,
        ),
    },
    {
        "id": "R-F5RZ-0",
        "title": "Annual average soil temperature method provided (200-year option)",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:durability",
        "requirement_text": "If projects are targeting 200-year durability, details on the method or approach used for annual average soil temperature calculation must be provided.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-F5RZ-0",
        "logic": "eval_durability_soil_temp_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {
            "methodology.standard": "Isometric",
            "methodology.storage_pathway": "soil",
        },
        "guidance_ids": ["G-QMBJ-0", "G-YY2W-0"],
        "evidence_timing": _both(
            "Método de temperatura do solo descrito: medição direta (≥10 amostras/site-mês) ou banco de dados global (Lembrechts et al.)",
            "Dados reais de temperatura do solo do ano anterior com mínimo 10 medições/site-mês",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── protocol_and_monitoring_data:reversals ──────────────────────────────
    {
        "id": "R-V143-0",
        "title": "Reversal risk assessment completed",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:reversals",
        "requirement_text": "Projects must complete the protocol or module specific risk assessment to support the risk of reversal and buffer pool size.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-V143-0",
        "logic": "eval_reversals_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-EP06-0"],
        "evidence_timing": _design_only("Questionário de risco de reversão completado; tamanho do buffer pool determinado (2% para biochar em solo)", hard_gate=True),
    },

    # ── protocol_and_monitoring_data:uncertainty ────────────────────────────
    {
        "id": "R-2AVD-0",
        "title": "Sensitivity analysis conducted",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:uncertainty",
        "requirement_text": "Projects must conduct a sensitivity analysis that demonstrates the impact of each input parameter's uncertainty on the final net CO₂e uncertainty.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-2AVD-0",
        "logic": "eval_uncertainty_analysis_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-NZQG-0", "G-X9ET-0", "G-9MK5-0"],
        "evidence_timing": _both(
            "Análise de sensibilidade descrita com método reproduzível",
            "Análise de sensibilidade executada com dados reais de medição",
            dev_hard=True, op_hard=True,
        ),
    },
    {
        "id": "R-K6MA-0",
        "title": "Uncertainty treatment method specified",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:uncertainty",
        "requirement_text": "Projects must specify whether they used conservative estimates, variance propagation and/or Monte Carlo simulations in consideration of uncertainty.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-K6MA-0",
        "logic": "eval_uncertainty_analysis_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Método de tratamento de incerteza especificado (estimativas conservadoras / propagação de variância / Monte Carlo)", hard_gate=True),
    },
    {
        "id": "R-Z106-0",
        "title": "Uncertainty analysis detailed and justified",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:uncertainty",
        "requirement_text": "Projects must detail and justify their uncertainty analysis and any uncertainty adjustments applied in instances of high uncertainty.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-Z106-0",
        "logic": "eval_uncertainty_analysis_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-47P2-0", "G-JV4P-0", "G-1ZBS-0", "G-BHDC-0", "G-WXYR-0"],
        "evidence_timing": _both(
            "Análise de incerteza detalhada incluindo análise laboratorial de carbono e fatores de emissão",
            "Análise de incerteza com dados reais: valores mín/máx por variável, fontes citadas",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── protocol_and_monitoring_data:proxies_&_models ───────────────────────
    {
        "id": "R-NZQ2-0",
        "title": "Models described and justified",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:proxies_&_models",
        "requirement_text": "Projects must describe and justify any models used for quantification, monitoring, and meeting specified protocol requirements.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-NZQ2-0",
        "logic": "eval_proxies_models_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-K6MR-0", "G-R81S-0", "G-6VGD-0", "G-BWXE-0", "G-4K64-0", "G-ZHS3-0", "G-GYAF-0"],
        "evidence_timing": _design_only("Modelos utilizados descritos com fonte, parâmetros e validação empírica", hard_gate=False),
    },

    # ── protocol_and_monitoring_data:data_collection_and_storage ────────────
    {
        "id": "R-GYA1-0",
        "title": "Data collection and storage approach described",
        "module": "protocol_and_monitoring_data",
        "subcategory": "protocol_and_monitoring_data:data_collection_and_storage",
        "requirement_text": "Projects must describe the data collection and storage approach including how data is transmitted, collected and stored, the length of time for which records are archived, backup procedures and the person(s) responsible.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-GYA1-0",
        "logic": "eval_data_collection_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _both(
            "Procedimento de coleta, armazenamento e retenção de dados descrito (mínimo 5 anos)",
            "Sistema de retenção implementado com retenção de dados por ≥ 5 anos",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── environmental_&_social_impact:environmental_&_social_impact ─────────
    {
        "id": "R-9MJQ-0",
        "title": "Environmental regulatory compliance outlined",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:environmental_&_social_impact",
        "requirement_text": "Projects must outline and detail compliance with applicable environmental national and local laws and regulations.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-9MJQ-0",
        "logic": "eval_environmental_social_impact_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Conformidade com leis ambientais nacionais e locais detalhada", hard_gate=True),
    },
    {
        "id": "R-X9EC-0",
        "title": "Environmental and social impact assessment",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:environmental_&_social_impact",
        "requirement_text": "Projects must provide an overall assessment for the potential material environmental and social impacts, both within and beyond its boundary.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-X9EC-0",
        "logic": "eval_environmental_social_impact_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-TGC2-0", "G-E57Q-0", "G-1T3C-0"],
        "evidence_timing": _design_only("Avaliação de impactos ambientais e sociais com plano de mitigação", hard_gate=False),
    },
    {
        "id": "R-4K5P-0",
        "title": "No net environmental harm demonstrated",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:environmental_&_social_impact",
        "requirement_text": "Projects must demonstrate that it creates no net environmental harm through an environmental impact assessment including resource efficiency, pollution prevention and biodiversity conservation.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-4K5P-0",
        "logic": "eval_environmental_social_impact_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-93TP-0", "G-NEZ1-0"],
        "evidence_timing": _design_only("Demonstração de ausência de dano ambiental líquido: eficiência de recursos, biodiversidade, poluição", hard_gate=True),
    },
    {
        "id": "R-R81B-0",
        "title": "No net social harm demonstrated",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:environmental_&_social_impact",
        "requirement_text": "Projects must demonstrate that it creates no net social harm by evaluating potential negative social risks from the project's implementation.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-R81B-0",
        "logic": "eval_environmental_social_impact_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-WRPB-0", "G-QQ9A-0", "G-GDJ0-0", "G-42DN-0"],
        "evidence_timing": _design_only("Avaliação de riscos sociais: direitos trabalhistas, direitos humanos, comunidades indígenas", hard_gate=True),
    },
    {
        "id": "R-5KQC-0",
        "title": "Agricultural productivity and soil quality monitoring documented",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:environmental_&_social_impact",
        "requirement_text": "Projects must document how agricultural productivity and soil quality will be monitored, including which characteristics will be tested and the frequency of testing.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-5KQC-0",
        "logic": "eval_environmental_social_impact_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {
            "methodology.standard": "Isometric",
            "methodology.storage_pathway": "soil",
        },
        "guidance_ids": ["G-3T7G-0", "G-B3YT-0"],
        "evidence_timing": _both(
            "Plano de monitoramento de produtividade e qualidade do solo documentado com parâmetros e frequência",
            "Resultados de monitoramento de solo: pH, umidade, densidade, SOC, nutrientes",
            dev_hard=True, op_hard=False,
        ),
    },

    # ── environmental_&_social_impact:sustainable_development ───────────────
    {
        "id": "R-BWX0-0",
        "title": "Alignment with relevant SDGs demonstrated",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:sustainable_development",
        "requirement_text": "Projects must demonstrate how their carbon removal activities are consistent with relevant SDGs.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-BWX0-0",
        "logic": "eval_sustainable_development_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Alinhamento com ODS relevantes demonstrado", hard_gate=False),
    },

    # ── environmental_&_social_impact:project_closure ───────────────────────
    {
        "id": "R-6VFZ-0",
        "title": "Project closure conditions and plan described",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:project_closure",
        "requirement_text": "Projects must describe the conditions under which the project will be considered closed, and describe the project closure plan.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-6VFZ-0",
        "logic": "eval_project_closure_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [],
        "evidence_timing": _design_only("Condições de encerramento do projeto e plano de fechamento descritos", hard_gate=False),
    },

    # ── environmental_&_social_impact:adaptive_management ───────────────────
    {
        "id": "R-BC4H-0",
        "title": "Adaptive management plan: information sharing, emergency response, pause/stop conditions",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:adaptive_management",
        "requirement_text": "Projects must include a plan for information sharing, emergency response and conditions for stopping or pausing a deployment.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-BC4H-0",
        "logic": "eval_adaptive_management_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-TNMF-0"],
        "evidence_timing": _design_only(
            "Plano de gestão adaptativa com: compartilhamento de informações, resposta emergencial e condições de pausa/parada "
            "(falha de instrumentos, poluentes > threshold, não conformidade regulatória, risco à saúde)",
            hard_gate=True,
        ),
    },

    # ── environmental_&_social_impact:pollution_prevention ──────────────────
    {
        "id": "R-MY64-0",
        "title": "Pollution prevention: PAHs, heavy metals, PCBs/Dioxins",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:pollution_prevention",
        "requirement_text": "Projects must describe and provide evidence for pollution prevention against PAHs, heavy metals and any other pollutants identified.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-MY64-0",
        "logic": "eval_pollution_prevention_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-PA8A-0", "G-XKZM-0", "G-4XPY-0", "G-C7E8-0"],
        "evidence_timing": _both(
            "Avaliação de risco de PAHs e metais pesados com plano de mitigação descrito",
            "Laudos laboratoriais: PAH ≤ limites WBC; PCB ≤ 0.2 mg/kg; PCDD/F ≤ 20 ng/kg; metais pesados ≤ limites EU/EPA",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── environmental_&_social_impact:site_selection ────────────────────────
    {
        "id": "R-M760-0",
        "title": "Baseline soil samples collected prior to biochar spreading",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:site_selection",
        "requirement_text": "Projects should collect and detail baseline soil samples prior to spreading biochar, including soil pH, moisture, bulk density, soil type, nutrient availability and SOC.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-M760-0",
        "logic": "eval_site_selection_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {
            "methodology.standard": "Isometric",
            "methodology.storage_pathway": "soil",
        },
        "guidance_ids": ["G-7T3K-0", "G-0GC9-0", "G-F3TX-0"],
        "evidence_timing": _both(
            "Plano de amostragem de solo basal descrito com parâmetros (pH, umidade, densidade, SOC, nutrientes)",
            "Amostras de solo coletadas até 30cm de profundidade ou profundidade de revolvimento; resultados laboratoriais",
            dev_hard=False, op_hard=False,
        ),
    },

    # ── environmental_&_social_impact:co-benefits ───────────────────────────
    {
        "id": "R-1YC3-0",
        "title": "Co-benefits related to soil health reported (optional)",
        "module": "environmental_and_social_impact",
        "subcategory": "environmental_&_social_impact:co-benefits",
        "requirement_text": "Projects may choose to report any co-benefits related to soil health and quality that are a result of their activity.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-1YC3-0",
        "logic": "eval_co_benefits_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {
            "methodology.standard": "Isometric",
            "methodology.storage_pathway": "soil",
        },
        "guidance_ids": ["G-FSVS-0"],
        "evidence_timing": _design_only("Co-benefícios de saúde do solo documentados (opcional)", hard_gate=False),
    },

    # ── stakeholder_input_process:stakeholder_consultation ──────────────────
    {
        "id": "R-ZHRN-0",
        "title": "Stakeholder consultation documented",
        "module": "stakeholder_input_process",
        "subcategory": "stakeholder_input_process:stakeholder_consultation",
        "requirement_text": "Projects must provide a description and documentation of how comments by local stakeholders have been invited and compiled, a summary of comments received, and how due account was taken.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-ZHRN-0",
        "logic": "eval_stakeholder_consultation_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-6AQY-0", "G-BC4Z-0", "G-Z10M-0", "G-JNW9-0"],
        "evidence_timing": _design_only("Consulta a stakeholders documentada: convites, comentários recebidos e como foram considerados", hard_gate=True),
    },
    {
        "id": "R-E579-0",
        "title": "Grievance mechanism outlined",
        "module": "stakeholder_input_process",
        "subcategory": "stakeholder_input_process:stakeholder_consultation",
        "requirement_text": "Projects must outline the mechanism for stakeholders to voice, process and resolve grievances. Acknowledgement ≤ 14 days; resolution ≤ 60 days.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-E579-0",
        "logic": "eval_stakeholder_consultation_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-W7XW-0", "G-FWSH-0", "G-3HN6-0"],
        "evidence_timing": _design_only(
            "Mecanismo de reclamação descrito: contato disponível, reconhecimento ≤ 14 dias, resolução ≤ 60 dias",
            hard_gate=True,
        ),
    },

    # ── appendix:monitoring_requirements ───────────────────────────────────
    {
        "id": "R-ENZR-0",
        "title": "Monitoring parameter table provided",
        "module": "appendix",
        "subcategory": "appendix:monitoring_requirements",
        "requirement_text": "Projects must create a table that outlines all monitored parameters in their selected protocol and modules, including data source, measurement frequency, QA/QC procedures and evidence provisions.",
        "source_url": "https://registry.isometric.com/standard/1.7?requirement=standard:standard:1.7:requirement:R-ENZR-0",
        "logic": "eval_monitoring_requirements_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-2AVV-0"],
        "evidence_timing": _both(
            "Tabela de parâmetros monitorados com fonte, frequência, QA/QC e evidências planejadas",
            "Tabela atualizada com dados reais de coleta e registros de QA/QC",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── appendix:reactor_design_requirements ────────────────────────────────
    {
        "id": "R-6AQG-0",
        "title": "Engineering design diagram of pyrolysis reactor",
        "module": "appendix",
        "subcategory": "appendix:reactor_design_requirements",
        "requirement_text": "Projects must describe and provide an engineering design diagram of the chemical reactor used to achieve pyrolysis, including dimensions, inflow/outflow locations, sensor positioning, and internal equipment.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-6AQG-0",
        "logic": "eval_reactor_design_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-T4W0-0", "G-8RAM-0", "G-1EKA-0"],
        "evidence_timing": _design_only(
            "Diagrama de engenharia do reator de pirólise com: dimensões, entradas/saídas, posicionamento de sensores de T/P e equipamentos internos",
            hard_gate=True,
        ),
    },
    {
        "id": "R-SZK5-0",
        "title": "Pyrolysis gas leakage sensors described",
        "module": "appendix",
        "subcategory": "appendix:reactor_design_requirements",
        "requirement_text": "Projects must describe and evidence the sensors used to quantify any loss of pyrolysis gasses during operation of the reactor to leakage.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-SZK5-0",
        "logic": "eval_reactor_design_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-QBS8-0", "G-D8Z6-0", "G-VWDT-0", "G-G21Y-0", "G-5Z7W-0", "G-MJPG-0", "G-YNGJ-0"],
        "evidence_timing": _both(
            "Sensores de leakagem de gás pirolítico descritos: modelo de reator OU medição contínua de pressão OU teste anual de vazamento",
            "Registros de medição de pressão (±2% precisão, ≥1 min intervalo) ou relatórios de teste de vazamento (anual, ISO/ASTM)",
            dev_hard=True, op_hard=True,
        ),
    },
    {
        "id": "R-DMET-0",
        "title": "Reactor material selection justified",
        "module": "appendix",
        "subcategory": "appendix:reactor_design_requirements",
        "requirement_text": "Projects must describe the selection of materials for each component of the reactor, including suitable justification from the perspectives of thermal and mechanical resilience.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-DMET-0",
        "logic": "eval_reactor_design_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-PV0S-0", "G-Y4R3-0", "G-5EFD-0"],
        "evidence_timing": _design_only(
            "Seleção de materiais do reator justificada termicamente e mecanicamente; conformidade com 2014/68/EU ou equivalente regional se alta pressão (>0.5 Bar)",
            hard_gate=True,
        ),
    },
    {
        "id": "R-19AF-0",
        "title": "Reactor maintenance plan evidenced",
        "module": "appendix",
        "subcategory": "appendix:reactor_design_requirements",
        "requirement_text": "Projects must describe and evidence an appropriate reactor maintenance plan including monitoring and mitigation for mechanical and thermal degradation.",
        "source_url": "https://registry.isometric.com/PROTOCOL/biochar/1.1?requirement=protocol:biochar:1.1:requirement:R-19AF-0",
        "logic": "eval_reactor_design_v1",
        "type": "requirement",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-7PSP-0", "G-CR6Q-0", "G-F0H0-0"],
        "evidence_timing": _both(
            "Plano de manutenção do reator documentado: escopo, periodicidade, responsáveis e integridade estrutural",
            "Registros de manutenção executada; conformidade com 2014/68/EU ou equivalente",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── appendix:sampling_procedure ─────────────────────────────────────────
    {
        "id": "R-S8K1-1",
        "title": "Sampling procedure described and justified",
        "module": "appendix",
        "subcategory": "appendix:sampling_procedure",
        "requirement_text": "Projects must describe and justify the sampling procedure, including the number and frequency of sampling and analysis.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-S8K1-1",
        "logic": "eval_sampling_procedure_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-VZQQ-0", "G-MP0D-0", "G-DC93-0"],
        "evidence_timing": _both(
            "Plano de amostragem descrito: método A (todo batch) ou B (1 a cada 10 batches após ≥30 amostras); ≥3 amostras/batch",
            "Registros de amostragem real: datas, quantidades, resultados; amostras com ≤6 meses de idade",
            dev_hard=True, op_hard=True,
        ),
    },

    # ── appendix:biochar_characterization ───────────────────────────────────
    {
        "id": "R-CXEP-0",
        "title": "Biochar characterization standards listed",
        "module": "appendix",
        "subcategory": "appendix:biochar_characterization",
        "requirement_text": "Projects must provide a detailed bulleted list of the relevant standards utilized in the biochar characterization.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-CXEP-0",
        "logic": "eval_biochar_char_standards_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-AK6B-0", "G-39F1-0"],
        "evidence_timing": _design_only(
            "Lista de normas utilizadas na caracterização: químicas (ISO 29541, ASTM D5373) e físicas (ISO 18122, ISO 17828)",
            hard_gate=True,
        ),
    },
    {
        "id": "R-7W1N-0",
        "title": "Biochar physical properties measured",
        "module": "appendix",
        "subcategory": "appendix:biochar_characterization",
        "requirement_text": "Projects should provide the details of any measurements of biochar physical properties that have been taken.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-7W1N-0",
        "logic": "eval_biochar_physical_properties_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-XQ9H-0", "G-510V-0", "G-PDJ7-0"],
        "evidence_timing": _both(
            "Propriedades físicas do biochar descritas: porosidade, superfície específica (BET), distribuição granulométrica",
            "Laudos laboratoriais de propriedades físicas (ISO 9277, ISO 15901, ISO 565)",
            dev_hard=False, op_hard=False,
        ),
    },
    {
        "id": "R-VGXA-0",
        "title": "Biochar chemical properties measured",
        "module": "appendix",
        "subcategory": "appendix:biochar_characterization",
        "requirement_text": "Projects should provide the details of any measurements of biochar chemical properties that have been taken.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-VGXA-0",
        "logic": "eval_biochar_chemical_properties_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": [
            "G-K3Q0-0", "G-4G8C-0", "G-TDEA-0", "G-1Q5M-0", "G-X6H2-0",
            "G-GAM8-0", "G-TY6S-0", "G-KMFF-0", "G-BSZP-0", "G-27Y3-0",
            "G-CAR5-0", "G-90WY-0",
        ],
        "evidence_timing": _both(
            "Propriedades químicas descritas: H/Corg, O/Corg, Carbono total, Cinorg, Nitrogênio, Cinzas, Umidade, PAHs, metais pesados",
            "Laudos laboratoriais (ISO 17025 ou validação externa): H/Corg < 0.5; O/Corg < 0.2; PAH, PCB, PCDD/F dentro dos limites WBC",
            dev_hard=True, op_hard=True,
        ),
    },
    {
        "id": "R-2TMM-0",
        "title": "Analytical laboratory identified and qualified",
        "module": "appendix",
        "subcategory": "appendix:biochar_characterization",
        "requirement_text": "Projects must report the analytical laboratory/laboratories utilized for the biochar characterization.",
        "source_url": "https://registry.isometric.com/MODULE/biochar-storage-agricultural-soils/1.1?requirement=module:biochar-storage-agricultural-soils:1.1:requirement:R-2TMM-0",
        "logic": "eval_biochar_laboratory_v1",
        "type": "requirement",
        "mode_applicability": "operational_only",
        "applies_if": {"methodology.standard": "Isometric"},
        "guidance_ids": ["G-67T6-0", "G-DHHG-0", "G-W504-0", "G-MV8T-0"],
        "evidence_timing": _both(
            "Laboratório(s) de análise identificado(s) com qualificação ISO 17025 ou validação externa equivalente",
            "Registros de calibração e QA/QC laboratorial disponíveis para o VVB; calibrações com materiais de referência certificados",
            dev_hard=True, op_hard=True,
        ),
    },
]
