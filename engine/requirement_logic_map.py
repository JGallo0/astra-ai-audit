REQUIREMENT_LOGIC_MAP = {
    # =========================
    # CORE ELIGIBILITY
    # =========================
    "ELIG_001": "eval_biochar_applicability",
    "DURA_001": "durability_option_declared",

    # =========================
    # FEEDSTOCK
    # =========================
    "FEED_001": "eval_feedstock_requirements",

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
    "BIOCHAR_003": "sampling_plan_consistency",

    # =========================
    # STORAGE / END USE
    # =========================
    "STOR_001": "eval_storage_requirements",
    "STOR_003": "deployment_method_selected",

    # =========================
    # MRV / MONITORING
    # =========================
    "MRV_001": "eval_monitoring_requirements",

    # =========================
    # TRACEABILITY
    # =========================
    "TRACE_001": "chain_of_custody_diagram",

    # =========================
    # UNCERTAINTY
    # =========================
    "UNC_002": "uncertainty_inputs",

    # =========================
    # REGULATORY
    # =========================
    "REG_001": "environmental_legal_requirements",
}
