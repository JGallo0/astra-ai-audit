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
        "path": "traceability.chain_of_custody_diagram",
        "type": "boolean",
        "description": "Whether a chain of custody diagram or equivalent is evidenced.",
    },
]
