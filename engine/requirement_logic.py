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


# =========================
# LOGIC REGISTRY
# =========================

LOGIC_MAP = {
    "biochar_applicability": eval_biochar_applicability,
    "reactor_requirements": eval_reactor_requirements,
    "storage_requirements": eval_storage_requirements,
    "feedstock_requirements": eval_feedstock_requirements,
    "monitoring_requirements": eval_monitoring_requirements,
}


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

def reactor_definition(data):
    prod = data["production"]
    if prod["pyrolysis_technology"] and prod["reactor_design_diagram"] and prod["maintenance_plan"]:
        return "compliant"
    return "non_compliant"


def storage_pathway(data):
    storage = data["storage"]
    if storage["storage_environment_stable"] and storage["storage_module"] and storage["storage_monitoring_plan"]:
        return "compliant"
    return "non_compliant"


def feedstock_compliance(data):
    feed = data["feedstock"]
    if feed["biomass_type"] and feed["pre_project_biomass_use"] and feed["feedstock_accounting_module_compliance"]:
        return "compliant"
    return "non_compliant"


def monitoring_system(data):
    mon = data["monitoring_reporting"]
    if mon["monitoring_plan"] and mon["uncertainty_method"] and mon["verification_ready"]:
        return "compliant"
    return "non_compliant"
