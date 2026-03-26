from versioning.methodology_manager import get_requirements
from engine.requirement_logic import run_engine

project_data = {
    "methodology": {
        "standard": "Isometric",
        "pathway": "biochar",
        "production_subpathway": "standard",
        "storage_pathway": "soil",
        "durability_option": "200",
    },

    "eligibility": {
        "net_negative_claim": True,
        "additionality_claim": True,
        "durability_years": 500,
    },

    "production": {
        "pyrolysis_technology": "continuous",
        "reactor_design_diagram": True,
        "maintenance_plan": True,
        "reactor_pressure_regime": "atmospheric",
        "sensor_inventory": True,
        "sensor_locations": True,
    },

    "storage": {
        "storage_environment_stable": True,
        "stockpiled_before_end_use": False,
        "soil": {
            "deployment_methods": ["direct_soil_application"],
            "integration_method": "direct",
        },
    },

    "sampling": {
        "method": "A",
        "batch_definition_days": 7,
    },

    "monitoring_reporting": {
        "monitoring_plan": True,
        "uncertainty_method": "basic",
        "verification_ready": True,
    },

    "feedstock": {
        "biomass_type": "eucalyptus_residue",
        "pre_project_biomass_use": "left_on_field",
        "feedstock_accounting_module_compliance": True,
    },

    "quantification": {
        "input_variables": True,
        "input_uncertainties": True,
    },

    "biochar": {
        "characterization": {
            "chemical_analysis_performed": True,
            "lab_reports": True,
        }
    },

    "traceability": {
        "chain_of_custody_diagram": True,
    },
}

requirements = get_requirements()
results = run_engine(project_data, requirements)

for r in results:
    print(
        f'{r["requirement_id"]} | {r["status"]} | {r["requirement_name"]} | {r["logic_key"]}'
    )
