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
    
# =========================
# LOGIC REGISTRY
# =========================

LOGIC_MAP = {
    "biochar_applicability": eval_biochar_applicability,
    "reactor_definition": reactor_definition,
    "storage_pathway": storage_pathway,
    "feedstock_compliance": feedstock_compliance,
    "monitoring_system": monitoring_system,
}


