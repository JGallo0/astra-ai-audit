# engine/requirement_logic.py

# =========================
# LOGIC FUNCTIONS
# =========================

def eval_biochar_applicability(data):
    try:
        if data["eligibility"]["net_negative_claim"] is not True:
            return "non_compliant"

        if data["eligibility"]["additionality_claim"] is not True:
            return "partial"

        if (data["eligibility"]["durability_years"] or 0) <= 200:
            return "non_compliant"

        if not data["production"]["pyrolysis_technology"]:
            return "non_compliant"

        if data["storage"]["storage_environment_stable"] is not True:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def eval_reactor_requirements(data):
    try:
        if not data["production"]["pyrolysis_technology"]:
            return "non_compliant"

        if not data["production"]["reactor_design_diagram"]:
            return "partial"

        if not data["production"]["maintenance_plan"]:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def eval_storage_requirements(data):
    try:
        if not data["storage"]["storage_module"]:
            return "non_compliant"

        if not data["storage"]["storage_location"]:
            return "partial"

        if not data["storage"]["storage_monitoring_plan"]:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def eval_feedstock_requirements(data):
    try:
        if not data["feedstock"]["biomass_type"]:
            return "non_compliant"

        if not data["feedstock"]["pre_project_biomass_use"]:
            return "partial"

        if data["feedstock"]["feedstock_accounting_module_compliance"] is not True:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def eval_monitoring_requirements(data):
    try:
        if data["monitoring_reporting"]["monitoring_plan"] is not True:
            return "non_compliant"

        if not data["monitoring_reporting"]["uncertainty_method"]:
            return "partial"

        if data["monitoring_reporting"]["verification_ready"] is not True:
            return "partial"

        return "compliant"

    except Exception:
        return "error"

def get_logic(name):
    if name not in LOGIC_MAP:
        raise ValueError(f"Logic function '{name}' not found")
    return LOGIC_MAP[name]


# =========================
# ENGINE RUNNER
# =========================

def run_engine(project_data, requirements):
    results = []

    for req in requirements:
        try:
            logic_fn = get_logic(req["logic"])
            status = logic_fn(project_data)
        except Exception:
            status = "error"

        results.append({
            "id": req.get("id"),
            "name": req.get("name"),
            "status": status,
            "logic": req.get("logic")
        })

    return results

# =========================
# ENGINE RUNNER
# =========================

def get_value(data, path):
    """
    Resolve dotted paths dentro do project_data.
    Exemplo:
        get_value(project_data, "methodology.storage_pathway")
    """
    keys = path.split(".")
    value = data

    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)

    return value


def requirement_applies(project_data, applies_if):
    """
    Avalia se um requirement é aplicável ao projeto.

    Suporta:
    1) igualdade simples
       ex: "methodology.storage_pathway": "soil"

    2) __contains
       ex: "storage.soil.deployment_methods__contains": "direct_soil_application"

    3) __contains_any
       ex: "storage.soil.deployment_methods__contains_any": ["on_site_mixing", "third_party_mixing"]
    """
    if not applies_if:
        return True

    for key, expected in applies_if.items():

        # Operador: __contains_any
        if key.endswith("__contains_any"):
            field = key.replace("__contains_any", "")
            value = get_value(project_data, field)

            if not isinstance(value, list):
                return False

            if not isinstance(expected, list):
                return False

            if not any(item in value for item in expected):
                return False

        # Operador: __contains
        elif key.endswith("__contains"):
            field = key.replace("__contains", "")
            value = get_value(project_data, field)

            if not isinstance(value, list):
                return False

            if expected not in value:
                return False

        # Igualdade simples
        else:
            value = get_value(project_data, key)

            if value != expected:
                return False

    return True


def run_engine(project_data, requirements):
    results = []

    for req in requirements:
        req_id = req.get("id")
        req_name = req.get("title") or req.get("name")
        logic_key = req.get("logic")
        applies_if = req.get("applies_if", {})
        fields_evaluated = req.get("fields", [])

        # 1) Verifica aplicabilidade
        if not requirement_applies(project_data, applies_if):
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "status": "not_applicable",
                "confidence": 1.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": ["Requirement not applicable to this project configuration."],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
            })
            continue

        # 2) Busca a função de lógica
        try:
            logic_fn = get_logic(logic_key)
        except Exception:
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "status": "error",
                "confidence": 0.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": [f"Logic function '{logic_key}' not found."],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
            })
            continue

        # 3) Executa a lógica
        try:
            status = logic_fn(project_data)
        except Exception as e:
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "status": "error",
                "confidence": 0.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": [f"Logic execution error: {str(e)}"],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
            })
            continue

        # 4) Monta saída estruturada
        if status == "compliant":
            confidence = 0.95
        elif status == "partial":
            confidence = 0.75
        elif status == "non_compliant":
            confidence = 0.90
        else:
            confidence = 0.0

        results.append({
            "requirement_id": req_id,
            "requirement_name": req_name,
            "status": status,
            "confidence": confidence,
            "missing_fields": [],
            "failed_fields": [],
            "notes": [],
            "logic_key": logic_key,
            "fields_evaluated": fields_evaluated,
        })

    return results

def reactor_design_diagram(data):
    """
    Requirement logic for:
    - R-6AQG-1 | P&ID or engineering design diagram with sensors
    """
    try:
        production = data.get("production", {})

        has_diagram = production.get("reactor_design_diagram")
        has_sensor_inventory = production.get("sensor_inventory")
        has_sensor_locations = production.get("sensor_locations")

        if not has_diagram:
            return "non_compliant"

        if not has_sensor_inventory:
            return "partial"

        if not has_sensor_locations:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def durability_option_declared(data):
    """
    Requirement logic for:
    - R-BFEE-0 | Durability option declared
    """
    try:
        methodology = data.get("methodology", {})
        durability_option = methodology.get("durability_option")

        allowed = ["200", "1000", "combined_200_1000"]

        if not durability_option:
            return "non_compliant"

        if durability_option not in allowed:
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def sampling_batch_definition(data):
    """
    Requirement logic for:
    - R-6YSW-0 | Production batch definition within allowed threshold

    Regra operacional simplificada:
    - standard: até 31 dias
    - combustion_coproduct: até 7 dias
    """
    try:
        methodology = data.get("methodology", {})
        sampling = data.get("sampling", {})

        production_subpathway = methodology.get("production_subpathway")
        batch_definition_days = sampling.get("batch_definition_days")

        if batch_definition_days is None:
            return "non_compliant"

        if production_subpathway == "combustion_coproduct":
            if batch_definition_days <= 7:
                return "compliant"
            return "non_compliant"

        # fallback para standard / outros
        if batch_definition_days <= 31:
            return "compliant"

        return "non_compliant"

    except Exception:
        return "error"


def chain_of_custody_diagram(data):
    """
    Requirement logic for:
    - R-3MYN-0 | Chain of custody diagram or equivalent provided
    """
    try:
        traceability = data.get("traceability", {})
        diagram = traceability.get("chain_of_custody_diagram")

        if not diagram:
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def biochar_chemical_analysis(data):
    """
    Requirement logic for:
    - R-6F0N-0 | Chemical analysis for biochar characterization performed
    """
    try:
        biochar = data.get("biochar", {})
        characterization = biochar.get("characterization", {})

        chemical_analysis_performed = characterization.get("chemical_analysis_performed")
        lab_reports = characterization.get("lab_reports")

        if chemical_analysis_performed is not True:
            return "non_compliant"

        if not lab_reports:
            return "partial"

        return "compliant"

    except Exception:
        return "error"

def uncertainty_inputs(data):
    """
    R-Z106-1 | Uncertainty inputs disclosed
    """
    try:
        quant = data.get("quantification", {})

        if not quant.get("input_variables"):
            return "non_compliant"

        if not quant.get("input_uncertainties"):
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def stockpiling_disclosure(data):
    """
    R-6E1D-0 | Biochar stockpiling disclosed
    """
    try:
        storage = data.get("storage", {})

        stockpiled = storage.get("stockpiled_before_end_use")
        disclosure = storage.get("stockpiling_documented")

        if stockpiled is True and not disclosure:
            return "non_compliant"

        if stockpiled is True and disclosure:
            return "compliant"

        return "compliant"

    except Exception:
        return "error"


def adaptive_management_plan(data):
    """
    R-BC4H-1 | Adaptive management plan in place
    """
    try:
        management = data.get("management", {})

        plan = management.get("adaptive_management_plan")
        triggers = management.get("monitoring_triggers")

        if not plan:
            return "non_compliant"

        if not triggers:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def feedstock_moisture_management(data):
    """
    R-NJ8G-0 | Feedstock moisture management and verification
    """
    try:
        feedstock = data.get("feedstock", {})

        moisture_control = feedstock.get("moisture_control_plan")
        moisture_measurement = feedstock.get("moisture_measurement")

        if not moisture_control:
            return "non_compliant"

        if not moisture_measurement:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def fuel_use_reversal_risk(data):
    """
    R-Z4A3-0 | Fuel-use reversal risk assessed
    """
    try:
        risk = data.get("risk_assessment", {})

        assessment = risk.get("fuel_use_reversal_risk")
        mitigation = risk.get("mitigation_plan")

        if not assessment:
            return "non_compliant"

        if not mitigation:
            return "partial"

        return "compliant"

    except Exception:
        return "error"
        
def sampling_plan_consistency(data):
    """
    R-S8K1-1 | Sampling plan consistent with Methods A/B
    """
    try:
        sampling = data.get("sampling", {})

        method = sampling.get("method")
        plan_defined = sampling.get("sampling_plan_defined")

        if not method:
            return "non_compliant"

        if method not in ["A", "B"]:
            return "non_compliant"

        if not plan_defined:
            return "partial"

        return "compliant"

    except Exception:
        return "error"    

def sampling_plan_consistency(data):
    """
    R-S8K1-1 | Sampling plan consistent with Methods A/B
    """
    try:
        sampling = data.get("sampling", {})

        method = sampling.get("method")
        plan_defined = sampling.get("sampling_plan_defined")

        if not method:
            return "non_compliant"

        if method not in ["A", "B"]:
            return "non_compliant"

        if not plan_defined:
            return "partial"

        return "compliant"

    except Exception:
        return "error"
def reactor_maintenance_plan(data):
    """
    R-19AF-1 | Reactor maintenance plan evidenced
    """
    try:
        production = data.get("production", {})

        maintenance_plan = production.get("maintenance_plan")
        maintenance_schedule = production.get("maintenance_schedule")

        if not maintenance_plan:
            return "non_compliant"

        if not maintenance_schedule:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def stack_emissions_monitoring_method(data):
    """
    R-TKNH-0 | Stack emissions monitoring method selected
    """
    try:
        emissions = data.get("emissions", {})

        method = emissions.get("stack_monitoring_method")
        frequency = emissions.get("testing_frequency")

        if not method:
            return "non_compliant"

        if not frequency:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def biochar_required_measurements(data):
    """
    R-VGXA-0 | All required physical and chemical measurements obtained or planned
    """
    try:
        biochar = data.get("biochar", {})
        characterization = biochar.get("characterization", {})

        required_complete = characterization.get("required_measurements_complete")
        measurement_values = characterization.get("measurement_values")

        if required_complete is not True:
            return "non_compliant"

        if not measurement_values:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def deployment_method_selected(data):
    """
    R-T2X2-0 | Deployment method specified
    """
    try:
        storage = data.get("storage", {})
        soil = storage.get("soil", {})

        deployment_methods = soil.get("deployment_methods")

        if not deployment_methods:
            return "non_compliant"

        if not isinstance(deployment_methods, list):
            return "non_compliant"

        if len(deployment_methods) == 0:
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def direct_soil_application_evidence(data):
    """
    R-8PBP-0 | Direct soil application evidence pathway confirmed
    """
    try:
        storage = data.get("storage", {})
        soil = storage.get("soil", {})
        deployment_methods = soil.get("deployment_methods", [])

        evidence = soil.get("direct_application_evidence_pathway")

        if "direct_soil_application" not in deployment_methods:
            return "not_applicable"

        if not evidence:
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"

def reactor_material_selection(data):
    try:
        prod = data.get("production", {})
        if not prod.get("reactor_components"):
            return "non_compliant"
        if not prod.get("material_selection_justification"):
            return "partial"
        return "compliant"
    except:
        return "error"


def engineering_design_diagram(data):
    try:
        prod = data.get("production", {})
        if not prod.get("engineering_design_diagram"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def end_material_process_description(data):
    try:
        prod = data.get("production", {})
        if not prod.get("end_material_process_description"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def crediting_activity_boundaries(data):
    try:
        quant = data.get("quantification", {})
        if not quant.get("crediting_activity_boundaries"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def storage_system_boundary(data):
    try:
        quant = data.get("quantification", {})
        if not quant.get("storage_emissions_accounted"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def environmental_legal_requirements(data):
    try:
        legal = data.get("legal", {})
        if not legal.get("applicable_environmental_requirements"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def regulatory_measurement_methods(data):
    try:
        legal = data.get("legal", {})
        if not legal.get("regulatory_measurement_methods"):
            return "non_compliant"
        return "compliant"
    except:
        return "error"


def biochar_characterization_approach(data):
    try:
        bio = data.get("biochar", {}).get("characterization", {})
        if not bio.get("approach_description"):
            return "non_compliant"
        if not bio.get("ongoing_monitoring_plan"):
            return "partial"
        return "compliant"
    except:
        return "error"

def reactor_material_selection(data):
    try:
        prod = data.get("production", {})

        components = prod.get("reactor_components")
        justification = prod.get("material_selection_justification")

        if not components:
            return "non_compliant"

        if not justification:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def engineering_design_diagram(data):
    try:
        prod = data.get("production", {})

        if not prod.get("engineering_design_diagram"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def end_material_process_description(data):
    try:
        prod = data.get("production", {})

        if not prod.get("end_material_process_description"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def crediting_activity_boundaries(data):
    try:
        quant = data.get("quantification", {})

        if not quant.get("crediting_activity_boundaries"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def storage_system_boundary(data):
    try:
        quant = data.get("quantification", {})

        if not quant.get("storage_emissions_accounted"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"

def environmental_legal_requirements(data):
    try:
        legal = data.get("legal", {})

        if not legal.get("applicable_environmental_requirements"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def regulatory_measurement_methods(data):
    try:
        legal = data.get("legal", {})

        if not legal.get("regulatory_measurement_methods"):
            return "non_compliant"

        return "compliant"

    except Exception:
        return "error"


def biochar_characterization_approach(data):
    try:
        bio = data.get("biochar", {}).get("characterization", {})

        if not bio.get("approach_description"):
            return "non_compliant"

        if not bio.get("ongoing_monitoring_plan"):
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def product_standard_compliance(data):
    try:
        product = data.get("product", {})

        standard = product.get("standard_compliance")
        certification = product.get("certification_scheme")

        if not standard:
            return "non_compliant"

        if not certification:
            return "partial"

        return "compliant"

    except Exception:
        return "error"


def contaminant_monitoring_plan(data):
    try:
        bio = data.get("biochar", {}).get("characterization", {})

        contaminants = bio.get("contaminant_testing")
        frequency = bio.get("contaminant_testing_frequency")

        if not contaminants:
            return "non_compliant"

        if not frequency:
            return "partial"

        return "compliant"

    except Exception:
        return "error"
        
# =========================
# LOGIC REGISTRY
# =========================

LOGIC_MAP = {
    "biochar_applicability": eval_biochar_applicability,
    "reactor_definition": eval_reactor_requirements,
    "storage_pathway": eval_storage_requirements,
    "feedstock_compliance": eval_feedstock_requirements,
    "monitoring_system": eval_monitoring_requirements,

    "reactor_design_diagram": reactor_design_diagram,
    "durability_option_declared": durability_option_declared,
    "sampling_batch_definition": sampling_batch_definition,
    "chain_of_custody_diagram": chain_of_custody_diagram,
    "biochar_chemical_analysis": biochar_chemical_analysis,

    "uncertainty_inputs": uncertainty_inputs,
    "stockpiling_disclosure": stockpiling_disclosure,
    "adaptive_management_plan": adaptive_management_plan,
    "feedstock_moisture_management": feedstock_moisture_management,
    "fuel_use_reversal_risk": fuel_use_reversal_risk,
    "sampling_plan_consistency": sampling_plan_consistency,

    "reactor_maintenance_plan": reactor_maintenance_plan,
    "stack_emissions_monitoring_method": stack_emissions_monitoring_method,
    "biochar_required_measurements": biochar_required_measurements,
    "deployment_method_selected": deployment_method_selected,
    "direct_soil_application_evidence": direct_soil_application_evidence,

    "reactor_material_selection": reactor_material_selection,
    "engineering_design_diagram": engineering_design_diagram,
    "end_material_process_description": end_material_process_description,
    "crediting_activity_boundaries": crediting_activity_boundaries,
    "storage_system_boundary": storage_system_boundary,
    
    "environmental_legal_requirements": environmental_legal_requirements,
    "regulatory_measurement_methods": regulatory_measurement_methods,
    "biochar_characterization_approach": biochar_characterization_approach,

    "reactor_material_selection": reactor_material_selection,
    "engineering_design_diagram": engineering_design_diagram,
    "end_material_process_description": end_material_process_description,
    "crediting_activity_boundaries": crediting_activity_boundaries,
    "storage_system_boundary": storage_system_boundary,

    "environmental_legal_requirements": environmental_legal_requirements,
    "regulatory_measurement_methods": regulatory_measurement_methods,
    "biochar_characterization_approach": biochar_characterization_approach,
    "product_standard_compliance": product_standard_compliance,
    "contaminant_monitoring_plan": contaminant_monitoring_plan,
    
}
