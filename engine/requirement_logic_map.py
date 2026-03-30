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
    "FEED_004": "feedstock_moisture_management",

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
    "MRV_004": "contaminant_monitoring_plan",

    # =========================
    # TRACEABILITY
    # =========================
    "TRACE_001": "chain_of_custody_diagram",

    # =========================
    # UNCERTAINTY
    # =========================
    "UNC_002": "uncertainty_inputs",

    # =========================
    # REVERSAL / SAFEGUARDS
    # =========================
    "REV_001": "fuel_use_reversal_risk",
    "SAFE_001": "adaptive_management_plan",

    # =========================
    # REGULATORY
    # =========================
    "REG_001": "environmental_legal_requirements",
    "MRV_002": "regulatory_measurement_methods",

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
