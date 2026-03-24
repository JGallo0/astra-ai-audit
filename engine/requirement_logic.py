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

def build_logic_result(
    status,
    missing_fields=None,
    failed_fields=None,
    notes=None,
):
    return {
        "status": status,
        "missing_fields": missing_fields or [],
        "failed_fields": failed_fields or [],
        "notes": notes or [],
    }

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
            logic_output = logic_fn(project_data)
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

        # Aceita formato antigo (string) e novo (dict)
        if isinstance(logic_output, dict):
            status = logic_output.get("status", "error")
            missing_fields = logic_output.get("missing_fields", [])
            failed_fields = logic_output.get("failed_fields", [])
            notes = logic_output.get("notes", [])
        else:
            status = logic_output
            missing_fields = []
            failed_fields = []
            notes = []

        # 4) Monta saída estruturada
        if status == "compliant":
            confidence = 0.95
        elif status == "partial":
            confidence = 0.75
        elif status == "non_compliant":
            confidence = 0.90
        elif status == "not_applicable":
            confidence = 1.0
        else:
            confidence = 0.0

        results.append({
            "requirement_id": req_id,
            "requirement_name": req_name,
            "status": status,
            "confidence": confidence,
            "missing_fields": missing_fields,
            "failed_fields": failed_fields,
            "notes": notes,
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

        missing_fields = []
        failed_fields = []
        notes = []

        has_diagram = production.get("reactor_design_diagram")
        has_sensor_inventory = production.get("sensor_inventory")
        has_sensor_locations = production.get("sensor_locations")

        if not has_diagram:
            missing_fields.append("production.reactor_design_diagram")
            notes.append("Reactor design diagram or P&ID is missing.")

        if not has_sensor_inventory:
            missing_fields.append("production.sensor_inventory")
            notes.append("Sensor inventory is missing.")

        if not has_sensor_locations:
            missing_fields.append("production.sensor_locations")
            notes.append("Sensor locations are missing.")

        if missing_fields:
            status = "non_compliant" if "production.reactor_design_diagram" in missing_fields else "partial"
            return build_logic_result(
                status=status,
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Reactor design diagram and sensor documentation are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_design_diagram execution error: {str(e)}"],
        )


def durability_option_declared(data):
    """
    R-BFEE-0 | Durability option declared
    """
    try:
        methodology = data.get("methodology", {})

        missing_fields = []
        failed_fields = []
        notes = []

        durability_option = methodology.get("durability_option")
        allowed = ["200", "1000", "combined_200_1000"]

        if not durability_option:
            missing_fields.append("methodology.durability_option")
            notes.append("Durability option is not declared.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if durability_option not in allowed:
            failed_fields.append("methodology.durability_option")
            notes.append("Durability option must be one of: 200, 1000, combined_200_1000.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=[f"Durability option declared as '{durability_option}'."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"durability_option_declared execution error: {str(e)}"],
        )


def sampling_batch_definition(data):
    """
    R-6YSW-0 | Production batch definition within allowed threshold
    """
    try:
        methodology = data.get("methodology", {})
        sampling = data.get("sampling", {})

        missing_fields = []
        failed_fields = []
        notes = []

        production_subpathway = methodology.get("production_subpathway")
        batch_definition_days = sampling.get("batch_definition_days")

        if batch_definition_days is None:
            missing_fields.append("sampling.batch_definition_days")
            notes.append("Batch definition in days is not provided.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if production_subpathway == "combustion_coproduct":
            if batch_definition_days > 7:
                failed_fields.append("sampling.batch_definition_days")
                notes.append("Combustion co-product systems must define batches within 7 days.")
                return build_logic_result(
                    status="non_compliant",
                    missing_fields=missing_fields,
                    failed_fields=failed_fields,
                    notes=notes,
                )

            return build_logic_result(
                status="compliant",
                notes=["Batch definition is within the 7-day threshold for combustion co-product systems."],
            )

        if batch_definition_days > 31:
            failed_fields.append("sampling.batch_definition_days")
            notes.append("Production batch definition exceeds the 31-day threshold.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Batch definition is within the allowed threshold."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"sampling_batch_definition execution error: {str(e)}"],
        )

def chain_of_custody_diagram(data):
    """
    R-3MYN-0 | Chain of custody diagram or equivalent provided
    """
    try:
        traceability = data.get("traceability", {})

        missing_fields = []
        failed_fields = []
        notes = []

        diagram = traceability.get("chain_of_custody_diagram")

        if not diagram:
            missing_fields.append("traceability.chain_of_custody_diagram")
            notes.append("Chain of custody diagram or equivalent evidence is missing.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Chain of custody diagram is present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"chain_of_custody_diagram execution error: {str(e)}"],
        )

def biochar_chemical_analysis(data):
    """
    R-6F0N-0 | Chemical analysis for biochar characterization performed
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        missing_fields = []
        failed_fields = []
        notes = []

        chemical_analysis_performed = characterization.get("chemical_analysis_performed")
        lab_reports = characterization.get("lab_reports")

        if chemical_analysis_performed is not True:
            missing_fields.append("biochar.characterization.chemical_analysis_performed")
            notes.append("Chemical analysis for biochar characterization is not evidenced.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not lab_reports:
            missing_fields.append("biochar.characterization.lab_reports")
            notes.append("Lab reports supporting chemical analysis are missing.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Chemical analysis and supporting lab reports are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_chemical_analysis execution error: {str(e)}"],
        )

def uncertainty_inputs(data):
    """
    R-Z106-1 | Uncertainty inputs disclosed
    """
    try:
        quant = data.get("quantification", {})

        missing_fields = []
        failed_fields = []
        notes = []

        input_variables = quant.get("input_variables")
        input_uncertainties = quant.get("input_uncertainties")

        if not input_variables:
            missing_fields.append("quantification.input_variables")
            notes.append("Input variables used in quantification are not disclosed.")

        if not input_uncertainties:
            missing_fields.append("quantification.input_uncertainties")
            notes.append("Input uncertainties are not disclosed.")

        if "quantification.input_variables" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Input variables and uncertainties are disclosed."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"uncertainty_inputs execution error: {str(e)}"],
        )


def stockpiling_disclosure(data):
    """
    R-6E1D-0 | Biochar stockpiling disclosed
    """
    try:
        storage = data.get("storage", {})

        missing_fields = []
        failed_fields = []
        notes = []

        stockpiled = storage.get("stockpiled_before_end_use")
        disclosure = storage.get("stockpiling_documented")

        if stockpiled is None:
            missing_fields.append("storage.stockpiled_before_end_use")
            notes.append("Stockpiling status before end use is not defined.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if stockpiled is True and not disclosure:
            missing_fields.append("storage.stockpiling_documented")
            notes.append("Stockpiling occurs before end use but is not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if stockpiled is True and disclosure:
            return build_logic_result(
                status="compliant",
                notes=["Stockpiling before end use is documented."],
            )

        return build_logic_result(
            status="compliant",
            notes=["No stockpiling before end use is reported."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"stockpiling_disclosure execution error: {str(e)}"],
        )

def adaptive_management_plan(data):
    """
    R-BC4H-1 | Adaptive management plan in place
    """
    try:
        management = data.get("management", {})

        missing_fields = []
        failed_fields = []
        notes = []

        plan = management.get("adaptive_management_plan")
        triggers = management.get("monitoring_triggers")

        if not plan:
            missing_fields.append("management.adaptive_management_plan")
            notes.append("Adaptive management plan is missing.")

        if not triggers:
            missing_fields.append("management.monitoring_triggers")
            notes.append("Monitoring triggers for adaptive management are missing.")

        if "management.adaptive_management_plan" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Adaptive management plan and monitoring triggers are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"adaptive_management_plan execution error: {str(e)}"],
        )

def feedstock_moisture_management(data):
    """
    R-NJ8G-0 | Feedstock moisture management and verification
    """
    try:
        feedstock = data.get("feedstock", {})

        missing_fields = []
        failed_fields = []
        notes = []

        moisture_control = feedstock.get("moisture_control_plan")
        moisture_measurement = feedstock.get("moisture_measurement")

        if not moisture_control:
            missing_fields.append("feedstock.moisture_control_plan")
            notes.append("Feedstock moisture control plan is missing.")

        if not moisture_measurement:
            missing_fields.append("feedstock.moisture_measurement")
            notes.append("Feedstock moisture measurement method is missing.")

        if "feedstock.moisture_control_plan" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Feedstock moisture control and measurement are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"feedstock_moisture_management execution error: {str(e)}"],
        )


def fuel_use_reversal_risk(data):
    """
    R-Z4A3-0 | Fuel-use reversal risk assessed
    """
    try:
        risk = data.get("risk_assessment", {})

        missing_fields = []
        failed_fields = []
        notes = []

        assessment = risk.get("fuel_use_reversal_risk")
        mitigation = risk.get("mitigation_plan")

        if not assessment:
            missing_fields.append("risk_assessment.fuel_use_reversal_risk")
            notes.append("Fuel-use reversal risk assessment is missing.")

        if not mitigation:
            missing_fields.append("risk_assessment.mitigation_plan")
            notes.append("Mitigation plan for fuel-use reversal risk is missing.")

        if "risk_assessment.fuel_use_reversal_risk" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Fuel-use reversal risk assessment and mitigation plan are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"fuel_use_reversal_risk execution error: {str(e)}"],
        )
        
def sampling_plan_consistency(data):
    """
    R-S8K1-1 | Sampling plan consistent with Methods A/B
    """
    try:
        sampling = data.get("sampling", {})

        missing_fields = []
        failed_fields = []
        notes = []

        method = sampling.get("method")
        plan_defined = sampling.get("sampling_plan_defined")

        if not method:
            missing_fields.append("sampling.method")
        elif method not in ["A", "B"]:
            failed_fields.append("sampling.method")
            notes.append("Sampling method must be 'A' or 'B'.")

        if not plan_defined:
            missing_fields.append("sampling.sampling_plan_defined")
            notes.append("Sampling plan is not documented.")

        if failed_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Sampling method and plan are defined."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"sampling_plan_consistency execution error: {str(e)}"],
        )
        
def reactor_maintenance_plan(data):
    """
    R-19AF-1 | Reactor maintenance plan evidenced
    """
    try:
        production = data.get("production", {})

        missing_fields = []
        failed_fields = []
        notes = []

        maintenance_plan = production.get("maintenance_plan")
        maintenance_schedule = production.get("maintenance_schedule")

        if not maintenance_plan:
            missing_fields.append("production.maintenance_plan")
            notes.append("Maintenance plan is missing.")

        if not maintenance_schedule:
            missing_fields.append("production.maintenance_schedule")
            notes.append("Maintenance schedule is missing.")

        if "production.maintenance_plan" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Maintenance plan and schedule are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_maintenance_plan execution error: {str(e)}"],
        )

def stack_emissions_monitoring_method(data):
    """
    R-TKNH-0 | Stack emissions monitoring method selected
    """
    try:
        emissions = data.get("emissions", {})

        missing_fields = []
        failed_fields = []
        notes = []

        method = emissions.get("stack_monitoring_method")
        frequency = emissions.get("testing_frequency")

        if not method:
            missing_fields.append("emissions.stack_monitoring_method")
            notes.append("Stack emissions monitoring method is missing.")

        if not frequency:
            missing_fields.append("emissions.testing_frequency")
            notes.append("Testing frequency for stack emissions is missing.")

        if "emissions.stack_monitoring_method" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Stack emissions monitoring method and frequency are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"stack_emissions_monitoring_method execution error: {str(e)}"],
        )

def biochar_required_measurements(data):
    """
    R-VGXA-0 | All required physical and chemical measurements obtained or planned
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        missing_fields = []
        failed_fields = []
        notes = []

        required_complete = characterization.get("required_measurements_complete")
        measurement_values = characterization.get("measurement_values")

        if required_complete is not True:
            missing_fields.append("biochar.characterization.required_measurements_complete")
            notes.append("Required physical and chemical measurements are not complete.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not measurement_values:
            missing_fields.append("biochar.characterization.measurement_values")
            notes.append("Measurement values are missing.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Required measurements and measurement values are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_required_measurements execution error: {str(e)}"],
        )


def deployment_method_selected(data):
    """
    R-T2X2-0 | Deployment method specified
    """
    try:
        soil = data.get("storage", {}).get("soil", {})

        missing_fields = []
        failed_fields = []
        notes = []

        deployment_methods = soil.get("deployment_methods")

        if not deployment_methods:
            missing_fields.append("storage.soil.deployment_methods")
            notes.append("No deployment method is specified.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not isinstance(deployment_methods, list):
            failed_fields.append("storage.soil.deployment_methods")
            notes.append("Deployment methods must be a list.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if len(deployment_methods) == 0:
            missing_fields.append("storage.soil.deployment_methods")
            notes.append("Deployment methods list is empty.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Deployment method is specified."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"deployment_method_selected execution error: {str(e)}"],
        )


def direct_soil_application_evidence(data):
    """
    R-8PBP-0 | Direct soil application evidence pathway confirmed
    """
    try:
        soil = data.get("storage", {}).get("soil", {})

        missing_fields = []
        failed_fields = []
        notes = []

        deployment_methods = soil.get("deployment_methods", [])
        evidence = soil.get("direct_application_evidence_pathway")

        if "direct_soil_application" not in deployment_methods:
            return build_logic_result(
                status="not_applicable",
                notes=["Direct soil application is not part of the deployment pathway."],
            )

        if not evidence:
            missing_fields.append("storage.soil.direct_application_evidence_pathway")
            notes.append("Evidence for direct soil application pathway is missing.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Direct soil application evidence pathway is documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"direct_soil_application_evidence execution error: {str(e)}"],
        )
def reactor_material_selection(data):
    """
    R-DMET-0 | Reactor material selection justified
    """
    try:
        production = data.get("production", {})

        missing_fields = []
        failed_fields = []
        notes = []

        components = production.get("reactor_components")
        justification = production.get("material_selection_justification")

        if not components:
            missing_fields.append("production.reactor_components")
            notes.append("Reactor components are not described.")

        if not justification:
            missing_fields.append("production.material_selection_justification")
            notes.append("Material selection justification is missing.")

        if "production.reactor_components" in missing_fields:
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if missing_fields:
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Reactor components and material selection justification are present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_material_selection execution error: {str(e)}"],
        )



def end_material_process_description(data):
    """
    R-V04V-0 | End material production process described in detail
    """
    try:
        production = data.get("production", {})

        missing_fields = []
        failed_fields = []
        notes = []

        description = production.get("end_material_process_description")

        if not description:
            missing_fields.append("production.end_material_process_description")
            notes.append("End material production process description is missing.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["End material production process is described."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"end_material_process_description execution error: {str(e)}"],
        )


def environmental_legal_requirements(data):
    """
    R-52YX-0 | Applicable environmental legal requirements provided
    """
    try:
        legal = data.get("legal", {})

        missing_fields = []
        failed_fields = []
        notes = []

        requirements = legal.get("applicable_environmental_requirements")

        if not requirements:
            missing_fields.append("legal.applicable_environmental_requirements")
            notes.append("Applicable environmental legal requirements are not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Applicable environmental legal requirements are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"environmental_legal_requirements execution error: {str(e)}"],
        )


def regulatory_measurement_methods(data):
    """
    R-RQTJ-0 | Regulatory measurements approach described
    """
    try:
        legal = data.get("legal", {})

        missing_fields = []
        failed_fields = []
        notes = []

        methods = legal.get("regulatory_measurement_methods")

        if not methods:
            missing_fields.append("legal.regulatory_measurement_methods")
            notes.append("Regulatory measurement methods are not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Regulatory measurement methods are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"regulatory_measurement_methods execution error: {str(e)}"],
        )

def biochar_characterization_approach(data):
    """
    R-NYQT-0 | Biochar characterization and ongoing monitoring approach described
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        missing_fields = []
        failed_fields = []
        notes = []

        approach_description = characterization.get("approach_description")
        ongoing_monitoring_plan = characterization.get("ongoing_monitoring_plan")

        if not approach_description:
            missing_fields.append("biochar.characterization.approach_description")
            notes.append("Biochar characterization approach is not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not ongoing_monitoring_plan:
            missing_fields.append("biochar.characterization.ongoing_monitoring_plan")
            notes.append("Ongoing monitoring plan for biochar characterization is missing.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Biochar characterization approach and monitoring plan are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_characterization_approach execution error: {str(e)}"],
        )


def engineering_design_diagram(data):
    """
    R-29W5-0 | Engineering design diagram provided
    """
    try:
        production = data.get("production", {})

        missing_fields = []
        failed_fields = []
        notes = []

        diagram = production.get("engineering_design_diagram")

        if not diagram:
            missing_fields.append("production.engineering_design_diagram")
            notes.append("Engineering design diagram is missing.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Engineering design diagram is present."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"engineering_design_diagram execution error: {str(e)}"],
        )


def crediting_activity_boundaries(data):
    """
    R-KPDH-0 | Crediting activity boundaries described in detail
    """
    try:
        quant = data.get("quantification", {})

        missing_fields = []
        failed_fields = []
        notes = []

        boundaries = quant.get("crediting_activity_boundaries")

        if not boundaries:
            missing_fields.append("quantification.crediting_activity_boundaries")
            notes.append("Crediting activity boundaries are not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Crediting activity boundaries are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"crediting_activity_boundaries execution error: {str(e)}"],
        )


def storage_system_boundary(data):
    """
    R-CCP7-0 | Storage emissions fully included in system boundary
    """
    try:
        quant = data.get("quantification", {})

        missing_fields = []
        failed_fields = []
        notes = []

        storage_emissions_accounted = quant.get("storage_emissions_accounted")

        if not storage_emissions_accounted:
            missing_fields.append("quantification.storage_emissions_accounted")
            notes.append("Storage emissions are not accounted for in the system boundary.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Storage emissions are included in the system boundary."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"storage_system_boundary execution error: {str(e)}"],
        )

def product_standard_compliance(data):
    """
    R-9KKF-0 | Compliance with relevant product standards evidenced
    """
    try:
        product = data.get("product", {})

        missing_fields = []
        failed_fields = []
        notes = []

        standard = product.get("standard_compliance")
        certification = product.get("certification_scheme")

        if not standard:
            missing_fields.append("product.standard_compliance")
            notes.append("Compliance with relevant product standards is not evidenced.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not certification:
            missing_fields.append("product.certification_scheme")
            notes.append("Certification scheme or reference standard is missing.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Product standard compliance and certification scheme are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"product_standard_compliance execution error: {str(e)}"],
        )


def contaminant_monitoring_plan(data):
    """
    R-HE38-0 | Contaminant monitoring plan specified
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        missing_fields = []
        failed_fields = []
        notes = []

        contaminants = characterization.get("contaminant_testing")
        frequency = characterization.get("contaminant_testing_frequency")

        if not contaminants:
            missing_fields.append("biochar.characterization.contaminant_testing")
            notes.append("Contaminant testing is not documented.")
            return build_logic_result(
                status="non_compliant",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        if not frequency:
            missing_fields.append("biochar.characterization.contaminant_testing_frequency")
            notes.append("Contaminant testing frequency is missing.")
            return build_logic_result(
                status="partial",
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
            )

        return build_logic_result(
            status="compliant",
            notes=["Contaminant testing and frequency are documented."],
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"contaminant_monitoring_plan execution error: {str(e)}"],
        )
        
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
    "product_standard_compliance": product_standard_compliance,
    "contaminant_monitoring_plan": contaminant_monitoring_plan,
}
