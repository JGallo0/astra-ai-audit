# engine/requirement_logic.py

# =========================
# LOGIC FUNCTIONS
# =========================

def eval_biochar_applicability(data):
    """
    Determines whether the project qualifies as a biochar CDR activity
    """
    try:
        eligibility = data.get("eligibility", {})
        production = data.get("production", {})
        storage = data.get("storage", {})

        net_negative = eligibility.get("net_negative_claim")
        additionality = eligibility.get("additionality_claim")
        durability_years = eligibility.get("durability_years")
        pyrolysis_tech = production.get("pyrolysis_technology")
        storage_stable = storage.get("storage_environment_stable")

        field_scores = [
            score_boolean_field(
                "eligibility.net_negative_claim",
                net_negative,
                25,
                note_if_missing="Project does not demonstrate net-negative emissions.",
            ),
            score_boolean_field(
                "eligibility.additionality_claim",
                additionality,
                20,
                note_if_missing="Additionality is not demonstrated.",
            ),
            {
                "path": "eligibility.durability_years",
                "weight": 25,
                "score": 25 if (durability_years or 0) >= 200 else 0,
                "status": "pass" if (durability_years or 0) >= 200 else "fail",
                "notes": [] if (durability_years or 0) >= 200 else ["Durability must be at least 200 years."],
            },
            score_presence_field(
                "production.pyrolysis_technology",
                pyrolysis_tech,
                15,
                note_if_missing="Pyrolysis technology is not defined.",
            ),
            score_boolean_field(
                "storage.storage_environment_stable",
                storage_stable,
                15,
                note_if_missing="Storage environment stability is not demonstrated.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = (
            net_negative is not True
            or (durability_years or 0) < 200
            or not pyrolysis_tech
        )

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=60,
            compliant_threshold=100,
        )

        missing_fields = [i["path"] for i in field_scores if i["status"] == "missing"]
        failed_fields = [i["path"] for i in field_scores if i["status"] == "fail"]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Project meets core eligibility criteria for biochar carbon removal.")
        elif status == "partial":
            notes.append("Core eligibility is partially evidenced but still contains material gaps.")
        elif status == "non_compliant" and not notes:
            notes.append("Core eligibility is not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_biochar_applicability execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def eval_reactor_requirements(data):
    """
    Ensures reactor system and monitoring are properly defined
    """
    try:
        production = data.get("production", {})

        pyrolysis = production.get("pyrolysis_technology")
        diagram = production.get("reactor_design_diagram")
        sensors = production.get("sensor_inventory")

        field_scores = [
            score_presence_field(
                "production.pyrolysis_technology",
                pyrolysis,
                40,
                note_if_missing="Pyrolysis technology is not defined.",
            ),
            score_boolean_field(
                "production.reactor_design_diagram",
                diagram,
                30,
                note_if_missing="Reactor design diagram is missing.",
            ),
            score_boolean_field(
                "production.sensor_inventory",
                sensors,
                30,
                note_if_missing="Sensor inventory is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not pyrolysis:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_reactor_requirements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def eval_storage_requirements(data):
    try:
        storage = data.get("storage", {})
        methodology = data.get("methodology", {})

        storage_module = storage.get("storage_module")

        # Nível 1: inferir storage_module a partir de storage_pathway quando não extraído
        # Ex: methodology.storage_pathway = "soil" → storage_module = "soil"
        if not storage_module:
            storage_pathway = methodology.get("storage_pathway")
            if storage_pathway:
                storage_module = storage_pathway

        storage_location = storage.get("storage_location")
        storage_monitoring_plan = storage.get("storage_monitoring_plan")

        field_scores = [
            score_presence_field(
                "storage.storage_module",
                storage_module,
                50,
                note_if_missing="Storage module is not defined.",
            ),
            score_presence_field(
                "storage.storage_location",
                storage_location,
                25,
                note_if_missing="Storage location is not defined.",
            ),
            score_boolean_field(
                "storage.storage_monitoring_plan",
                storage_monitoring_plan,
                25,
                note_if_missing="Storage monitoring plan is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        # Nível 1: removido hard_fail gate — ausência de storage_module por falha de
        # extração não deve invalidar projeto que documenta storage_pathway
        status = derive_requirement_status_from_score(
            requirement_score,
            non_compliant_threshold=30,
            compliant_threshold=85,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Storage module, location, and monitoring plan are sufficiently evidenced.")
        elif status == "partial":
            notes.append("Storage framework is partially evidenced but remains incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("Storage requirements are not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_storage_requirements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
        
def eval_feedstock_requirements(data):
    try:
        feedstock = data.get("feedstock", {})

        biomass_type = feedstock.get("biomass_type")
        pre_project_biomass_use = feedstock.get("pre_project_biomass_use")
        accounting_compliance = feedstock.get("feedstock_accounting_module_compliance")

        field_scores = [
            score_presence_field(
                "feedstock.biomass_type",
                biomass_type,
                50,
                note_if_missing="Biomass/feedstock type is not defined.",
            ),
            score_presence_field(
                "feedstock.pre_project_biomass_use",
                pre_project_biomass_use,
                20,
                note_if_missing="Pre-project biomass use is not defined.",
            ),
            score_boolean_field(
                "feedstock.feedstock_accounting_module_compliance",
                accounting_compliance,
                30,
                note_if_missing="Feedstock accounting module compliance is not evidenced.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not biomass_type:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Feedstock type, pre-project use, and accounting module compliance are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_feedstock_requirements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def eval_monitoring_requirements(data):
    try:
        monitoring = data.get("monitoring_reporting", {})

        monitoring_plan = monitoring.get("monitoring_plan")
        uncertainty_method = monitoring.get("uncertainty_method")
        verification_ready = monitoring.get("verification_ready")

        field_scores = [
            score_boolean_field(
                "monitoring_reporting.monitoring_plan",
                monitoring_plan,
                60,
                note_if_missing="Monitoring plan is missing.",
            ),
            score_presence_field(
                "monitoring_reporting.uncertainty_method",
                uncertainty_method,
                15,
                note_if_missing="Uncertainty method is missing.",
            ),
            score_boolean_field(
                "monitoring_reporting.verification_ready",
                verification_ready,
                25,
                note_if_missing="Verification readiness is not evidenced.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = monitoring_plan is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=60,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Monitoring plan, uncertainty method, and verification readiness are sufficiently evidenced.")
        elif status == "partial":
            notes.append("Monitoring framework is partially evidenced but still incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("Monitoring requirements are not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_monitoring_requirements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

# =========================
# ENGINE RUNNER
# =========================

def build_logic_result(
    status,
    missing_fields=None,
    failed_fields=None,
    notes=None,
    requirement_score=None,
    field_scores=None,
    requirement_rating=None,
    gap=None,
    recommendation=None,
):
    return {
        "status": status,
        "missing_fields": missing_fields or [],
        "failed_fields": failed_fields or [],
        "notes": notes or [],
        "requirement_score": requirement_score,
        "field_scores": field_scores or [],
        "requirement_rating": requirement_rating,
        # v1: gap e recommendation podem ser definidos pela função de lógica
        # run_engine usa esses valores se presentes, senão gera os genéricos
        "_gap_override": gap,
        "_recommendation_override": recommendation,
    }

def score_boolean_field(
    path,
    value,
    weight,
    *,
    note_if_missing=None,
):
    if value is True:
        return {
            "path": path,
            "weight": weight,
            "score": weight,
            "status": "pass",
            "notes": [],
        }

    if value in [False, None]:
        status = "missing" if value is None else "fail"
        notes = [note_if_missing] if note_if_missing else []
        return {
            "path": path,
            "weight": weight,
            "score": 0,
            "status": status,
            "notes": notes,
        }

    return {
        "path": path,
        "weight": weight,
        "score": 0,
        "status": "fail",
        "notes": [f"Unexpected value for {path}: {value}"],
    }


def score_presence_field(
    path,
    value,
    weight,
    *,
    note_if_missing=None,
):
    has_value = value not in [None, "", [], {}]

    if has_value:
        return {
            "path": path,
            "weight": weight,
            "score": weight,
            "status": "pass",
            "notes": [],
        }

    notes = [note_if_missing] if note_if_missing else []

    return {
        "path": path,
        "weight": weight,
        "score": 0,
        "status": "missing",
        "notes": notes,
    }


def summarize_field_scores(field_scores):
    total_weight = sum(item.get("weight", 0) for item in field_scores)
    earned_score = sum(item.get("score", 0) for item in field_scores)

    if total_weight <= 0:
        return 0

    return round((earned_score / total_weight) * 100, 2)


def derive_requirement_status_from_score(
    requirement_score,
    *,
    non_compliant_threshold=50,
    compliant_threshold=100,
):
    if requirement_score >= compliant_threshold:
        return "compliant"

    if requirement_score < non_compliant_threshold:
        return "non_compliant"

    return "partial"

def derive_status_with_hard_gate(
    requirement_score,
    *,
    hard_fail: bool = False,
    hard_partial: bool = False,
    non_compliant_threshold=50,
    compliant_threshold=100,
):
    if hard_fail:
        return "non_compliant"

    if hard_partial:
        return "partial"

    return derive_requirement_status_from_score(
        requirement_score,
        non_compliant_threshold=non_compliant_threshold,
        compliant_threshold=compliant_threshold,
    )

def derive_requirement_rating(requirement_score):
    if requirement_score >= 90:
        return "strong"
    if requirement_score >= 75:
        return "good"
    if requirement_score >= 50:
        return "moderate"
    return "weak"


def collect_field_score_notes(field_scores):
    notes = []

    for item in field_scores:
        notes.extend(item.get("notes", []))

    return notes

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

def get_logic(logic_key):
    if not logic_key:
        raise KeyError("Missing logic key")

    from engine.logic_registry import LOGIC_REGISTRY

    logic_fn = LOGIC_REGISTRY.get(logic_key)
    if logic_fn is None:
        raise KeyError(f"Logic function '{logic_key}' not found.")
    return logic_fn


def run_core_cross_checks(project_data):
    """Verifica consistências cruzadas entre campos do projeto.
    Retorna lista de findings, cada um com 'paths' e 'message'.
    Implementação futura — retorna lista vazia por ora."""
    return []


def compute_confidence_from_field_scores(status, field_scores):
    """Estima confiança da avaliação com base nos field_scores e status."""
    if not field_scores:
        base = {"compliant": 0.85, "partial": 0.55, "non_compliant": 0.70,
                "not_applicable": 1.0, "error": 0.20}.get(status, 0.30)
        return base
    scores = [f.get("score", 0) for f in field_scores if isinstance(f, dict)]
    if not scores:
        return 0.30
    avg = sum(scores) / len(scores)
    return round(min(max(avg / 100.0, 0.0), 1.0), 4)


def classify_evidence_strength(field_scores):
    """Classifica a força da evidência com base nos field_scores."""
    if not field_scores:
        return "none"
    scores = [f.get("score", 0) for f in field_scores if isinstance(f, dict)]
    if not scores:
        return "none"
    avg = sum(scores) / len(scores)
    if avg >= 80:
        return "strong"
    if avg >= 55:
        return "moderate"
    if avg >= 25:
        return "weak"
    return "insufficient"


def apply_inference_rules(project_data: dict) -> dict:
    """
    Nível 2: preenche campos ausentes (None / []) com base em evidências
    relacionadas. Nunca sobrescreve valores já definidos (True/False explícito).
    Retorna uma cópia — não muta o project_data original.
    """
    import copy
    data = copy.deepcopy(project_data)

    eligibility = data.setdefault("eligibility", {})
    feedstock   = data.setdefault("feedstock", {})
    storage     = data.setdefault("storage", {})
    methodology = data.setdefault("methodology", {})
    production  = data.setdefault("production", {})
    emissions   = data.setdefault("emissions", {})
    em_testing  = data.setdefault("emissions_testing", {})
    biochar_c   = data.setdefault("biochar", {}).setdefault("characterization", {})
    safeguards  = data.setdefault("safeguards", {})
    management  = data.setdefault("management", {})
    quant       = data.setdefault("quantification", {})
    ghg         = data.setdefault("ghg_accounting", {})

    # 1. net_negative_claim — permanência + adicionalidade implica remoção líquida negativa
    if eligibility.get("net_negative_claim") is None:
        if eligibility.get("permanence_claim") is True and eligibility.get("additionality_claim") is True:
            eligibility["net_negative_claim"] = True

    # 2. storage_module — storage_pathway identifica o módulo de armazenamento
    if not storage.get("storage_module"):
        pathway = methodology.get("storage_pathway")
        if pathway:
            storage["storage_module"] = pathway

    # 3. emissions_testing.regular_testing — frequência/método documentados = testagem regular
    if em_testing.get("regular_testing") is not True:
        if emissions.get("testing_frequency") or emissions.get("stack_monitoring_method"):
            em_testing["regular_testing"] = True

    # 4. biochar.characterization.required_measurements_complete — lab_reports + measurement_values
    if biochar_c.get("required_measurements_complete") is None:
        if biochar_c.get("lab_reports") is True and biochar_c.get("measurement_values") is True:
            biochar_c["required_measurements_complete"] = True

    # 5. safeguards.adaptive_management_plan — propagado de management (mesmo plano)
    if safeguards.get("adaptive_management_plan") is not True:
        if management.get("adaptive_management_plan") is True:
            safeguards["adaptive_management_plan"] = True

    # 6. feedstock.source_locations — biomass_type + certificação implicam origem rastreável
    if not feedstock.get("source_locations"):
        if feedstock.get("biomass_type") and feedstock.get("certification_scheme"):
            feedstock["source_locations"] = [
                f"Certified supply ({feedstock['certification_scheme']})"
            ]

    # 7. quantification.lca_performed — sistema GHG completo equivale a ACV realizada
    if quant.get("lca_performed") is None:
        if (quant.get("input_variables") is True
                and quant.get("input_uncertainties") is True
                and ghg.get("system_boundary_defined") is True):
            quant["lca_performed"] = True

    # 8. storage.soil.deployment_methods — storage_pathway "soil" implica aplicação ao solo
    storage_soil = storage.setdefault("soil", {})
    if not storage_soil.get("deployment_methods"):
        if methodology.get("storage_pathway") == "soil":
            storage_soil["deployment_methods"] = "soil_application"

    # 9. traceability.chain_of_custody_diagram — inferir apenas quando None (não extraído)
    # Certificação de sustentabilidade implica rastreabilidade formal da cadeia
    traceability = data.setdefault("traceability", {})
    if traceability.get("chain_of_custody_diagram") is None:
        if feedstock.get("certification_scheme"):
            traceability["chain_of_custody_diagram"] = True

    return data


def run_engine(project_data, requirements, audit_mode="development"):
    from scoring import calculate_compliance_score

    # Nível 2: aplicar inferências antes de avaliar
    project_data = apply_inference_rules(project_data)

    results = []
    cross_check_findings = run_core_cross_checks(project_data)

    for req in requirements:
        req_id = req.get("id")
        req_name = req.get("title") or req.get("name")
        logic_key = req.get("logic")
        applies_if = req.get("applies_if", {})
        fields_evaluated = req.get("fields", [])

        # 1a) Verifica aplicabilidade por configuração do projeto
        if not requirement_applies(project_data, applies_if):
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "title": req_name,
                "module": req.get("module"),
                "status": "not_applicable",
                "risk": "none",
                "confidence": 1.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": ["Requirement not applicable to this project configuration."],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
                "requirement_score": None,
                "requirement_score_normalized": 0.0,
                "priority_score": 0.0,
                "field_scores": [],
                "requirement_rating": None,
                "evidence_strength": "none",
                "cross_checks": [],
                "project_evidence": "",
                "methodology_basis": build_methodology_basis_text(req),
                "gap": "",
                "recommendation": "",
                "source_url": req.get("source_url", ""),
                "requirement_text": req.get("requirement_text", ""),
                "audit_mode": audit_mode,
            })
            continue

        # 1b) Verifica aplicabilidade por modo de auditoria (development vs operational)
        mode_applicability = req.get("mode_applicability", "both")
        if mode_applicability == "operational_only" and audit_mode == "development":
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "title": req_name,
                "module": req.get("module"),
                "status": "not_applicable",
                "risk": "none",
                "confidence": 1.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": [
                    "Requisito aplicável apenas em projetos operacionais.",
                    "Em fase de desenvolvimento/PDD, a evidência operacional ainda não existe — não penaliza o score.",
                ],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
                "requirement_score": None,
                "requirement_score_normalized": 0.0,
                "priority_score": 0.0,
                "field_scores": [],
                "requirement_rating": None,
                "evidence_strength": "none",
                "cross_checks": [],
                "project_evidence": "",
                "methodology_basis": build_methodology_basis_text(req),
                "gap": "",
                "recommendation": "Providencie esta evidência quando o projeto estiver operacional.",
                "source_url": req.get("source_url", ""),
                "requirement_text": req.get("requirement_text", ""),
                "audit_mode": audit_mode,
            })
            continue

        # 2) Busca a função de lógica
        try:
            logic_fn = get_logic(logic_key)
        except Exception:
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "title": req_name,
                "module": req.get("module"),
                "status": "error",
                "risk": "unknown",
                "confidence": 0.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": [f"Logic function '{logic_key}' not found."],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
                "requirement_score": 0,
                "requirement_score_normalized": 0.0,
                "priority_score": compute_priority_score("error", 0),
                "field_scores": [],
                "requirement_rating": "weak",
                "evidence_strength": "none",
                "cross_checks": [],
                "project_evidence": "",
                "methodology_basis": build_methodology_basis_text(req),
                "gap": "Requirement not evaluated due to missing or disconnected logic.",
                "recommendation": "Connect or implement deterministic logic for this requirement.",
            })
            continue

        # 3) Executa a lógica — tenta com audit_mode (v1), fallback sem (legacy)
        try:
            try:
                logic_output = logic_fn(project_data, audit_mode=audit_mode)
            except TypeError:
                logic_output = logic_fn(project_data)
        except Exception as e:
            results.append({
                "requirement_id": req_id,
                "requirement_name": req_name,
                "title": req_name,
                "module": req.get("module"),
                "status": "error",
                "risk": "unknown",
                "confidence": 0.0,
                "missing_fields": [],
                "failed_fields": [],
                "notes": [f"Logic execution error: {str(e)}"],
                "logic_key": logic_key,
                "fields_evaluated": fields_evaluated,
                "requirement_score": 0,
                "requirement_score_normalized": 0.0,
                "priority_score": compute_priority_score("error", 0),
                "field_scores": [],
                "requirement_rating": "weak",
                "evidence_strength": "none",
                "cross_checks": [],
                "project_evidence": "",
                "methodology_basis": build_methodology_basis_text(req),
                "gap": "Requirement not evaluated due to missing or disconnected logic.",
                "recommendation": "Connect or implement deterministic logic and verify the extraction pipeline for the required fields.",
            })
            continue

        # 4) Normaliza a saída da lógica
        if isinstance(logic_output, dict):
            status = logic_output.get("status", "error")
            missing_fields = logic_output.get("missing_fields", [])
            failed_fields = logic_output.get("failed_fields", [])
            notes = logic_output.get("notes", [])
            requirement_score = logic_output.get("requirement_score")
            field_scores = logic_output.get("field_scores", [])
            requirement_rating = logic_output.get("requirement_rating")
        else:
            status = logic_output
            missing_fields = []
            failed_fields = []
            notes = []
            requirement_score = None
            field_scores = []
            requirement_rating = None

        if notes is None:
            notes = []
        elif not isinstance(notes, list):
            notes = [str(notes)]

        # 5) Cross-checks relacionados
        related_cross_checks = [
            finding
            for finding in cross_check_findings
            if any(
                path in (missing_fields + failed_fields + fields_evaluated)
                for path in finding.get("paths", [])
            )
        ]

        if related_cross_checks:
            for finding in related_cross_checks:
                notes.append(f"[Cross-check] {finding.get('message')}")

        # 6) Confidence e evidência
        confidence = compute_confidence_from_field_scores(
            status,
            field_scores,
        )

        evidence_strength = classify_evidence_strength(field_scores)

        if status == "compliant":
            risk = "low"
        elif status == "partial":
            risk = "medium"
        elif status == "non_compliant":
            risk = "high"
        elif status == "not_applicable":
            risk = "none"
        else:
            risk = "unknown"

        normalized_score = normalize_score_0_100(requirement_score)

        priority_score = compute_priority_score(
            status,
            normalized_score,
        )

        project_evidence = build_project_evidence_text(
            missing_fields,
            failed_fields,
        )

        methodology_basis = build_methodology_basis_text(req)

        _gap_gen, _rec_gen = build_gap_and_recommendation(
            status, missing_fields, failed_fields,
        )
        # Preferir gap/recommendation da função de lógica (v1) se presentes
        gap = logic_output.get("_gap_override") or _gap_gen if isinstance(logic_output, dict) else _gap_gen
        recommendation = logic_output.get("_recommendation_override") or _rec_gen if isinstance(logic_output, dict) else _rec_gen

        # 7) Monta saída estruturada
        results.append({
            "requirement_id": req_id,
            "requirement_name": req_name,
            "title": req_name,
            "module": req.get("module"),
            "status": status,
            "risk": risk,
            "confidence": confidence,
            "missing_fields": missing_fields,
            "failed_fields": failed_fields,
            "notes": notes,
            "logic_key": logic_key,
            "fields_evaluated": fields_evaluated,
            "requirement_score": requirement_score,
            "requirement_score_normalized": normalized_score,
            "priority_score": priority_score,
            "field_scores": field_scores,
            "requirement_rating": requirement_rating,
            "evidence_strength": evidence_strength,
            "cross_checks": related_cross_checks,
            "project_evidence": project_evidence,
            "methodology_basis": methodology_basis,
            "gap": gap,
            "recommendation": recommendation,
            # v1 fields (source traceability)
            "source_url": req.get("source_url", ""),
            "requirement_text": req.get("requirement_text", ""),
            "audit_mode": audit_mode,
        })

    score_data    = calculate_compliance_score(results)
    module_summary = aggregate_module_summary(results)
    top_risks     = build_top_risks(results, limit=5)

    return {
        "results": results,
        "score_data": score_data,
        "module_summary": module_summary,
        "top_risks": top_risks,
    }
    
def reactor_design_diagram(data):
    """
    R-6AQG-1 | P&ID or engineering design diagram with sensors
    """
    try:
        production = data.get("production", {})

        has_diagram = production.get("reactor_design_diagram")
        has_sensor_inventory = production.get("sensor_inventory")
        has_sensor_locations = production.get("sensor_locations")

        field_scores = [
            score_boolean_field(
                "production.reactor_design_diagram",
                has_diagram,
                50,
                note_if_missing="Reactor design diagram or P&ID is missing.",
            ),
            score_boolean_field(
                "production.sensor_inventory",
                has_sensor_inventory,
                25,
                note_if_missing="Sensor inventory is missing.",
            ),
            score_boolean_field(
                "production.sensor_locations",
                has_sensor_locations,
                25,
                note_if_missing="Sensor locations are missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if has_diagram is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Reactor design diagram and sensor documentation are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_design_diagram execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def durability_option_declared(data):
    """
    R-BFEE-0 | Durability option declared
    """
    try:
        methodology = data.get("methodology", {})

        durability_option = methodology.get("durability_option")
        allowed = ["200", "1000", "combined_200_1000"]

        field_scores = []

        if not durability_option:
            field_scores.append({
                "path": "methodology.durability_option",
                "weight": 100,
                "score": 0,
                "status": "missing",
                "notes": ["Durability option is not declared."],
            })
        elif durability_option not in allowed:
            field_scores.append({
                "path": "methodology.durability_option",
                "weight": 100,
                "score": 0,
                "status": "fail",
                "notes": ["Durability option must be one of: 200, 1000, combined_200_1000."],
            })
        else:
            field_scores.append({
                "path": "methodology.durability_option",
                "weight": 100,
                "score": 100,
                "status": "pass",
                "notes": [],
            })

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not durability_option or durability_option not in allowed:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append(f"Durability option declared as '{durability_option}'.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"durability_option_declared execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def sampling_batch_definition(data):
    """
    R-6YSW-0 | Production batch definition within allowed threshold
    """
    try:
        methodology = data.get("methodology", {})
        sampling = data.get("sampling", {})

        production_subpathway = methodology.get("production_subpathway")
        batch_definition_days = sampling.get("batch_definition_days")

        field_scores = []

        if batch_definition_days is None:
            field_scores.append({
                "path": "sampling.batch_definition_days",
                "weight": 100,
                "score": 0,
                "status": "missing",
                "notes": ["Batch definition in days is not provided."],
            })
        else:
            limit = 7 if production_subpathway == "combustion_coproduct" else 31

            if batch_definition_days <= limit:
                field_scores.append({
                    "path": "sampling.batch_definition_days",
                    "weight": 100,
                    "score": 100,
                    "status": "pass",
                    "notes": [],
                })
            else:
                if production_subpathway == "combustion_coproduct":
                    note = "Combustion co-product systems must define batches within 7 days."
                else:
                    note = "Production batch definition exceeds the 31-day threshold."

                field_scores.append({
                    "path": "sampling.batch_definition_days",
                    "weight": 100,
                    "score": 0,
                    "status": "fail",
                    "notes": [note],
                })

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if batch_definition_days is None:
            status = "non_compliant"
        else:
            limit = 7 if production_subpathway == "combustion_coproduct" else 31
            if batch_definition_days > limit:
                status = "non_compliant"
            else:
                status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            if production_subpathway == "combustion_coproduct":
                notes.append("Batch definition is within the 7-day threshold for combustion co-product systems.")
            else:
                notes.append("Batch definition is within the allowed threshold.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"sampling_batch_definition execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
        
def chain_of_custody_diagram(data):
    """
    R-3MYN-0 | Chain of custody diagram or equivalent provided
    """
    try:
        traceability = data.get("traceability", {})

        diagram = traceability.get("chain_of_custody_diagram")

        field_scores = [
            score_boolean_field(
                "traceability.chain_of_custody_diagram",
                diagram,
                100,
                note_if_missing="Chain of custody diagram or equivalent evidence is missing.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if diagram is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Chain of custody diagram or equivalent evidence is present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"chain_of_custody_diagram execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def biochar_chemical_analysis(data):
    """
    R-6F0N-0 | Chemical analysis for biochar characterization performed
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        chemical_analysis_performed = characterization.get("chemical_analysis_performed")
        lab_reports = characterization.get("lab_reports")

        field_scores = [
            score_boolean_field(
                "biochar.characterization.chemical_analysis_performed",
                chemical_analysis_performed,
                70,
                note_if_missing="Chemical analysis for biochar characterization is not evidenced.",
            ),
            score_boolean_field(
                "biochar.characterization.lab_reports",
                lab_reports,
                30,
                note_if_missing="Lab reports supporting chemical analysis are missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if chemical_analysis_performed is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Chemical analysis and supporting lab reports are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_chemical_analysis execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def uncertainty_inputs(data):
    """
    R-Z106-1 | Uncertainty inputs disclosed
    """
    try:
        quant = data.get("quantification", {})

        input_variables = quant.get("input_variables")
        input_uncertainties = quant.get("input_uncertainties")

        field_scores = [
            score_boolean_field(
                "quantification.input_variables",
                input_variables,
                60,
                note_if_missing="Input variables used in quantification are not disclosed.",
            ),
            score_boolean_field(
                "quantification.input_uncertainties",
                input_uncertainties,
                40,
                note_if_missing="Input uncertainties are not disclosed.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if input_variables is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Input variables and uncertainties are disclosed.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"uncertainty_inputs execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def stockpiling_disclosure(data):
    """
    R-6E1D-0 | Biochar stockpiling disclosed
    """
    try:
        storage = data.get("storage", {})

        stockpiled = storage.get("stockpiled_before_end_use")
        disclosure = storage.get("stockpiling_documented")

        field_scores = []

        # Campo 1: status de stockpiling
        if stockpiled is True or stockpiled is False:
            field_scores.append({
                "path": "storage.stockpiled_before_end_use",
                "weight": 60,
                "score": 60,
                "status": "pass",
                "notes": [],
            })
        else:
            field_scores.append({
                "path": "storage.stockpiled_before_end_use",
                "weight": 60,
                "score": 0,
                "status": "missing",
                "notes": ["Stockpiling status before end use is not defined."],
            })

        # Campo 2: documentação só importa se stockpiling existir
        if stockpiled is True:
            field_scores.append(
                score_boolean_field(
                    "storage.stockpiling_documented",
                    disclosure,
                    40,
                    note_if_missing="Stockpiling occurs before end use but is not documented.",
                )
            )
        else:
            field_scores.append({
                "path": "storage.stockpiling_documented",
                "weight": 40,
                "score": 40,
                "status": "not_applicable",
                "notes": [],
            })

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if stockpiled is None:
            status = "partial"
        elif stockpiled is True and disclosure is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            if stockpiled is True:
                notes.append("Stockpiling before end use is documented.")
            else:
                notes.append("No stockpiling before end use is reported.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"stockpiling_disclosure execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def adaptive_management_plan(data):
    """
    R-BC4H-1 | Adaptive management plan in place
    """
    try:
        management = data.get("management", {})

        plan = management.get("adaptive_management_plan")
        triggers = management.get("monitoring_triggers")
        pause_or_stop = management.get("pause_or_stop_conditions")

        field_scores = [
            score_boolean_field(
                "management.adaptive_management_plan",
                plan,
                50,
                note_if_missing="Adaptive management plan is missing.",
            ),
            score_boolean_field(
                "management.monitoring_triggers",
                triggers,
                25,
                note_if_missing="Monitoring triggers for adaptive management are missing.",
            ),
            score_boolean_field(
                "management.pause_or_stop_conditions",
                pause_or_stop,
                25,
                note_if_missing="Pause or stop conditions are missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if plan is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append(
                "Adaptive management plan, monitoring triggers, and pause/stop conditions are present."
            )

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"adaptive_management_plan execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def feedstock_moisture_management(data):
    """
    R-NJ8G-0 | Feedstock moisture management and verification
    """
    try:
        feedstock = data.get("feedstock", {})

        moisture_plan = feedstock.get("moisture_control_plan")
        moisture_measurement = feedstock.get("moisture_measurement")

        field_scores = [
            score_boolean_field(
                "feedstock.moisture_control_plan",
                moisture_plan,
                60,
                note_if_missing="Feedstock moisture control plan is missing.",
            ),
            score_boolean_field(
                "feedstock.moisture_measurement",
                moisture_measurement,
                40,
                note_if_missing="Feedstock moisture measurement method is missing or not evidenced.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if moisture_plan is not True and moisture_measurement is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Feedstock moisture control plan and moisture measurement are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"feedstock_moisture_management execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def contaminant_monitoring_plan(data):
    """
    R-HE38-0 | Contaminant monitoring plan specified
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})
        safeguards = data.get("safeguards", {})

        contaminants = characterization.get("contaminant_testing")
        frequency = characterization.get("contaminant_testing_frequency")

        # backward-compatible support in case future mapper/schema moves this to safeguards
        safeguards_plan = safeguards.get("contaminant_monitoring_plan")
        safeguards_frequency = safeguards.get("testing_frequency")

        contaminants_present = (contaminants is True) or (safeguards_plan is True)
        frequency_present = bool(frequency) or bool(safeguards_frequency)

        field_scores = []

        # Campo 1: testing / monitoring plan
        if contaminants_present:
            field_scores.append({
                "path": "biochar.characterization.contaminant_testing",
                "weight": 70,
                "score": 70,
                "status": "pass",
                "notes": [],
            })
        else:
            field_scores.append({
                "path": "biochar.characterization.contaminant_testing",
                "weight": 70,
                "score": 0,
                "status": "missing",
                "notes": ["Contaminant testing or contaminant monitoring plan is not documented."],
            })

        # Campo 2: frequency
        if frequency_present:
            field_scores.append({
                "path": "biochar.characterization.contaminant_testing_frequency",
                "weight": 30,
                "score": 30,
                "status": "pass",
                "notes": [],
            })
        else:
            field_scores.append({
                "path": "biochar.characterization.contaminant_testing_frequency",
                "weight": 30,
                "score": 0,
                "status": "missing",
                "notes": ["Contaminant testing frequency is missing."],
            })

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not contaminants_present:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Contaminant testing and monitoring frequency are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"contaminant_monitoring_plan execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def product_standard_compliance(data):
    """
    R-9KKF-0 | Compliance with relevant product standards evidenced
    """
    try:
        product = data.get("product", {})

        standard = product.get("standard_compliance")
        certification = product.get("certification_scheme")

        field_scores = [
            score_boolean_field(
                "product.standard_compliance",
                standard,
                70,
                note_if_missing="Compliance with relevant product standards is not evidenced.",
            ),
            score_presence_field(
                "product.certification_scheme",
                certification,
                30,
                note_if_missing="Certification scheme or reference standard is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if standard is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Product standard compliance and certification scheme are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"product_standard_compliance execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def fuel_use_reversal_risk(data):
    """
    R-Z4A3-0 | Fuel-use reversal risk assessed
    """
    try:
        risk = data.get("risk_assessment", {})

        assessment = risk.get("fuel_use_reversal_risk")
        mitigation = risk.get("mitigation_plan")

        field_scores = [
            score_boolean_field(
                "risk_assessment.fuel_use_reversal_risk",
                assessment,
                65,
                note_if_missing="Fuel-use reversal risk assessment is missing.",
            ),
            score_boolean_field(
                "risk_assessment.mitigation_plan",
                mitigation,
                35,
                note_if_missing="Mitigation plan for fuel-use reversal risk is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if assessment is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=65,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Fuel-use reversal risk assessment and mitigation plan are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"fuel_use_reversal_risk execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
        
def sampling_plan_consistency(data):
    """
    R-S8K1-1 | Sampling plan consistent with Methods A/B
    """
    try:
        sampling = data.get("sampling", {})

        method = sampling.get("method")
        plan_defined = sampling.get("sampling_plan_defined")

        field_scores = []

        # Campo 1: method
        if method in ["A", "B"]:
            field_scores.append({
                "path": "sampling.method",
                "weight": 60,
                "score": 60,
                "status": "pass",
                "notes": [],
            })
        elif method in [None, ""]:
            field_scores.append({
                "path": "sampling.method",
                "weight": 60,
                "score": 0,
                "status": "missing",
                "notes": ["Sampling method is not documented."],
            })
        else:
            field_scores.append({
                "path": "sampling.method",
                "weight": 60,
                "score": 0,
                "status": "fail",
                "notes": ["Sampling method must be 'A' or 'B'."],
            })

        # Campo 2: sampling plan
        field_scores.append(
            score_boolean_field(
                "sampling.sampling_plan_defined",
                plan_defined,
                40,
                note_if_missing="Sampling plan is not documented.",
            )
        )

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if method not in ["A", "B"]:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Sampling method and sampling plan are properly defined.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"sampling_plan_consistency execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
        
def reactor_maintenance_plan(data):
    """
    R-19AF-1 | Reactor maintenance plan evidenced
    """
    try:
        production = data.get("production", {})

        maintenance_plan = production.get("maintenance_plan")
        maintenance_schedule = production.get("maintenance_schedule")

        field_scores = [
            score_boolean_field(
                "production.maintenance_plan",
                maintenance_plan,
                70,
                note_if_missing="Maintenance plan is missing.",
            ),
            score_boolean_field(
                "production.maintenance_schedule",
                maintenance_schedule,
                30,
                note_if_missing="Maintenance schedule is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if maintenance_plan is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Maintenance plan and schedule are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_maintenance_plan execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def stack_emissions_monitoring_method(data):
    """
    R-TKNH-0 | Stack emissions monitoring method selected
    """
    try:
        emissions = data.get("emissions", {})

        method = emissions.get("stack_monitoring_method")
        frequency = emissions.get("testing_frequency")

        field_scores = [
            score_presence_field(
                "emissions.stack_monitoring_method",
                method,
                60,
                note_if_missing="Stack emissions monitoring method is missing.",
            ),
            score_presence_field(
                "emissions.testing_frequency",
                frequency,
                40,
                note_if_missing="Testing frequency for stack emissions is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not method:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append(
                "Stack emissions monitoring method and testing frequency are present."
            )

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"stack_emissions_monitoring_method execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def biochar_required_measurements(data):
    """
    R-VGXA-0 | All required physical and chemical measurements obtained or planned
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        required_complete = characterization.get("required_measurements_complete")
        measurement_values = characterization.get("measurement_values")

        field_scores = [
            score_boolean_field(
                "biochar.characterization.required_measurements_complete",
                required_complete,
                70,
                note_if_missing="Required physical and chemical measurements are not complete.",
            ),
            score_boolean_field(
                "biochar.characterization.measurement_values",
                measurement_values,
                30,
                note_if_missing="Measurement values are missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if required_complete is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Required measurements and measurement values are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_required_measurements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def deployment_method_selected(data):
    """
    R-T2X2-0 | Deployment method specified
    """
    try:
        soil = data.get("storage", {}).get("soil", {})

        deployment_methods = soil.get("deployment_methods")

        field_scores = []

        if not deployment_methods:
            field_scores.append({
                "path": "storage.soil.deployment_methods",
                "weight": 100,
                "score": 0,
                "status": "missing",
                "notes": ["No deployment method is specified."],
            })
            status = "non_compliant"

        elif isinstance(deployment_methods, str):
            deployment_methods = [deployment_methods]

            field_scores.append({
                "path": "storage.soil.deployment_methods",
                "weight": 100,
                "score": 100,
                "status": "pass",
                "notes": ["Deployment method provided as string and normalized to list."],
            })
            status = "compliant"

        elif len(deployment_methods) == 0:
            field_scores.append({
                "path": "storage.soil.deployment_methods",
                "weight": 100,
                "score": 0,
                "status": "missing",
                "notes": ["Deployment methods list is empty."],
            })
            status = "non_compliant"

        else:
            field_scores.append({
                "path": "storage.soil.deployment_methods",
                "weight": 100,
                "score": 100,
                "status": "pass",
                "notes": [],
            })
            status = "compliant"

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Deployment method is specified.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"deployment_method_selected execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def direct_soil_application_evidence(data):
    """
    R-8PBP-0 | Direct soil application evidence pathway confirmed
    """
    try:
        soil = data.get("storage", {}).get("soil", {})

        deployment_methods = soil.get("deployment_methods", [])
        evidence = soil.get("direct_application_evidence_pathway")

        field_scores = []

        if "direct_soil_application" not in deployment_methods:
            field_scores.append({
                "path": "storage.soil.direct_application_evidence_pathway",
                "weight": 100,
                "score": 100,
                "status": "not_applicable",
                "notes": [],
            })
            status = "not_applicable"

        else:
            field_scores.append(
                score_boolean_field(
                    "storage.soil.direct_application_evidence_pathway",
                    evidence,
                    100,
                    note_if_missing="Evidence for direct soil application pathway is missing.",
                )
            )

            requirement_score = summarize_field_scores(field_scores)
            requirement_rating = derive_requirement_rating(requirement_score)

            if evidence is not True:
                status = "non_compliant"
            else:
                status = "compliant"

            missing_fields = [
                item["path"]
                for item in field_scores
                if item["status"] == "missing"
            ]
            failed_fields = [
                item["path"]
                for item in field_scores
                if item["status"] == "fail"
            ]
            notes = collect_field_score_notes(field_scores)

            if status == "compliant":
                notes.append("Direct soil application evidence pathway is documented.")

            return build_logic_result(
                status=status,
                missing_fields=missing_fields,
                failed_fields=failed_fields,
                notes=notes,
                requirement_score=requirement_score,
                field_scores=field_scores,
                requirement_rating=requirement_rating,
            )

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        return build_logic_result(
            status=status,
            missing_fields=[],
            failed_fields=[],
            notes=["Direct soil application is not part of the deployment pathway."],
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"direct_soil_application_evidence execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
        
def reactor_material_selection(data):
    """
    R-DMET-0 | Reactor material selection justified
    """
    try:
        production = data.get("production", {})

        components = production.get("reactor_components")
        justification = production.get("material_selection_justification")

        field_scores = [
            score_boolean_field(
                "production.reactor_components",
                components,
                60,
                note_if_missing="Reactor components are not described.",
            ),
            score_boolean_field(
                "production.material_selection_justification",
                justification,
                40,
                note_if_missing="Material selection justification is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if components is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Reactor components and material selection justification are present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"reactor_material_selection execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def end_material_process_description(data):
    """
    R-V04V-0 | End material production process described in detail
    """
    try:
        production = data.get("production", {})

        description = production.get("end_material_process_description")

        field_scores = [
            score_boolean_field(
                "production.end_material_process_description",
                description,
                100,
                note_if_missing="End material production process description is missing.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if description is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("End material production process is described.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"end_material_process_description execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def environmental_legal_requirements(data):
    """
    R-52YX-0 | Applicable environmental legal requirements provided
    """
    try:
        legal = data.get("legal", {})

        requirements = legal.get("applicable_environmental_requirements")

        field_scores = [
            score_boolean_field(
                "legal.applicable_environmental_requirements",
                requirements,
                100,
                note_if_missing="Applicable environmental legal requirements are not documented.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if requirements is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Applicable environmental legal requirements are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"environmental_legal_requirements execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def regulatory_measurement_methods(data):
    """
    R-RQTJ-0 | Regulatory measurements approach described
    """
    try:
        legal = data.get("legal", {})

        methods = legal.get("regulatory_measurement_methods")

        field_scores = [
            score_boolean_field(
                "legal.regulatory_measurement_methods",
                methods,
                100,
                note_if_missing="Regulatory measurement methods are not documented.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if methods is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Regulatory measurement methods are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"regulatory_measurement_methods execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def biochar_characterization_approach(data):
    """
    R-NYQT-0 | Biochar characterization and ongoing monitoring approach described
    """
    try:
        characterization = data.get("biochar", {}).get("characterization", {})

        approach_description = characterization.get("approach_description")
        ongoing_monitoring_plan = characterization.get("ongoing_monitoring_plan")

        field_scores = [
            score_presence_field(
                "biochar.characterization.approach_description",
                approach_description,
                65,
                note_if_missing="Biochar characterization approach is not documented.",
            ),
            score_boolean_field(
                "biochar.characterization.ongoing_monitoring_plan",
                ongoing_monitoring_plan,
                35,
                note_if_missing="Ongoing monitoring plan for biochar characterization is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not approach_description:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=65,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Biochar characterization approach and monitoring plan are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_characterization_approach execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def engineering_design_diagram(data):
    """
    R-29W5-0 | Engineering design diagram provided
    """
    try:
        production = data.get("production", {})

        diagram = production.get("engineering_design_diagram")

        field_scores = [
            score_boolean_field(
                "production.engineering_design_diagram",
                diagram,
                100,
                note_if_missing="Engineering design diagram is missing.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if diagram is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Engineering design diagram is present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"engineering_design_diagram execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def crediting_activity_boundaries(data):
    """
    R-KPDH-0 | Crediting activity boundaries described in detail
    """
    try:
        quant = data.get("quantification", {})

        boundaries = quant.get("crediting_activity_boundaries")

        field_scores = [
            score_boolean_field(
                "quantification.crediting_activity_boundaries",
                boundaries,
                100,
                note_if_missing="Crediting activity boundaries are not documented.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if boundaries is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Crediting activity boundaries are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"crediting_activity_boundaries execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def storage_system_boundary(data):
    """
    R-CCP7-0 | Storage emissions fully included in system boundary
    """
    try:
        quant = data.get("quantification", {})

        storage_emissions_accounted = quant.get("storage_emissions_accounted")

        field_scores = [
            score_boolean_field(
                "quantification.storage_emissions_accounted",
                storage_emissions_accounted,
                100,
                note_if_missing="Storage emissions are not accounted for in the system boundary.",
            )
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if storage_emissions_accounted is not True:
            status = "non_compliant"
        else:
            status = "compliant"

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Storage emissions are included in the system boundary.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"storage_system_boundary execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def pyrolysis_gas_end_use_accounting(data):
    """
    R-E8H6-0 | Pyrolysis gas end-use accounting approach selected
    """
    try:
        emissions = data.get("emissions", {})
        production = data.get("production", {})

        approach = emissions.get("pyrolysis_gas_end_use_approach")
        control_system = emissions.get("emissions_control_system")

        if not control_system:
            control_system = production.get("gas_burner_present") or production.get("combustion_gas_control")

        field_scores = [
            score_presence_field(
                "emissions.pyrolysis_gas_end_use_approach",
                approach,
                60,
                note_if_missing="Pyrolysis gas end-use accounting approach is missing.",
            ),
            score_presence_field(
                "emissions.emissions_control_system",
                control_system,
                40,
                note_if_missing="Emissions control system for pyrolysis gas end-use is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        status = derive_requirement_status_from_score(
            requirement_score,
            non_compliant_threshold=60,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Pyrolysis gas end-use accounting approach and emissions control system are documented.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"pyrolysis_gas_end_use_accounting execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )
def biochar_incorporation_documentation(data):
    """
    Logic for biochar incorporation / built-environment incorporation documentation
    """
    try:
        storage = data.get("storage", {})
        soil = storage.get("soil", {})
        built = storage.get("built_environment", {})

        soil_evidence = soil.get("direct_application_evidence_pathway")
        soil_methods = soil.get("deployment_methods")
        built_evidence = (
            built.get("incorporation_documentation")
            if isinstance(built, dict) else None
        ) or storage.get("built_environment_incorporation_evidence")

        field_scores = []

        soil_pathway_present = bool(soil_methods)
        built_pathway_present = bool(built_evidence)

        if soil_pathway_present:
            field_scores.append(
                score_boolean_field(
                    "storage.soil.direct_application_evidence_pathway",
                    soil_evidence,
                    50,
                    note_if_missing="Evidence for soil incorporation pathway is missing.",
                )
            )
        else:
            field_scores.append({
                "path": "storage.soil.direct_application_evidence_pathway",
                "weight": 50,
                "score": 50,
                "status": "not_applicable",
                "notes": [],
            })

        if built_pathway_present:
            field_scores.append({
                "path": "storage.built_environment_incorporation_evidence",
                "weight": 50,
                "score": 50,
                "status": "pass",
                "notes": [],
            })
        else:
            field_scores.append({
                "path": "storage.built_environment_incorporation_evidence",
                "weight": 50,
                "score": 0 if not soil_pathway_present else 50,
                "status": "missing" if not soil_pathway_present else "not_applicable",
                "notes": (
                    ["No documentation of built-environment incorporation pathway was found."]
                    if not soil_pathway_present else []
                ),
            })

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not soil_pathway_present and not built_pathway_present:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Biochar incorporation pathway documentation is present.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"biochar_incorporation_documentation execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def derive_status_with_hard_gate(
    requirement_score,
    *,
    hard_fail: bool = False,
    hard_partial: bool = False,
    non_compliant_threshold=50,
    compliant_threshold=100,
):
    if hard_fail:
        return "non_compliant"

    if hard_partial:
        return "partial"

    return derive_requirement_status_from_score(
        requirement_score,
        non_compliant_threshold=non_compliant_threshold,
        compliant_threshold=compliant_threshold,
    )

def build_project_evidence_text(missing_fields, failed_fields):
    lines = []

    if missing_fields:
        lines.append("Missing fields:")
        for f in missing_fields[:5]:
            lines.append(f"- {f}")

    if failed_fields:
        lines.append("Failed checks:")
        for f in failed_fields[:5]:
            lines.append(f"- {f}")

    return "\n".join(lines).strip()


def build_methodology_basis_text(req):
    module = req.get("module")
    requirement_id = req.get("id") or req.get("requirement_id")

    parts = []
    if module:
        parts.append(f"Module: {module}")
    if requirement_id:
        parts.append(f"Requirement ID: {requirement_id}")

    return " | ".join(parts)


def build_gap_and_recommendation(status, missing_fields, failed_fields):
    gap = ""
    recommendation = ""

    if status == "compliant":
        recommendation = "Maintain current evidence and proceed to validation readiness."

    elif status == "partial":
        gap = "Partial evidence available; some required elements are incomplete."
        if missing_fields:
            recommendation = "Provide missing documentation and strengthen evidence for identified gaps."
        else:
            recommendation = "Strengthen consistency and completeness of existing evidence."

    elif status == "non_compliant":
        gap = "Core requirement not met or insufficiently evidenced."
        if failed_fields:
            recommendation = "Correct failed conditions and provide full supporting evidence before validation."
        else:
            recommendation = "Establish missing core elements required for compliance."

    elif status == "error":
        gap = "Requirement not evaluated due to missing or disconnected logic."
        recommendation = "Connect logic or ensure required fields are properly extracted and mapped."

    return gap, recommendation

def normalize_score_0_100(value):
    try:
        if value is None:
            return 0.0
        v = float(value)
        if v <= 1.0:
            return round(v * 100.0, 2)
        return round(v, 2)
    except Exception:
        return 0.0


def compute_priority_score(status, requirement_score):
    # status_weight: erro/NC > partial > compliant
    if status == "error":
        status_weight = 100
    elif status == "non_compliant":
        status_weight = 90
    elif status == "partial":
        status_weight = 60
    elif status == "compliant":
        status_weight = 10
    else:
        status_weight = 0

    score = normalize_score_0_100(requirement_score)
    # quanto menor o score, maior a prioridade
    score_penalty = 100 - score

    return round(status_weight * 0.6 + score_penalty * 0.4, 2)


def aggregate_module_summary(results):
    module_summary = {}

    for r in results or []:
        module = r.get("module") or "unknown"
        ms = module_summary.setdefault(module, {
            "count": 0,
            "compliant": 0,
            "partial": 0,
            "non_compliant": 0,
            "error": 0,
            "priority_sum": 0.0,
        })

        ms["count"] += 1
        status = r.get("status")

        if status in ms:
            ms[status] += 1
        else:
            ms[status] = ms.get(status, 0) + 1

        ms["priority_sum"] += float(r.get("priority_score", 0) or 0)

    # calcular média de prioridade por módulo
    for m, ms in module_summary.items():
        if ms["count"] > 0:
            ms["priority_avg"] = round(ms["priority_sum"] / ms["count"], 2)
        else:
            ms["priority_avg"] = 0.0

    return module_summary


def build_top_risks(results, limit=5):
    sorted_items = sorted(
        results or [],
        key=lambda r: float(r.get("priority_score", 0) or 0),
        reverse=True,
    )

    top = []
    for r in sorted_items[:limit]:
        rid = r.get("requirement_id")
        title = r.get("title") or r.get("requirement_name")
        gap = r.get("gap", "")
        rec = r.get("recommendation", "")

        line = f"{rid} — {title}"
        if gap:
            line += f" | Gap: {gap}"
        if rec:
            line += f" | Action: {rec}"

        top.append(line)

    return top
    
def eval_project_ownership(data):
    try:
        project = data.get("project", {})

        country = project.get("country")
        locations = project.get("locations")
        ownership_evidence = project.get("ownership_evidence")

        # Nível 1: proxies de propriedade quando ownership_evidence não foi extraído
        # Certificação Isometric e descrição do sistema identificam o titular do projeto
        if not ownership_evidence:
            cert_scheme = data.get("product", {}).get("certification_scheme")
            system_desc = data.get("production", {}).get("system_description")
            proxies = [v for v in [cert_scheme, system_desc] if v]
            if proxies:
                ownership_evidence = proxies

        field_scores = [
            score_presence_field(
                "project.country",
                country,
                20,
                note_if_missing="Project country is not documented.",
            ),
            score_presence_field(
                "project.locations",
                locations,
                20,
                note_if_missing="Project locations are not documented.",
            ),
            score_presence_field(
                "project.ownership_evidence",
                ownership_evidence,
                60,
                note_if_missing="Ownership evidence is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        # Nível 1: removido hard_fail gate — falha de extração de ownership_evidence
        # não deve invalidar projeto com certificação e descrição do sistema identificadas
        status = derive_requirement_status_from_score(
            requirement_score,
            non_compliant_threshold=25,
            compliant_threshold=85,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Project ownership and location context are sufficiently evidenced.")
        elif status == "partial":
            notes.append("Project ownership framework is partially evidenced but remains incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("Project ownership is not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_project_ownership execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_project_crediting_context(data):
    try:
        project = data.get("project", {})
        methodology = data.get("methodology", {})

        standard = methodology.get("standard")
        pathway = methodology.get("pathway")
        durability_option = methodology.get("durability_option")

        field_scores = [
            score_presence_field(
                "methodology.standard",
                standard,
                40,
                note_if_missing="Methodology standard is not defined.",
            ),
            score_presence_field(
                "methodology.pathway",
                pathway,
                30,
                note_if_missing="Methodology pathway is not defined.",
            ),
            score_presence_field(
                "methodology.durability_option",
                durability_option,
                30,
                note_if_missing="Durability option is not defined.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not standard or not pathway:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_project_crediting_context execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_feedstock_origin(data):
    try:
        feedstock = data.get("feedstock", {})

        biomass_type = feedstock.get("biomass_type")
        source_locations = feedstock.get("source_locations")

        field_scores = [
            score_presence_field(
                "feedstock.biomass_type",
                biomass_type,
                40,
                note_if_missing="Feedstock type is not documented.",
            ),
            score_presence_field(
                "feedstock.source_locations",
                source_locations,
                60,
                note_if_missing="Feedstock source locations are not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not biomass_type:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=40,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_feedstock_origin execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_feedstock_counterfactual(data):
    try:
        feedstock = data.get("feedstock", {})
        ghg = data.get("ghg_accounting", {})

        pre_project_use = feedstock.get("pre_project_biomass_use")
        baseline_defined = ghg.get("baseline_defined")

        field_scores = [
            score_presence_field(
                "feedstock.pre_project_biomass_use",
                pre_project_use,
                60,
                note_if_missing="Pre-project feedstock use is not documented.",
            ),
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                40,
                note_if_missing="Baseline is not defined.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not pre_project_use:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_feedstock_counterfactual execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_feedstock_traceability(data):
    try:
        traceability = data.get("traceability", {})
        feedstock = data.get("feedstock", {})

        chain_diagram = traceability.get("chain_of_custody_diagram")
        source_locations = feedstock.get("source_locations")

        # Nível 1: certificação de sustentabilidade (FSC, PEFC, SBP etc.) como proxy
        # de rastreabilidade de cadeia de custódia — implica tracking formal do feedstock
        cert_scheme = feedstock.get("certification_scheme")
        has_sustainability_cert = bool(cert_scheme)
        effective_chain = chain_diagram is True or has_sustainability_cert

        field_scores = [
            score_boolean_field(
                "traceability.chain_of_custody_diagram",
                effective_chain,
                60,
                note_if_missing="Chain of custody evidence is missing.",
            ),
            score_presence_field(
                "feedstock.source_locations",
                source_locations,
                40,
                note_if_missing="Feedstock source locations are missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        # Nível 1: removido hard gate `chain_diagram is not True → non_compliant`
        # Certificação de sustentabilidade é evidência equivalente de rastreabilidade
        status = derive_requirement_status_from_score(
            requirement_score,
            non_compliant_threshold=25,
            compliant_threshold=85,
        )

        notes = collect_field_score_notes(field_scores)
        if has_sustainability_cert and chain_diagram is not True:
            notes.append(
                f"Rastreabilidade inferida a partir de certificação de sustentabilidade: {cert_scheme}."
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_feedstock_traceability execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_additionality_core(data):
    try:
        eligibility = data.get("eligibility", {})
        ghg = data.get("ghg_accounting", {})

        additionality_claim = eligibility.get("additionality_claim")
        baseline_defined = ghg.get("baseline_defined")

        field_scores = [
            score_boolean_field(
                "eligibility.additionality_claim",
                additionality_claim,
                60,
                note_if_missing="Additionality is not demonstrated.",
            ),
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                40,
                note_if_missing="Baseline is not defined.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if additionality_claim is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_additionality_core execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_additionality_barriers(data):
    try:
        eligibility = data.get("eligibility", {})
        management = data.get("management", {})

        additionality_claim = eligibility.get("additionality_claim")
        adaptive_plan = management.get("adaptive_management_plan")

        field_scores = [
            score_boolean_field(
                "eligibility.additionality_claim",
                additionality_claim,
                70,
                note_if_missing="Additionality claim is missing.",
            ),
            score_boolean_field(
                "management.adaptive_management_plan",
                adaptive_plan,
                30,
                note_if_missing="Supporting management structure is not evidenced.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if additionality_claim is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=70,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_additionality_barriers execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_baseline_core(data):
    try:
        ghg = data.get("ghg_accounting", {})
        feedstock = data.get("feedstock", {})

        baseline_defined = ghg.get("baseline_defined")
        pre_project_use = feedstock.get("pre_project_biomass_use")

        field_scores = [
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                60,
                note_if_missing="Baseline scenario is not defined.",
            ),
            score_presence_field(
                "feedstock.pre_project_biomass_use",
                pre_project_use,
                40,
                note_if_missing="Pre-project biomass use is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if baseline_defined is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_baseline_core execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_baseline_evidence(data):
    try:
        ghg = data.get("ghg_accounting", {})
        feedstock = data.get("feedstock", {})

        baseline_defined = ghg.get("baseline_defined")
        accounting_compliance = feedstock.get("feedstock_accounting_module_compliance")

        field_scores = [
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                50,
                note_if_missing="Baseline assumptions are not documented.",
            ),
            score_boolean_field(
                "feedstock.feedstock_accounting_module_compliance",
                accounting_compliance,
                50,
                note_if_missing="Feedstock accounting evidence is missing.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if baseline_defined is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_baseline_evidence execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_system_boundary(data):
    try:
        ghg = data.get("ghg_accounting", {})
        quant = data.get("quantification", {})

        system_boundary = ghg.get("system_boundary_defined")
        crediting_boundaries = quant.get("crediting_activity_boundaries")

        field_scores = [
            score_boolean_field(
                "ghg_accounting.system_boundary_defined",
                system_boundary,
                60,
                note_if_missing="System boundary is not defined.",
            ),
            score_boolean_field(
                "quantification.crediting_activity_boundaries",
                crediting_boundaries,
                40,
                note_if_missing="Crediting activity boundaries are not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = system_boundary is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=60,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("System boundary and crediting activity boundaries are sufficiently evidenced.")
        elif status == "partial":
            notes.append("System boundary framework is partially evidenced but remains incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("System boundary requirements are not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_system_boundary execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def eval_leakage_sources(data):
    try:
        emissions = data.get("emissions_testing", {})
        feedstock = data.get("feedstock", {})

        leakage_monitoring = emissions.get("leakage_monitoring")
        pre_project_use = feedstock.get("pre_project_biomass_use")

        field_scores = [
            score_boolean_field(
                "emissions_testing.leakage_monitoring",
                leakage_monitoring,
                60,
                note_if_missing="Leakage monitoring is not documented.",
            ),
            score_presence_field(
                "feedstock.pre_project_biomass_use",
                pre_project_use,
                40,
                note_if_missing="Counterfactual use is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if leakage_monitoring is not True:
            status = "partial"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_leakage_sources execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_leakage_treatment(data):
    try:
        emissions = data.get("emissions_testing", {})
        monitoring = data.get("monitoring_reporting", {})

        leakage_monitoring = emissions.get("leakage_monitoring")
        uncertainty_method = monitoring.get("uncertainty_method")

        field_scores = [
            score_boolean_field(
                "emissions_testing.leakage_monitoring",
                leakage_monitoring,
                50,
                note_if_missing="Leakage treatment is not evidenced.",
            ),
            score_presence_field(
                "monitoring_reporting.uncertainty_method",
                uncertainty_method,
                50,
                note_if_missing="Conservative uncertainty treatment is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not uncertainty_method:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_leakage_treatment execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_carbon_accounting_structure(data):
    try:
        ghg = data.get("ghg_accounting", {})
        quant = data.get("quantification", {})

        system_boundary = ghg.get("system_boundary_defined")
        baseline_defined = ghg.get("baseline_defined")
        input_variables = quant.get("input_variables")

        field_scores = [
            score_boolean_field(
                "ghg_accounting.system_boundary_defined",
                system_boundary,
                35,
                note_if_missing="System boundary is not defined.",
            ),
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                35,
                note_if_missing="Baseline is not defined.",
            ),
            score_boolean_field(
                "quantification.input_variables",
                input_variables,
                30,
                note_if_missing="Input variables are not disclosed.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if system_boundary is not True or baseline_defined is not True:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=60,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_carbon_accounting_structure execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_emissions_accounting_method(data):
    try:
        quant = data.get("quantification", {})
        monitoring = data.get("monitoring_reporting", {})
        emissions = data.get("emissions", {})

        input_uncertainties = quant.get("input_uncertainties")
        uncertainty_method = monitoring.get("uncertainty_method")
        stack_method = emissions.get("stack_monitoring_method")

        field_scores = [
            score_boolean_field(
                "quantification.input_uncertainties",
                input_uncertainties,
                30,
                note_if_missing="Input uncertainties are not documented.",
            ),
            score_presence_field(
                "monitoring_reporting.uncertainty_method",
                uncertainty_method,
                35,
                note_if_missing="Uncertainty method is not documented.",
            ),
            score_presence_field(
                "emissions.stack_monitoring_method",
                stack_method,
                35,
                note_if_missing="Emissions monitoring method is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not uncertainty_method:
            status = "non_compliant"
        else:
            status = derive_requirement_status_from_score(
                requirement_score,
                non_compliant_threshold=50,
                compliant_threshold=100,
            )

        return build_logic_result(
            status=status,
            missing_fields=[i["path"] for i in field_scores if i["status"] == "missing"],
            failed_fields=[i["path"] for i in field_scores if i["status"] == "fail"],
            notes=collect_field_score_notes(field_scores),
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_emissions_accounting_method execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )

def eval_lca_approach(data):
    """
    LCA_001 | Life cycle assessment approach documented
    """
    try:
        quant = data.get("quantification", {})
        methodology = data.get("methodology", {})

        lca_performed = quant.get("lca_performed")
        standard = methodology.get("standard")

        field_scores = [
            score_boolean_field(
                "quantification.lca_performed",
                lca_performed,
                70,
                note_if_missing="Life cycle assessment approach is not documented.",
            ),
            score_presence_field(
                "methodology.standard",
                standard,
                30,
                note_if_missing="Methodology standard is not defined.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = lca_performed is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=50,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Life cycle assessment approach is documented.")
        elif status == "partial":
            notes.append("Life cycle assessment approach is partially evidenced but still incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("Life cycle assessment approach is not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_lca_approach execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_lca_scope_coverage(data):
    """
    LCA_002 | Emission sources and sinks included
    """
    try:
        quant = data.get("quantification", {})
        ghg = data.get("ghg_accounting", {})

        lca_performed = quant.get("lca_performed")
        system_boundary_defined = ghg.get("system_boundary_defined")
        storage_emissions_accounted = quant.get("storage_emissions_accounted")

        field_scores = [
            score_boolean_field(
                "quantification.lca_performed",
                lca_performed,
                40,
                note_if_missing="Life cycle assessment has not been evidenced.",
            ),
            score_boolean_field(
                "ghg_accounting.system_boundary_defined",
                system_boundary_defined,
                35,
                note_if_missing="System boundary is not defined.",
            ),
            score_boolean_field(
                "quantification.storage_emissions_accounted",
                storage_emissions_accounted,
                25,
                note_if_missing="Storage-related emissions are not accounted for.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = lca_performed is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=50,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("LCA scope covers key sources and sinks.")
        elif status == "partial":
            notes.append("LCA scope is partially evidenced but still incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("LCA scope does not sufficiently cover key sources and sinks.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_lca_scope_coverage execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_lca_data_sources(data):
    """
    LCA_003 | Input data sources and emission factors documented
    """
    try:
        quant = data.get("quantification", {})

        lca_performed = quant.get("lca_performed")
        input_variables = quant.get("input_variables")
        input_uncertainties = quant.get("input_uncertainties")

        field_scores = [
            score_boolean_field(
                "quantification.lca_performed",
                lca_performed,
                30,
                note_if_missing="Life cycle assessment has not been evidenced.",
            ),
            score_boolean_field(
                "quantification.input_variables",
                input_variables,
                35,
                note_if_missing="Input data sources are not documented.",
            ),
            score_boolean_field(
                "quantification.input_uncertainties",
                input_uncertainties,
                35,
                note_if_missing="Emission factors and/or uncertainty treatment are not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = lca_performed is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=50,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("LCA input data sources and uncertainty treatment are documented.")
        elif status == "partial":
            notes.append("LCA input data documentation is partially evidenced but still incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("LCA input data sources and uncertainty treatment are not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_lca_data_sources execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
        )


def eval_lca_net_removal_logic(data):
    """
    LCA_004 | Net removal calculation logic documented
    """
    try:
        quant = data.get("quantification", {})
        ghg = data.get("ghg_accounting", {})

        lca_performed = quant.get("lca_performed")
        baseline_defined = ghg.get("baseline_defined")
        system_boundary_defined = ghg.get("system_boundary_defined")
        storage_emissions_accounted = quant.get("storage_emissions_accounted")

        field_scores = [
            score_boolean_field(
                "quantification.lca_performed",
                lca_performed,
                30,
                note_if_missing="Life cycle assessment has not been evidenced.",
            ),
            score_boolean_field(
                "ghg_accounting.baseline_defined",
                baseline_defined,
                25,
                note_if_missing="Baseline scenario is not defined.",
            ),
            score_boolean_field(
                "ghg_accounting.system_boundary_defined",
                system_boundary_defined,
                25,
                note_if_missing="System boundary is not defined.",
            ),
            score_boolean_field(
                "quantification.storage_emissions_accounted",
                storage_emissions_accounted,
                20,
                note_if_missing="Storage-related emissions are not accounted for in the net removal logic.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        hard_fail = lca_performed is not True

        status = derive_status_with_hard_gate(
            requirement_score,
            hard_fail=hard_fail,
            non_compliant_threshold=50,
            compliant_threshold=100,
        )

        missing_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "missing"
        ]
        failed_fields = [
            item["path"]
            for item in field_scores
            if item["status"] == "fail"
        ]
        notes = collect_field_score_notes(field_scores)

        if status == "compliant":
            notes.append("Net removal calculation logic is documented.")
        elif status == "partial":
            notes.append("Net removal calculation logic is partially evidenced but still incomplete.")
        elif status == "non_compliant" and not notes:
            notes.append("Net removal calculation logic is not sufficiently evidenced.")

        return build_logic_result(
            status=status,
            missing_fields=missing_fields,
            failed_fields=failed_fields,
            notes=notes,
            requirement_score=requirement_score,
            field_scores=field_scores,
            requirement_rating=requirement_rating,
        )

    except Exception as e:
        return build_logic_result(
            status="error",
            notes=[f"eval_lca_net_removal_logic execution error: {str(e)}"],
            requirement_score=0,
            field_scores=[],
            requirement_rating="weak",
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
    "pyrolysis_gas_end_use_accounting": pyrolysis_gas_end_use_accounting,
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
    "biochar_incorporation_documentation": biochar_incorporation_documentation,
}
