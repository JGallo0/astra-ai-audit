"""
Mapeamento Requirement ID → nome da função de lógica — Verra VCS VM0044 v1.2.
IDs no formato V-XXXX-0.

Referência: VM0044 v1.2 — "Methodology for Biochar Utilization in Soil and
Non-Soil Applications", Verra VCS Program.
"""

REQUIREMENT_LOGIC_MAP_VERRA_V1 = {

    # ── Applicability Conditions ─────────────────────────────────────────────
    "V-APPL-0": "eval_verra_applicability_v1",        # AC 1-3: escopo geral
    "V-FEED-0": "eval_verra_feedstock_eligibility_v1", # AC 4: feedstock waste + não importado
    "V-FCAT-0": "eval_verra_feedstock_category_v1",    # AC 4d: Tabela 1 — 7 categorias
    "V-TECH-0": "eval_verra_technology_class_v1",      # AC 5-8: high-tech vs low-tech
    "V-HCOR-0": "eval_verra_hcorg_gate_v1",            # AC 10: H/Corg ≤ 0.7 para solo
    "V-APPL-S": "eval_verra_application_type_v1",      # AC 11-15: solo vs não-solo; exclusões

    # ── Additionality ────────────────────────────────────────────────────────
    "V-REGS-0": "eval_verra_regulatory_surplus_v1",    # Step 1: excede regulação
    "V-PLST-0": "eval_verra_positive_list_v1",         # Step 2: positive list (ACs)
    "V-VT08-0": "eval_verra_vt0008_investment_v1",     # Step 3: VT0008 análise financeira

    # ── Baseline ─────────────────────────────────────────────────────────────
    "V-BASE-0": "eval_verra_baseline_v1",              # Seção 6: baseline = zero (conservador)
    "V-BFED-0": "eval_verra_baseline_feedstock_v1",    # Evidência do destino do feedstock

    # ── Carbon Accounting ────────────────────────────────────────────────────
    "V-PERM-0": "eval_verra_permanence_v1",            # Tabela 3: PRde,k por temperatura
    "V-TEMP-0": "eval_verra_temperature_monitoring_v1", # monitoramento contínuo Tprod
    "V-CARB-0": "eval_verra_carbon_content_v1",        # FCp,t,p — conteúdo de carbono
    "V-MASS-0": "eval_verra_mass_monitoring_v1",       # Mt,k,p,y — pesagem contínua
    "V-PEPS-0": "eval_verra_process_emissions_v1",     # PEPS,p,y — emissões do processo
    "V-LEAK-0": "eval_verra_leakage_v1",               # LEy — transporte > 200 km
    "V-APPL-E": "eval_verra_application_emissions_v1", # PEAS,y — emissões na aplicação

    # ── Product Quality ───────────────────────────────────────────────────────
    "V-QUAL-0": "eval_verra_biochar_quality_v1",       # IBI/EBC testing guidelines
    "V-CONT-0": "eval_verra_contaminants_v1",          # metais pesados, PAH per IBI/EBC
    "V-MINE-0": "eval_verra_mineral_additives_v1",     # aditivos minerais ≤ 10%

    # ── Monitoring ────────────────────────────────────────────────────────────
    "V-MONI-0": "eval_verra_monitoring_plan_v1",       # Seção 9: parâmetros e frequências
    "V-TRCK-0": "eval_verra_chain_of_custody_v1",      # rastreabilidade feedstock → aplicação
    "V-GEOG-0": "eval_verra_geographic_info_v1",       # coordenadas geodésicas de aplicação
    "V-DATA-0": "eval_verra_data_management_v1",       # armazenamento 2 anos pós-crédito

    # ── Reversal Risk ─────────────────────────────────────────────────────────
    "V-REVR-0": "eval_verra_reversal_risk_v1",         # Seção 8.4: risco negligível se biochar no solo
}
