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
            "crediting_standard": None,
        },

        "eligibility": {
            "net_negative_claim": None,
            "durability_years": None,
            "additionality_claim": None,
            "additionality_evidence": [],
            "eligible_pathway": None,
        },

        "feedstock": {
            "biomass_type": None,
            "source_locations": [],
            "pre_project_biomass_use": None,
            "feedstock_accounting_module_compliance": None,
        },

        "production": {
            "pyrolysis_technology": None,
            "reactor_design_diagram": False,
            "process_parameters": {},
            "production_rate": None,
            "maintenance_plan": False,
        },

        "biochar_characterization": {
            "carbon_content": None,
            "h_c_ratio": None,
            "o_c_ratio": None,
            "sampling_method": None,
            "sampling_frequency": None,
            "approach_description": None,
            "ongoing_monitoring_plan": None,
            "pollutants": {
                "PAHs": None,
                "heavy_metals": None,
                "PCBs": None,
                "dioxins": None,
                "furans": None,
            },
        },

        "storage": {
            "storage_module": None,
            "storage_location": None,
            "storage_environment_stable": None,
            "storage_monitoring_plan": False,
            "loss_accounting_method": None,
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
            "net_cdr": None,
        },

        "emissions_testing": {
            "measurement_option": None,
            "continuous_measurement": False,
            "regular_testing": False,
            "gaseous_route": None,
            "leakage_monitoring": False,
        },

        "safeguards": {
            "environmental_risk_assessment": False,
            "social_risk_assessment": False,
            "stakeholder_input_process": False,
            "mitigation_plan": False,
            "adaptive_management_plan": False,
            "permits_documented": False,
        },

        "monitoring_reporting": {
            "monitoring_plan": False,
            "data_sharing_plan": False,
            "uncertainty_method": None,
            "verification_ready": False,
            "vvb_requirements_addressed": False,
        },
    }


def get_demo_project_data():
    data = get_empty_project_data()

    # Projeto
    data["project"]["name"] = "Demo Biochar Project"

    # Elegibilidade
    data["eligibility"]["net_negative_claim"] = True
    data["eligibility"]["additionality_claim"] = True
    data["eligibility"]["durability_years"] = 500

    # Produção
    data["production"]["pyrolysis_technology"] = "continuous"
    data["production"]["reactor_design_diagram"] = True
    data["production"]["maintenance_plan"] = True
    data["production"]["maintenance_schedule"] = True
    data["production"]["sensor_inventory"] = True
    data["production"]["sensor_locations"] = True
    data["production"]["reactor_components"] = True
    data["production"]["material_selection_justification"] = True
    data["production"]["engineering_design_diagram"] = True
    data["production"]["end_material_process_description"] = True

    # Armazenamento
    data["storage"]["storage_environment_stable"] = True
    data["storage"]["storage_module"] = "soil_application"
    data["storage"]["storage_location"] = "demo_storage_site"
    data["storage"]["storage_monitoring_plan"] = True
    data["storage"]["loss_accounting_method"] = "mass_balance"
    data["storage"]["stockpiled_before_end_use"] = False
    data["storage"]["stockpiling_documented"] = True
    data["storage"]["soil"] = {
        "deployment_methods": ["direct_soil_application"],
        "integration_method": "direct",
        "direct_application_evidence_pathway": True,
    }

    # Biomassa
    data["feedstock"]["biomass_type"] = "eucalyptus_residues"
    data["feedstock"]["pre_project_biomass_use"] = "left_on_field"
    data["feedstock"]["feedstock_accounting_module_compliance"] = True
    data["feedstock"]["moisture_control_plan"] = True
    data["feedstock"]["moisture_measurement"] = True

    # Monitoramento e reporte
    data["monitoring_reporting"]["monitoring_plan"] = True
    data["monitoring_reporting"]["uncertainty_method"] = "defined"
    data["monitoring_reporting"]["verification_ready"] = True

    # Metodologia
    data["methodology"] = {
        "standard": "Isometric",
        "pathway": "biochar",
        "production_subpathway": "standard",
        "storage_pathway": "soil",
        "durability_option": "200",
    }

    # Amostragem
    data["sampling"] = {
        "method": "A",
        "batch_definition_days": 7,
        "sampling_plan_defined": True,
    }

    # Quantificação
    data["quantification"] = {
        "input_variables": True,
        "input_uncertainties": True,
        "crediting_activity_boundaries": True,
        "storage_emissions_accounted": True,
    }

    # Caracterização do biochar
    data["biochar"] = {
        "characterization": {
            "chemical_analysis_performed": True,
            "lab_reports": True,
            "required_measurements_complete": True,
            "measurement_values": True,
            "approach_description": True,
            "ongoing_monitoring_plan": True,
        }
    }

    # Mantém compatibilidade com o schema original também
    data["biochar_characterization"]["approach_description"] = True
    data["biochar_characterization"]["ongoing_monitoring_plan"] = True

    # Rastreabilidade
    data["traceability"] = {
        "chain_of_custody_diagram": True,
    }

    # Gestão
    data["management"] = {
        "adaptive_management_plan": True,
        "monitoring_triggers": True,
    }

    # Riscos
    data["risk_assessment"] = {
        "fuel_use_reversal_risk": True,
        "mitigation_plan": True,
    }

    # Emissões
    data["emissions"] = {
        "stack_monitoring_method": "periodic_stack_testing",
        "testing_frequency": "quarterly",
    }

    # Legal
    data["legal"] = {
        "applicable_environmental_requirements": True,
        "regulatory_measurement_methods": True,
    }

    return data
