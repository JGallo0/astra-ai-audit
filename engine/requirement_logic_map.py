REQUIREMENT_LOGIC_MAP = {
    # =========================
    # CORE ELIGIBILITY
    # =========================
    "ELIG_001": "eval_biochar_applicability",
    "ELIG_002": "eval_project_ownership",
    "ELIG_003": "eval_project_crediting_context",
    "DURA_001": "durability_option_declared",

    # =========================
    # FEEDSTOCK
    # =========================
    "FEED_001": "eval_feedstock_requirements",
    "FEED_002": "eval_feedstock_origin",
    "FEED_003": "eval_feedstock_counterfactual",
    "FEED_004": "feedstock_moisture_management",
    "FEED_005": "eval_feedstock_traceability",

    # =========================
    # TECHNOLOGY / PRODUCTION
    # =========================
    "TECH_001": "eval_reactor_requirements",
    "TECH_002": "reactor_maintenance_plan",
    "TECH_003": "stack_emissions_monitoring_method",
    "TECH_004": "crediting_activity_boundaries",

    # =========================
    # BIOCHAR
    # =========================
    "BIOCHAR_001": "biochar_chemical_analysis",
    "BIOCHAR_002": "biochar_required_measurements",
    "BIOCHAR_003": "sampling_plan_consistency",
    "BIOCHAR_004": "biochar_characterization_approach",
    "BCQ_001": "product_standard_compliance",

    # =========================
    # STORAGE / END USE
    # =========================
    "STOR_001": "eval_storage_requirements",
    "STOR_002": "stockpiling_disclosure",
    "STOR_003": "deployment_method_selected",

    # =========================
    # MRV / MONITORING
    # =========================
    "MRV_001": "eval_monitoring_requirements",
    "MRV_002": "regulatory_measurement_methods",
    "MRV_004": "contaminant_monitoring_plan",

    # =========================
    # TRACEABILITY
    # =========================
    "TRACE_001": "chain_of_custody_diagram",

    # =========================
    # OWNERSHIP / ADDITIONALITY / BASELINE
    # =========================
    "OWN_001": "eval_project_ownership",
    "ADD_001": "eval_additionality_core",
    "ADD_002": "eval_additionality_barriers",
    "BASE_001": "eval_baseline_core",
    "BASE_002": "eval_baseline_evidence",
    "BOUND_001": "eval_system_boundary",

    # =========================
    # LEAKAGE / UNCERTAINTY / CARBON ACCOUNTING
    # =========================
    "LEAK_001": "eval_leakage_sources",
    "LEAK_002": "eval_leakage_treatment",
    "UNC_002": "uncertainty_inputs",
    "CARB_001": "eval_carbon_accounting_structure",
    "CARB_002": "eval_emissions_accounting_method",

    # =========================
    # REVERSAL / SAFEGUARDS / REGULATORY
    # =========================
    "REV_001": "fuel_use_reversal_risk",
    "SAFE_001": "adaptive_management_plan",
    "REG_001": "environmental_legal_requirements",

    # =========================
    # OPTIONAL / ADVANCED TECH
    # =========================
    "TECH_DIAG_001": "reactor_design_diagram",
    "TECH_DIAG_002": "engineering_design_diagram",
    "TECH_MAT_001": "reactor_material_selection",
    "TECH_END_001": "end_material_process_description",
    "STOR_SOIL_001": "direct_soil_application_evidence",
    "STOR_BOUND_001": "storage_system_boundary",
}
