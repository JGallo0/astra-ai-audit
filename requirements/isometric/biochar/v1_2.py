# requirements/isometric/biochar/v1_2.py

from copy import deepcopy

# =========================================================
# PACKAGE METADATA
# =========================================================

PACKAGE_META = {
    "standard": "Isometric Standard",
    "standard_version": "1.5.1",
    "pathway": "Biochar",
    "protocol": "Biochar Production and Storage Protocol",
    "protocol_version": "1.2",
    "combined_registry_page": "Requirements for Biochar",
    "modules_available": [
        "Isometric Standard v1.5.1",
        "Biochar Production and Storage Protocol v1.2",
        "Biochar Production in Combustion Co-product Systems Module v1.0",
        "Biochar Production in Distributed and Small Scale Projects Module v1.0",
        "Biochar Storage in the Built Environment Module v1.0",
        "Biochar Storage in Soil Environments Module v1.2",
    ],
}

# =========================================================
# APPLICABILITY HELPERS
# =========================================================
# Convention:
# - applies_if is a declarative dict, not executable logic
# - the engine should decide whether a requirement is applicable
# - if no applies_if is provided, default applicability is:
#   methodology.standard == "Isometric"
#   methodology.pathway == "biochar"

DEFAULT_APPLIES_IF = {
    "methodology.standard": "Isometric",
    "methodology.pathway": "biochar",
}

def with_default_applies_if(extra=None):
    applies = deepcopy(DEFAULT_APPLIES_IF)
    if extra:
        applies.update(extra)
    return applies


# =========================================================
# REQUIREMENT RECORD SHAPE
# =========================================================
# Each requirement should contain:
# - id: official Isometric requirement ID
# - title: short normalized title for UI/reporting
# - registry_section: section shown in Isometric registry
# - module: source module used operationally by Co2mply
# - applies_if: declarative applicability rules
# - fields: internal schema fields expected for evaluation
# - logic: logic key used by engine.requirement_logic.LOGIC_MAP
# - evidence_types: useful for extraction / traceability
# - severity: optional prioritization for reporting
# - notes: optional internal implementation notes

REQUIREMENTS = [
    # =====================================================
    # PROTOCOL & MONITORING DATA
    # =====================================================

    {
        "id": "R-Z106-1",
        "title": "Uncertainty inputs disclosed",
        "registry_section": "Uncertainty",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "quantification.input_variables",
            "quantification.input_uncertainties",
        ],
        "logic": "uncertainty_inputs",
        "evidence_types": [
            "quantification_method",
            "calculation_sheet",
            "uncertainty_table",
        ],
        "severity": "high",
        "notes": "Project must report all input variables used in net CO2e removal calculation and their uncertainties.",
    },
    {
        "id": "R-BFEE-0",
        "title": "Durability option declared",
        "registry_section": "Durability",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "methodology.durability_option",
        ],
        "logic": "durability_option_declared",
        "evidence_types": [
            "pdd_section",
            "methodology_choice_record",
        ],
        "severity": "high",
        "notes": "Project must state whether it is pursuing the combined 200- and 1000-year durability option.",
    },
    {
        "id": "R-Z4A3-0",
        "title": "Fuel-use reversal risk assessed",
        "registry_section": "Reversals",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "risk_assessment.fuel_use_risk_exists",
            "risk_assessment.particle_size_distribution",
            "risk_assessment.non_combustion_justification",
        ],
        "logic": "fuel_use_reversal_risk",
        "evidence_types": [
            "risk_assessment",
            "lab_report",
            "pdd_section",
        ],
        "severity": "high",
    },
    {
        "id": "R-6E1D-0",
        "title": "Biochar stockpiling disclosed",
        "registry_section": "Reversals",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "storage.stockpiled_before_end_use",
            "storage.stockpile_controls",
        ],
        "logic": "stockpiling_disclosure",
        "evidence_types": [
            "storage_plan",
            "operational_sop",
        ],
        "severity": "medium",
    },
    {
        "id": "R-BC4H-1",
        "title": "Adaptive management plan in place",
        "registry_section": "Adaptive management",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "management.information_sharing_plan",
            "management.emergency_response_plan",
            "management.pause_or_stop_conditions",
        ],
        "logic": "adaptive_management_plan",
        "evidence_types": [
            "management_plan",
            "emergency_plan",
            "sop",
        ],
        "severity": "high",
    },

    # =====================================================
    # SAMPLING PROCEDURE
    # =====================================================

    {
        "id": "R-6YSW-0",
        "title": "Production batch definition within allowed threshold",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "sampling.batch_definition_days",
            "methodology.production_subpathway",
        ],
        "logic": "sampling_batch_definition",
        "evidence_types": [
            "sampling_plan",
            "monitoring_plan",
        ],
        "severity": "high",
        "notes": "Public registry notes <1 month for general production and <7 days for combustion co-product systems.",
    },
    {
        "id": "R-S8K1-1",
        "title": "Sampling plan consistent with Methods A/B",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "sampling.method",
            "sampling.number",
            "sampling.frequency",
            "sampling.analytical_methods",
        ],
        "logic": "sampling_plan_consistency",
        "evidence_types": [
            "sampling_plan",
            "lab_plan",
        ],
        "severity": "high",
    },
    {
        "id": "R-ADXG-0",
        "title": "Method B moisture transition pathway selected",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if({
            "sampling.method": "B",
        }),
        "fields": [
            "sampling.method_b_moisture_transition_pathway",
        ],
        "logic": "method_b_moisture_pathway",
        "evidence_types": [
            "sampling_plan",
            "monitoring_plan",
        ],
        "severity": "medium",
    },
    {
        "id": "R-QTJS-0",
        "title": "Combustion co-product additional sampling requirements met",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production in Combustion Co-product Systems Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.production_subpathway": "combustion_coproduct",
        }),
        "fields": [
            "sampling.combustion_coproduct_requirements_met",
            "sampling.combustion_coproduct_evidence",
        ],
        "logic": "combustion_coproduct_sampling_requirements",
        "evidence_types": [
            "sampling_plan",
            "module_specific_annex",
        ],
        "severity": "high",
    },
    {
        "id": "R-NJ8G-0",
        "title": "Feedstock moisture management and verification",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "feedstock.moisture_management_plan",
            "feedstock.moisture_verification_method",
        ],
        "logic": "feedstock_moisture_management",
        "evidence_types": [
            "feedstock_sop",
            "monitoring_plan",
        ],
        "severity": "high",
    },
    {
        "id": "R-WVZT-0",
        "title": "Operator payment model does not incentivize volume over outcomes",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production in Distributed and Small Scale Projects Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.production_subpathway": "distributed_small_scale",
        }),
        "fields": [
            "operations.payment_model_description",
            "operations.payment_model_outcome_safeguards",
        ],
        "logic": "payment_model_safeguards",
        "evidence_types": [
            "operator_contract",
            "incentive_policy",
        ],
        "severity": "medium",
    },
    {
        "id": "R-GGVF-0",
        "title": "Technician training program evidenced",
        "registry_section": "Sampling procedure",
        "module": "Biochar Production in Distributed and Small Scale Projects Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.production_subpathway": "distributed_small_scale",
        }),
        "fields": [
            "operations.training_program",
            "operations.training_records",
        ],
        "logic": "technician_training_program",
        "evidence_types": [
            "training_program",
            "training_records",
            "sop",
        ],
        "severity": "medium",
    },

    # =====================================================
    # REACTOR DESIGN REQUIREMENTS
    # =====================================================

    {
        "id": "R-6AQG-1",
        "title": "P&ID or engineering design diagram with sensors",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "production.reactor_design_diagram",
            "production.sensor_inventory",
            "production.sensor_locations",
        ],
        "logic": "reactor_design_diagram",
        "evidence_types": [
            "p_and_id",
            "engineering_design_diagram",
            "sensor_map",
        ],
        "severity": "critical",
    },
    {
        "id": "R-DMET-0",
        "title": "Reactor material selection justified",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "production.reactor_components",
            "production.material_selection_justification",
        ],
        "logic": "reactor_material_selection",
        "evidence_types": [
            "engineering_memorial",
            "equipment_specification",
            "design_basis",
        ],
        "severity": "high",
    },
    {
        "id": "R-19AF-1",
        "title": "Reactor maintenance plan evidenced",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "production.maintenance_plan",
            "production.maintenance_schedule",
        ],
        "logic": "reactor_maintenance_plan",
        "evidence_types": [
            "maintenance_plan",
            "sop",
            "maintenance_schedule",
        ],
        "severity": "high",
    },
    {
        "id": "R-SZK5-1",
        "title": "High-pressure pyrolysis gas loss detection and quantification",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if({
            "production.reactor_pressure_regime": "high_pressure",
        }),
        "fields": [
            "production.reactor_pressure_bar_g",
            "production.gas_loss_detection_method",
            "production.gas_leakage_quantification_method",
        ],
        "logic": "high_pressure_gas_loss_detection",
        "evidence_types": [
            "instrumentation_plan",
            "pressure_monitoring_records",
            "leak_test_certificate",
        ],
        "severity": "critical",
        "notes": "Registry text specifies >0.5 bar above ambient pressure.",
    },
    {
        "id": "R-45Q4-0",
        "title": "Combustion co-product system eligibility met",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production in Combustion Co-product Systems Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.production_subpathway": "combustion_coproduct",
        }),
        "fields": [
            "production.combustion_coproduct_system_eligibility",
            "production.combustion_coproduct_system_evidence",
        ],
        "logic": "combustion_coproduct_system_eligibility",
        "evidence_types": [
            "module_specific_annex",
            "engineering_design_diagram",
        ],
        "severity": "critical",
    },
    {
        "id": "R-1XCV-0",
        "title": "Distributed and small-scale eligibility criteria met",
        "registry_section": "Reactor design requirements",
        "module": "Biochar Production in Distributed and Small Scale Projects Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.production_subpathway": "distributed_small_scale",
        }),
        "fields": [
            "production.distributed_small_scale_eligibility",
            "production.distributed_small_scale_monitoring_eligibility",
        ],
        "logic": "distributed_small_scale_eligibility",
        "evidence_types": [
            "module_specific_annex",
            "monitoring_plan",
        ],
        "severity": "critical",
    },

    # =====================================================
    # EMISSIONS TESTING
    # =====================================================

    {
        "id": "R-TKNH-0",
        "title": "Stack emissions monitoring method selected",
        "registry_section": "Emissions testing",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "emissions.stack_monitoring_method",
            "emissions.testing_frequency",
        ],
        "logic": "stack_emissions_monitoring_method",
        "evidence_types": [
            "emissions_test_plan",
            "cems_specification",
            "third_party_lab_scope",
        ],
        "severity": "high",
    },
    {
        "id": "R-E8H6-0",
        "title": "Pyrolysis gas end-use accounting approach selected",
        "registry_section": "Emissions testing",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "emissions.pyrolysis_gas_end_use_approach",
            "emissions.emissions_control_system",
        ],
        "logic": "pyrolysis_gas_end_use_accounting",
        "evidence_types": [
            "process_description",
            "mass_energy_balance",
            "emissions_plan",
        ],
        "severity": "high",
    },

    # =====================================================
    # BUILT ENVIRONMENT MODULE
    # =====================================================

    {
        "id": "R-PFG9-0",
        "title": "Built-environment storage evidence provided",
        "registry_section": "Applicability",
        "module": "Biochar Storage in the Built Environment Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "built_environment",
        }),
        "fields": [
            "storage.built_environment_incorporation_evidence",
        ],
        "logic": "built_environment_storage_evidence",
        "evidence_types": [
            "product_specification",
            "incorporation_record",
            "engineering_submittal",
        ],
        "severity": "critical",
    },
    {
        "id": "R-A4BY-0",
        "title": "Built materials meet performance requirements",
        "registry_section": "Applicability",
        "module": "Biochar Storage in the Built Environment Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "built_environment",
        }),
        "fields": [
            "storage.built_material_performance_evidence",
        ],
        "logic": "built_material_performance",
        "evidence_types": [
            "product_standard_certificate",
            "test_report",
        ],
        "severity": "critical",
    },
    {
        "id": "R-XS7K-0",
        "title": "Built materials do not require additional installation or maintenance products",
        "registry_section": "Applicability",
        "module": "Biochar Storage in the Built Environment Module v1.0",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "built_environment",
        }),
        "fields": [
            "storage.additional_installation_products_required",
            "storage.additional_maintenance_products_required",
        ],
        "logic": "built_environment_additional_products",
        "evidence_types": [
            "product_specification",
            "installation_manual",
        ],
        "severity": "medium",
    },

    # =====================================================
    # ENVIRONMENTAL AND SOCIAL SAFEGUARDS
    # =====================================================

    {
        "id": "R-HE38-0",
        "title": "Contaminant monitoring plan specified",
        "registry_section": "Environmental and social safeguards",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "safeguards.contaminant_monitoring_plan",
            "safeguards.contaminants_tracked",
            "safeguards.testing_frequency",
        ],
        "logic": "contaminant_monitoring_plan",
        "evidence_types": [
            "monitoring_plan",
            "quality_plan",
        ],
        "severity": "high",
    },
    {
        "id": "R-52YX-0",
        "title": "Applicable environmental legal requirements provided",
        "registry_section": "Environmental and social safeguards",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "legal.applicable_environmental_requirements",
        ],
        "logic": "environmental_legal_requirements",
        "evidence_types": [
            "permit_register",
            "legal_register",
            "licenses",
        ],
        "severity": "high",
    },
    {
        "id": "R-RQTJ-0",
        "title": "Regulatory measurements approach described",
        "registry_section": "Environmental and social safeguards",
        "module": "Isometric Standard v1.5.1",
        "applies_if": with_default_applies_if(),
        "fields": [
            "legal.regulatory_measurement_methods",
        ],
        "logic": "regulatory_measurement_methods",
        "evidence_types": [
            "monitoring_plan",
            "regulatory_compliance_plan",
        ],
        "severity": "medium",
    },

    # =====================================================
    # SYSTEM BOUNDARIES
    # =====================================================

    {
        "id": "R-CCP7-0",
        "title": "Storage emissions fully included in system boundary",
        "registry_section": "System boundaries",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "quantification.system_boundary_description",
            "quantification.storage_emissions_accounted",
        ],
        "logic": "storage_system_boundary",
        "evidence_types": [
            "quantification_method",
            "lca_report",
            "boundary_diagram",
        ],
        "severity": "critical",
    },

    # =====================================================
    # BIOCHAR CHARACTERIZATION
    # =====================================================

    {
        "id": "R-6F0N-0",
        "title": "Chemical analysis for biochar characterization performed",
        "registry_section": "Biochar characterization",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "biochar.characterization.chemical_analysis_performed",
            "biochar.characterization.lab_reports",
        ],
        "logic": "biochar_chemical_analysis",
        "evidence_types": [
            "lab_report",
            "characterization_report",
        ],
        "severity": "critical",
    },
    {
        "id": "R-NYQT-0",
        "title": "Biochar characterization and ongoing monitoring approach described",
        "registry_section": "Biochar characterization",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "biochar.characterization.approach_description",
            "biochar.characterization.ongoing_monitoring_plan",
        ],
        "logic": "biochar_characterization_approach",
        "evidence_types": [
            "pdd_section",
            "monitoring_plan",
        ],
        "severity": "high",
    },
    {
        "id": "R-VGXA-0",
        "title": "All required physical and chemical measurements obtained or planned",
        "registry_section": "Biochar characterization",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "biochar.characterization.required_measurements_complete",
            "biochar.characterization.measurement_values",
        ],
        "logic": "biochar_required_measurements",
        "evidence_types": [
            "lab_report",
            "characterization_table",
        ],
        "severity": "critical",
    },

    # =====================================================
    # QUANTIFICATION
    # =====================================================

    {
        "id": "R-KPDH-0",
        "title": "Crediting activity boundaries described in detail",
        "registry_section": "Quantification",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "quantification.crediting_activity_boundaries",
        ],
        "logic": "crediting_activity_boundaries",
        "evidence_types": [
            "boundary_diagram",
            "pdd_section",
            "lca_report",
        ],
        "severity": "critical",
    },
    {
        "id": "R-7B96-0",
        "title": "At least 500 R0 inertinite measurements per sample",
        "registry_section": "Calculation of inertinite",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if({
            "methodology.durability_option": "combined_200_1000",
        }),
        "fields": [
            "biochar.inertinite_analysis.r0_measurement_count_per_sample",
            "biochar.inertinite_analysis.r0_method_description",
        ],
        "logic": "inertinite_measurement_count",
        "evidence_types": [
            "petrographic_report",
            "lab_report",
        ],
        "severity": "high",
        "notes": "Applicability may depend on the chosen durability pathway/model; keep this conditional in engine config.",
    },

    # =====================================================
    # PROCESS REQUIREMENTS / EQUIPMENT
    # =====================================================

    {
        "id": "R-V04V-0",
        "title": "End material production process described in detail",
        "registry_section": "Process requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "production.end_material_process_description",
        ],
        "logic": "end_material_process_description",
        "evidence_types": [
            "process_flow_diagram",
            "pdd_section",
            "sop",
        ],
        "severity": "high",
    },
    {
        "id": "R-EN0G-0",
        "title": "Biochar incorporation documented",
        "registry_section": "Process requirements",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "storage.incorporation_documentation",
        ],
        "logic": "biochar_incorporation_documentation",
        "evidence_types": [
            "deployment_records",
            "logbook",
            "geotagged_photos",
        ],
        "severity": "critical",
    },
    {
        "id": "R-29W5-0",
        "title": "Engineering design diagram provided",
        "registry_section": "Reactor and equipment description",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "production.engineering_design_diagram",
        ],
        "logic": "engineering_design_diagram",
        "evidence_types": [
            "engineering_design_diagram",
        ],
        "severity": "high",
    },
    {
        "id": "R-9KKF-0",
        "title": "Compliance with relevant product standards evidenced",
        "registry_section": "Compliance with product standards",
        "module": "Biochar Production and Storage Protocol v1.2",
        "applies_if": with_default_applies_if(),
        "fields": [
            "product.relevant_standards",
            "product.compliance_evidence",
            "product.comparability_to_traditional_products",
        ],
        "logic": "product_standard_compliance",
        "evidence_types": [
            "certificate",
            "test_report",
            "specification_sheet",
        ],
        "severity": "high",
    },

    # =====================================================
    # SOIL ENVIRONMENTS MODULE
    # =====================================================

    {
        "id": "R-F5RZ-0",
        "title": "Annual average soil temperature method provided",
        "registry_section": "Monitoring requirements",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
            "methodology.durability_option": "200",
        }),
        "fields": [
            "storage.soil.annual_average_soil_temperature_method",
        ],
        "logic": "soil_temperature_method",
        "evidence_types": [
            "soil_monitoring_plan",
            "climate_method_note",
        ],
        "severity": "medium",
    },
    {
        "id": "R-3MYN-0",
        "title": "Chain of custody diagram or equivalent provided",
        "registry_section": "Monitoring requirements",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
        }),
        "fields": [
            "traceability.chain_of_custody_diagram",
        ],
        "logic": "chain_of_custody_diagram",
        "evidence_types": [
            "chain_of_custody_diagram",
            "traceability_procedure",
        ],
        "severity": "critical",
    },
    {
        "id": "R-T2X2-0",
        "title": "Deployment method specified",
        "registry_section": "Mixing pathway",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
        }),
        "fields": [
            "storage.soil.deployment_methods",
        ],
        "logic": "deployment_method_selected",
        "evidence_types": [
            "deployment_plan",
            "pdd_section",
        ],
        "severity": "critical",
    },
    {
        "id": "R-1CMC-0",
        "title": "Mixing pathway controls confirmed",
        "registry_section": "Mixing pathway",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
            "storage.soil.deployment_methods__contains_any": ["on_site_mixing", "third_party_mixing"],
        }),
        "fields": [
            "storage.soil.integration_method",
            "storage.soil.end_use_definition",
            "traceability.custody_tracking_approach",
            "risk_assessment.reversal_prevention_approach",
        ],
        "logic": "mixing_pathway_controls",
        "evidence_types": [
            "deployment_plan",
            "custody_tracking_plan",
            "reversal_risk_plan",
        ],
        "severity": "critical",
    },
    {
        "id": "R-8PBP-0",
        "title": "Direct soil application evidence pathway confirmed",
        "registry_section": "Mixing pathway",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
            "storage.soil.deployment_methods__contains": "direct_soil_application",
        }),
        "fields": [
            "storage.soil.direct_application_evidence_pathway",
        ],
        "logic": "direct_soil_application_evidence",
        "evidence_types": [
            "geotagged_photos",
            "timestamped_visual_evidence",
            "logbook_records",
            "project_boundaries",
        ],
        "severity": "critical",
    },
    {
        "id": "R-WB7B-0",
        "title": "On-site mixing records and tracking confirmed",
        "registry_section": "Mixing pathway",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
            "storage.soil.deployment_methods__contains": "on_site_mixing",
        }),
        "fields": [
            "storage.soil.on_site_mixing_records",
            "traceability.quantitative_tracking_system",
        ],
        "logic": "on_site_mixing_records",
        "evidence_types": [
            "facility_records",
            "batch_records",
            "photos_videos",
            "weighbridge_records",
            "inventory_records",
        ],
        "severity": "critical",
    },
    {
        "id": "R-G030-0",
        "title": "Third-party sales and mixing evidence confirmed",
        "registry_section": "Mixing pathway",
        "module": "Biochar Storage in Soil Environments Module v1.2",
        "applies_if": with_default_applies_if({
            "methodology.storage_pathway": "soil",
            "storage.soil.deployment_methods__contains": "third_party_mixing",
        }),
        "fields": [
            "commercial.third_party_purchaser_affidavit",
            "commercial.sales_invoices",
            "commercial.delivery_records",
            "storage.soil.third_party_mixing_evidence",
            "traceability.quantitative_tracking_system",
        ],
        "logic": "third_party_mixing_sales_evidence",
        "evidence_types": [
            "purchaser_affidavit",
            "invoice",
            "delivery_note",
            "photos_videos",
            "weighbridge_records",
            "inventory_records",
        ],
        "severity": "critical",
    },
]
