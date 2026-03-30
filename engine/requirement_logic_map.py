REQUIREMENT_LOGIC_MAP = {

    # =========================
    # ELIGIBILITY
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
    # BIOCHAR QUALITY
    # =========================
    "BIOCHAR_001": "biochar_chemical_analysis",
    "BIOCHAR_002": "biochar_required_measurements",
    "BIOCHAR_003": "sampling_plan_consistency",
    "BIOCHAR_004": "biochar_characterization_approach",
    "BCQ_001": "product_standard_compliance",

    # =========================
    # STORAGE
    # =========================
    "STOR_001": "eval_storage_requirements",
    "STOR_002": "stockpiling_disclosure",
    "STOR_003": "deployment_method_selected",

    # =========================
    # MRV
    # =========================
    "MRV_001": "eval_monitoring_requirements",
    "MRV_002": "regulatory_measurement_methods",
    "MRV_003": "contaminant_monitoring_plan",
    "MRV_004": "uncertainty_inputs",

    # =========================
    # TRACEABILITY
    # =========================
    "TRACE_001": "chain_of_custody_diagram",
    "TRACE_002": "sampling_batch_definition",
    "TRACE_003": "biochar_incorporation_documentation",

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
    # LEAKAGE / UNCERTAINTY
    # =========================
    "LEAK_001": "eval_leakage_sources",
    "LEAK_002": "eval_leakage_treatment",
    "UNC_001": "uncertainty_inputs",
    "UNC_002": "uncertainty_inputs",

    # =========================
    # CARBON ACCOUNTING
    # =========================
    "CARB_001": "eval_carbon_accounting_structure",
    "CARB_002": "eval_emissions_accounting_method",

    # =========================
    # REVERSAL / SAFEGUARDS / REGULATORY
    # =========================
    "REV_001": "fuel_use_reversal_risk",
    "SAFE_001": "adaptive_management_plan",
    "REG_001": "environmental_legal_requirements",
}
