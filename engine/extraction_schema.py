# engine/extraction_schema.py

EXTRACTION_FIELDS = [
    # =========================================================
    # METHODOLOGY
    # =========================================================
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

    # =========================================================
    # PROJECT
    # =========================================================
    {
        "path": "project.project_boundary_defined",
        "type": "boolean",
        "description": "Whether the project boundary is explicitly defined.",
    },

    # =========================================================
    # ELIGIBILITY
    # =========================================================
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
        "description": "Durability duration in years when stated or inferred.",
    },
    {
        "path": "eligibility.permanence_claim",
        "type": "boolean",
        "description": "Whether the project explicitly claims permanence or long-term carbon storage.",
    },

    # =========================================================
    # PRODUCTION
    # =========================================================
    {
        "path": "production.pyrolysis_technology",
        "type": "string",
        "description": "Pyrolysis technology type used in the project.",
    },
    {
        "path": "production.thermal_process_type",
        "type": "string",
        "description": "Thermal conversion process type described by the project.",
    },
    {
        "path": "production.system_description",
        "type": "string",
        "description": "Narrative description of the production system or technology configuration.",
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

    # =========================================================
    # BIOCHAR CHARACTERIZATION — numeric (Phase 3, R-XXXX protocol-native)
    # =========================================================
    {
        "path": "biochar.characterization.h_c_ratio",
        "type": "float",
        "requirement_id": "R-VGXA-0",
        "guidance_id": "G-TY6S-0",
        "description": "H/Corg molar ratio from elemental analysis. Protocol hard gate: must be < 0.5 for 200-year durability.",
        "extraction_hint": "Search for 'H/C ratio', 'H/Corg', 'hydrogen to carbon ratio', 'hydrogen to organic carbon'. Extract the numeric value (e.g. 0.43). Often in biochar characterization appendix.",
    },
    {
        "path": "biochar.characterization.o_c_ratio",
        "type": "float",
        "requirement_id": "R-VGXA-0",
        "guidance_id": "G-27Y3-0",
        "description": "O/Corg molar ratio from elemental analysis. Protocol threshold: < 0.2.",
        "extraction_hint": "Search for 'O/C ratio', 'O/Corg', 'oxygen to organic carbon ratio'. Extract numeric value.",
    },
    {
        "path": "biochar.characterization.pcb_mg_kg",
        "type": "float",
        "requirement_id": "R-MY64-0",
        "description": "PCB (polychlorinated biphenyls) concentration in mg/kg DM. WBC limit: ≤ 0.2 mg/kg.",
        "extraction_hint": "Search for 'PCB', 'polychlorinated biphenyls' in biochar analysis results. Extract numeric value in mg/kg.",
    },
    {
        "path": "biochar.characterization.pcdd_f_ng_kg",
        "type": "float",
        "requirement_id": "R-MY64-0",
        "description": "PCDD/F (dioxins/furans) in ng/kg DM. WBC limit: ≤ 20 ng/kg.",
        "extraction_hint": "Search for 'PCDD/F', 'dioxins', 'furans', 'polychlorinated dibenzo-p-dioxins' in analysis. Extract numeric value in ng/kg.",
    },
    {
        "path": "biochar.characterization.pah_epa16_mg_kg",
        "type": "float",
        "requirement_id": "R-MY64-0",
        "description": "Sum of 16 EPA PAHs in mg/kg DM. Must be declared.",
        "extraction_hint": "Search for 'PAH', 'polycyclic aromatic hydrocarbons', 'sum of EPA 16 PAHs'. Extract numeric value in mg/kg.",
    },

    # =========================================================
    # STORAGE — soil temperature (Phase 3, R-F5RZ-0)
    # =========================================================
    {
        "path": "storage.soil.annual_avg_temp_celsius",
        "type": "float",
        "requirement_id": "R-F5RZ-0",
        "description": "Annual average soil temperature in °C used in Fdurable calculation (200-year option).",
        "extraction_hint": "Search for soil temperature value used in durability/Fdurable calculation, e.g. '18.5°C', 'mean soil temperature'. Extract numeric value.",
    },
    {
        "path": "storage.soil.temperature_method",
        "type": "string",
        "requirement_id": "R-F5RZ-0",
        "allowed_values": ["direct_measurement", "global_database", "lembrechts_2022"],
        "description": "Method to obtain annual average soil temperature.",
        "extraction_hint": "Search for whether soil temperature comes from direct field measurement or from global database (Lembrechts et al. 2022 or equivalent).",
    },

    # =========================================================
    # SAMPLING — numeric (Phase 3, R-S8K1-1)
    # =========================================================
    {
        "path": "sampling.method",
        "type": "string",
        "allowed_values": ["A", "B"],
        "description": "Sampling method used by the project.",
    },
    {
        "path": "sampling.sampling_method",
        "type": "string",
        "requirement_id": "R-S8K1-1",
        "allowed_values": ["method_a", "method_b"],
        "description": "Sampling method: Method A (every batch) or Method B (1 per 10 batches, after 30 samples).",
        "extraction_hint": "Search for explicit mention of 'Method A', 'Method B', or sampling frequency (every batch vs every 10 batches).",
    },
    {
        "path": "sampling.sample_count",
        "type": "integer",
        "requirement_id": "R-S8K1-1",
        "description": "Total number of biochar samples collected. Protocol requires ≥ 30 before using Method B.",
        "extraction_hint": "Search for total sample count, e.g. '45 samples collected', '30 samples minimum'. Extract integer.",
    },
    {
        "path": "sampling.samples_per_batch",
        "type": "integer",
        "requirement_id": "R-S8K1-1",
        "description": "Number of samples per production batch. Protocol minimum: 3.",
        "extraction_hint": "Search for 'samples per batch', 'minimum 3 samples', 'three replicates per batch'. Extract integer.",
    },
    {
        "path": "sampling.sample_age_months",
        "type": "float",
        "requirement_id": "R-S8K1-1",
        "description": "Maximum age of eligible samples in months. Protocol: only ≤ 6 months eligible.",
        "extraction_hint": "Search for sample age window, e.g. '6 months', 'last six months'. Extract numeric value.",
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

    # =========================================================
    # PROJECT — location and ownership (Phase 3, R-A5B6-0, R-M858-0)
    # =========================================================
    {
        "path": "project.country",
        "type": "string",
        "requirement_id": "R-A5B6-0",
        "description": "Country where the project is located.",
        "extraction_hint": "Search for country name in project location section. R-A5B6-0 requires at least one address/geo-coordinate.",
    },
    {
        "path": "project.locations",
        "type": "list",
        "requirement_id": "R-A5B6-0",
        "description": "Project addresses and/or geo-coordinates.",
        "extraction_hint": "Search for specific addresses, GPS coordinates (lat/lon), city/state/country of project facilities.",
    },
    {
        "path": "project.ownership_evidence",
        "type": "list",
        "requirement_id": "R-M858-0",
        "description": "Evidence of legal ownership over carbon removal rights.",
        "extraction_hint": "Search for company name, legal entity name, registration number, ownership contract mention, project proponent identification.",
    },

    # =========================================================
    # FEEDSTOCK
    # =========================================================
    {
        "path": "feedstock.biomass_type",
        "type": "string",
        "description": "Biomass/feedstock type.",
    },
    {
        "path": "feedstock.certification_scheme",
        "type": "string",
        "description": "Feedstock or biomass sourcing certification scheme, when applicable.",
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

    # =========================================================
    # QUANTIFICATION / GHG ACCOUNTING
    # =========================================================
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
        "path": "quantification.lca_performed",
        "type": "boolean",
        "description": "Whether an LCA or equivalent lifecycle quantification study is evidenced.",
    },
    {
        "path": "ghg_accounting.system_boundary_defined",
        "type": "boolean",
        "description": "Whether the GHG accounting system boundary is defined.",
    },

    # =========================================================
    # STORAGE
    # =========================================================
    {
        "path": "storage.storage_module",
        "type": "string",
        "description": "Storage module or storage category used by the project.",
    },
    {
        "path": "storage.storage_location",
        "type": "string",
        "description": "Storage location or storage destination described by the project.",
    },
    {
        "path": "storage.storage_monitoring_plan",
        "type": "boolean",
        "description": "Whether a storage monitoring plan is evidenced.",
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

    # =========================================================
    # TRACEABILITY
    # =========================================================
    {
        "path": "traceability.chain_of_custody_diagram",
        "type": "boolean",
        "description": "Whether a chain of custody diagram or equivalent is evidenced.",
    },

    # =========================================================
    # MANAGEMENT
    # =========================================================
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
        "path": "management.pause_or_stop_conditions",
        "type": "boolean",
        "description": "Whether pause or stop conditions are documented.",
    },

    # =========================================================
    # MONITORING / REPORTING
    # =========================================================
    {
        "path": "monitoring_reporting.monitoring_plan",
        "type": "boolean",
        "description": "Whether a monitoring plan is evidenced.",
    },
    {
        "path": "monitoring_reporting.uncertainty_method",
        "type": "string",
        "description": "Method used to address or quantify uncertainty.",
    },
    {
        "path": "monitoring_reporting.verification_ready",
        "type": "boolean",
        "description": "Whether the project appears verification-ready from a monitoring/reporting perspective.",
    },

    # =========================================================
    # RISK ASSESSMENT
    # =========================================================
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

    # =========================================================
    # EMISSIONS
    # =========================================================
    {
        "path": "emissions.syngas_handling",
        "type": "string",
        "description": "How pyrolysis gases or syngas are handled, combusted, flared, or otherwise treated.",
    },
    {
        "path": "emissions.emissions_sources_identified",
        "type": "boolean",
        "description": "Whether emissions sources are identified in the project documentation.",
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

    # =========================================================
    # LEGAL
    # =========================================================
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

    # =========================================================
    # BIOCHAR CHARACTERIZATION
    # =========================================================
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

    # =========================================================
    # PRODUCT
    # =========================================================
    {
        "path": "product.standard_compliance",
        "type": "boolean",
        "description": "Whether compliance with relevant product standards is evidenced.",
    },
    {
        "path": "product.certification_scheme",
        "type": "string",
        "description": "Certification scheme or reference standard used at product level.",
    },
    {
        "path": "product.end_use",
        "type": "string",
        "description": "Declared end use of the biochar product.",
    },
]
