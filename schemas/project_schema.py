# schemas/project_schema.py

def get_empty_project_data():
    return {
        "project": {
            "name": None,
            "country": None,
            "locations": [],
            "project_boundary_defined": False,
            "ownership_evidence": [],
            "methodology": None,
            "crediting_standard": None
        },

        "eligibility": {
            "net_negative_claim": None,
            "durability_years": None,
            "additionality_claim": None,
            "additionality_evidence": [],
            "eligible_pathway": None
        },

        "feedstock": {
            "biomass_type": None,
            "source_locations": [],
            "pre_project_biomass_use": None,
            "feedstock_accounting_module_compliance": None
        },

        "production": {
            "pyrolysis_technology": None,
            "reactor_design_diagram": False,
            "process_parameters": {},
            "production_rate": None,
            "maintenance_plan": False
        },

        "biochar_characterization": {
            "carbon_content": None,
            "h_c_ratio": None,
            "o_c_ratio": None,
            "sampling_method": None,
            "sampling_frequency": None,
            "pollutants": {
                "PAHs": None,
                "heavy_metals": None,
                "PCBs": None,
                "dioxins": None,
                "furans": None
            }
        },

        "storage": {
            "storage_module": None,
            "storage_location": None,
            "storage_environment_stable": None,
            "storage_monitoring_plan": False,
            "loss_accounting_method": None
        },

        "ghg_accounting": {
            "system_boundary_defined": False,
            "baseline_defined": False,
            "co2_removed": None,
            "co2_stored": None,
            "counterfactual_emissions": None,
            "operations_emissions": None,
            "leakage_emissions": None,
            "end_of_life_emissions": None,
            "net_cdr": None
        },

        "emissions_testing": {
            "measurement_option": None,
            "continuous_measurement": False,
            "regular_testing": False,
            "gaseous_route": None,
            "leakage_monitoring": False
        },

        "safeguards": {
            "environmental_risk_assessment": False,
            "social_risk_assessment": False,
            "stakeholder_input_process": False,
            "mitigation_plan": False,
            "adaptive_management_plan": False,
            "permits_documented": False
        },

        "monitoring_reporting": {
            "monitoring_plan": False,
            "data_sharing_plan": False,
            "uncertainty_method": None,
            "verification_ready": False,
            "vvb_requirements_addressed": False
        }
    }

def get_demo_project_data():
    data = get_empty_project_data()
    data["project"]["name"] = "Demo Biochar Project"
    data["eligibility"]["net_negative_claim"] = True
    data["eligibility"]["additionality_claim"] = True
    data["eligibility"]["durability_years"] = 500
    data["production"]["pyrolysis_technology"] = "continuous"
    data["production"]["reactor_design_diagram"] = True
    data["production"]["maintenance_plan"] = True
    data["storage"]["storage_environment_stable"] = True
    data["storage"]["storage_module"] = "soil_application"
    data["storage"]["storage_monitoring_plan"] = True
    data["feedstock"]["biomass_type"] = "eucalyptus_residues"
    data["feedstock"]["pre_project_biomass_use"] = "left_on_field"
    data["feedstock"]["feedstock_accounting_module_compliance"] = True

    data["monitoring_reporting"]["monitoring_plan"] = True
    data["monitoring_reporting"]["uncertainty_method"] = "defined"
    data["monitoring_reporting"]["verification_ready"] = True
    return data
