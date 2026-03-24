# engine/extraction_schema.py

EXTRACTION_FIELDS = [
    {
        "path": "methodology.standard",
        "type": "string",
        "allowed_values": ["Isometric"],
        "description": "Crediting standard used by the project.",
    },
    {
        "path": "methodology.pathway",
        "type": "string",
        "allowed_values": ["biochar"],
        "description": "Project pathway.",
    },
    {
        "path": "methodology.production_subpathway",
        "type": "string",
        "allowed_values": ["standard", "combustion_coproduct", "distributed_small_scale"],
        "description": "Production subpathway under the methodology.",
    },
    {
        "path": "methodology.storage_pathway",
        "type": "string",
        "allowed_values": ["soil", "built_environment"],
        "description": "Storage pathway.",
    },
    {
        "path": "methodology.durability_option",
        "type": "string",
        "allowed_values": ["200", "1000", "combined_200_1000"],
        "description": "Declared durability option.",
    },
    {
        "path": "eligibility.net_negative_claim",
        "type": "boolean",
        "description": "Whether the project claims net-negative removals.",
    },
    {
        "path": "eligibility.additionality_claim",
        "type": "boolean",
        "description": "Whether the project explicitly claims additionality.",
    },
    {
        "path": "eligibility.durability_years",
        "type": "integer",
        "description": "Durability duration in years when stated.",
    },
    {
        "path": "production.pyrolysis_technology",
        "type": "string",
        "description": "Pyrolysis technology type used in the project.",
    },
    {
        "path": "production.reactor_design_diagram",
        "type": "boolean",
        "description": "Whether a reactor design diagram or P&ID is evidenced.",
    },
    {
        "path": "production.sensor_inventory",
        "type": "boolean",
        "description": "Whether a sensor inventory is evidenced.",
    },
    {
        "path": "production.sensor_locations",
        "type": "boolean",
        "description": "Whether sensor locations are evidenced.",
    },
    {
        "path": "production.maintenance_plan",
        "type": "boolean",
        "description": "Whether a maintenance plan is evidenced.",
    },
    {
        "path": "production.maintenance_schedule",
        "type": "boolean",
        "description": "Whether a maintenance schedule is evidenced.",
    },
    {
        "path": "production.reactor_components",
        "type": "boolean",
        "description": "Whether reactor components are described.",
    },
    {
        "path": "production.material_selection_justification",
        "type": "boolean",
        "description": "Whether material selection justification is evidenced.",
    },
    {
        "path": "production.engineering_design_diagram",
        "type": "boolean",
        "description": "Whether an engineering design diagram is evidenced.",
    },
    {
        "path": "production.end_material_process_description",
        "type": "boolean",
        "description": "Whether the end material process description is evidenced.",
    },
    {
        "path": "sampling.method",
        "type": "string",
        "allowed_values": ["A", "B"],
        "description": "Sampling method used by the project.",
    },
    {
        "path": "sampling.batch_definition_days",
        "type": "integer",
        "description": "Number of days used to define a production batch.",
    },
    {
        "path": "sampling.sampling_plan_defined",
        "type": "boolean",
        "description": "Whether a sampling plan is evidenced.",
    },
    {
        "path": "feedstock.biomass_type",
        "type": "string",
        "description": "Biomass/feedstock type.",
    },
    {
        "path": "feedstock.pre_project_biomass_use",
        "type": "string",
        "description": "Pre-project use of biomass/feedstock.",
    },
    {
        "path": "feedstock.feedstock_accounting_module_compliance",
        "type": "boolean",
        "description": "Whether feedstock accounting module compliance is evidenced.",
    },
    {
        "path": "feedstock.moisture_control_plan",
        "type": "boolean",
        "description": "Whether a feedstock moisture control plan is evidenced.",
    },
    {
        "path": "feedstock.moisture_measurement",
        "type": "boolean",
        "description": "Whether feedstock moisture measurement is evidenced.",
    },
    {
        "path": "quantification.input_variables",
        "type": "boolean",
        "description": "Whether input variables are disclosed.",
    },
    {
        "path": "quantification.input_uncertainties",
        "type": "boolean",
        "description": "Whether input uncertainties are disclosed.",
    },
    {
        "path": "quantification.crediting_activity_boundaries",
        "type": "boolean",
        "description": "Whether crediting activity boundaries are described.",
    },
    {
        "path": "quantification.storage_emissions_accounted",
        "type": "boolean",
        "description": "Whether storage emissions are accounted for.",
    },
    {
        "path": "storage.storage_environment_stable",
        "type": "boolean",
        "description": "Whether the storage environment is stable.",
    },
    {
        "path": "storage.stockpiled_before_end_use",
        "type": "boolean",
        "description": "Whether biochar is stockpiled before end use.",
    },
    {
        "path": "storage.stockpiling_documented",
        "type": "boolean",
        "description": "Whether stockpiling is documented when applicable.",
    },
    {
        "path": "storage.soil.deployment_methods",
        "type": "list_string",
        "description": "Deployment methods used in soil storage pathway.",
    },
    {
        "path": "storage.soil.direct_application_evidence_pathway",
        "type": "boolean",
        "description": "Whether evidence exists for direct soil application pathway.",
    },
    {
        "path": "traceability.chain_of_custody_diagram",
        "type": "boolean",
        "description": "Whether a chain of custody diagram or equivalent is evidenced.",
    },
    {
        "path": "management.adaptive_management_plan",
        "type": "boolean",
        "description": "Whether an adaptive management plan is evidenced.",
    },
    {
        "path": "management.monitoring_triggers",
        "type": "boolean",
        "description": "Whether monitoring triggers are documented.",
    },
    {
        "path": "risk_assessment.fuel_use_reversal_risk",
        "type": "boolean",
        "description": "Whether fuel-use reversal risk assessment is evidenced.",
    },
    {
        "path": "risk_assessment.mitigation_plan",
        "type": "boolean",
        "description": "Whether a mitigation plan is documented.",
    },
    {
        "path": "emissions.stack_monitoring_method",
        "type": "string",
        "description": "Method used for stack emissions monitoring.",
    },
    {
        "path": "emissions.testing_frequency",
        "type": "string",
        "description": "Testing frequency for stack emissions monitoring.",
    },
    {
        "path": "legal.applicable_environmental_requirements",
        "type": "boolean",
        "description": "Whether applicable environmental legal requirements are documented.",
    },
    {
        "path": "legal.regulatory_measurement_methods",
        "type": "boolean",
        "description": "Whether regulatory measurement methods are documented.",
    },
    {
        "path": "biochar.characterization.chemical_analysis_performed",
        "type": "boolean",
        "description": "Whether chemical analysis for biochar characterization is evidenced.",
    },
    {
        "path": "biochar.characterization.lab_reports",
        "type": "boolean",
        "description": "Whether supporting lab reports are evidenced.",
    },
    {
        "path": "biochar.characterization.required_measurements_complete",
        "type": "boolean",
        "description": "Whether required measurements are complete.",
    },
    {
        "path": "biochar.characterization.measurement_values",
        "type": "boolean",
        "description": "Whether measurement values are documented.",
    },
    {
        "path": "biochar.characterization.approach_description",
        "type": "boolean",
        "description": "Whether the characterization approach is documented.",
    },
    {
        "path": "biochar.characterization.ongoing_monitoring_plan",
        "type": "boolean",
        "description": "Whether ongoing monitoring plan is documented.",
    },
    {
        "path": "biochar.characterization.contaminant_testing",
        "type": "boolean",
        "description": "Whether contaminant testing is documented.",
    },
    {
        "path": "biochar.characterization.contaminant_testing_frequency",
        "type": "string",
        "description": "Frequency of contaminant testing.",
    },
    {
        "path": "product.standard_compliance",
        "type": "boolean",
        "description": "Whether compliance with relevant product standards is evidenced.",
    },
    {
        "path": "product.certification_scheme",
        "type": "string",
        "description": "Certification scheme or reference standard used.",
    },
]
