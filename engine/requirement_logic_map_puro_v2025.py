"""
Mapeamento Requirement ID → nome da função de lógica — Puro.Earth Biochar 2025.
IDs no formato P-XXXX-0.
"""

REQUIREMENT_LOGIC_MAP_PURO_V2025 = {

    # ── project_data ────────────────────────────────────────────────────────
    "P-PROT-0": "eval_puro_protocol_eligibility_v1",
    "P-OWNR-0": "eval_puro_project_ownership_v1",
    "P-TECH-0": "eval_puro_technical_description_v1",
    "P-PART-0": "eval_puro_project_participants_v1",
    "P-GEOS-0": "eval_puro_project_locations_v1",
    "P-NETC-0": "eval_puro_removal_capacity_v1",

    # ── feedstock_and_production ─────────────────────────────────────────────
    "P-FELI-0": "eval_puro_feedstock_eligibility_v1",
    "P-FFOR-0": "eval_puro_forest_sustainability_v1",
    "P-FLAN-0": "eval_puro_land_clearing_v1",
    "P-QUAL-0": "eval_puro_product_quality_v1",
    "P-NONS-0": "eval_puro_non_soil_application_v1",

    # ── carbon_accounting ────────────────────────────────────────────────────
    "P-BOUN-0": "eval_puro_system_boundary_v1",
    "P-GHGS-0": "eval_puro_ghg_statement_v1",
    "P-BASE-0": "eval_puro_baseline_v1",
    "P-LEAK-0": "eval_puro_leakage_v1",
    "P-UNCR-0": "eval_puro_uncertainty_v1",
    "P-MODL-0": "eval_puro_models_v1",

    # ── additionality ────────────────────────────────────────────────────────
    "P-FADD-0": "eval_puro_financial_additionality_v1",
    "P-CADD-0": "eval_puro_common_practice_additionality_v1",
    "P-NADD-0": "eval_puro_environmental_additionality_v1",
    "P-RADD-0": "eval_puro_regulatory_additionality_v1",

    # ── permanence ───────────────────────────────────────────────────────────
    "P-DSEL-0": "eval_puro_durability_selection_v1",
    "P-DDEM-0": "eval_puro_durability_demonstration_v1",
    "P-STMP-0": "eval_puro_soil_temp_v1",
    "P-RREV-0": "eval_puro_reversals_v1",

    # ── monitoring ───────────────────────────────────────────────────────────
    "P-DATA-0": "eval_puro_data_collection_v1",
    "P-MPRT-0": "eval_puro_monitoring_parameters_v1",
    "P-SPRP-0": "eval_puro_sampling_procedure_v1",

    # ── environmental_and_social_impact ──────────────────────────────────────
    "P-ENVC-0": "eval_puro_regulatory_compliance_v1",
    "P-EISA-0": "eval_puro_env_social_impact_v1",
    "P-NNEH-0": "eval_puro_no_net_env_harm_v1",
    "P-NNSH-0": "eval_puro_no_net_social_harm_v1",
    "P-PLUT-0": "eval_puro_pollution_prevention_v1",
    "P-ADPT-0": "eval_puro_adaptive_management_v1",
    "P-SOIL-0": "eval_puro_baseline_soil_v1",
    "P-AGPM-0": "eval_puro_soil_quality_monitoring_v1",
    "P-COBP-0": "eval_puro_co_benefits_v1",

    # ── stakeholder_input_process ────────────────────────────────────────────
    "P-STKS-0": "eval_puro_stakeholder_consultation_v1",
    "P-GRVN-0": "eval_puro_grievance_v1",

    # ── appendix ─────────────────────────────────────────────────────────────
    "P-RDES-0": "eval_puro_reactor_design_v1",
    "P-GSEN-0": "eval_puro_gas_sensors_v1",
    "P-RMAT-0": "eval_puro_reactor_material_v1",
    "P-RMNT-0": "eval_puro_maintenance_v1",
    "P-CHAR-0": "eval_puro_characterization_standards_v1",
    "P-CHEM-0": "eval_puro_biochar_chemical_v1",
    "P-PHYS-0": "eval_puro_biochar_physical_v1",
    "P-LABN-0": "eval_puro_laboratory_v1",

    # ── project_management ───────────────────────────────────────────────────
    "P-CLOS-0": "eval_puro_closure_plan_v1",
    "P-ALIGN-0": "eval_puro_sdg_alignment_v1",
}
