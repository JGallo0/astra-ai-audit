def eval_project_ownership(data):
    try:
        project = data.get("project", {})

        country = project.get("country")
        locations = project.get("locations")
        ownership_evidence = project.get("ownership_evidence")

        field_scores = [
            score_presence_field(
                "project.country",
                country,
                25,
                note_if_missing="Project country is not documented.",
            ),
            score_presence_field(
                "project.locations",
                locations,
                25,
                note_if_missing="Project locations are not documented.",
            ),
            score_presence_field(
                "project.ownership_evidence",
                ownership_evidence,
                50,
                note_if_missing="Ownership evidence is not documented.",
            ),
        ]

        requirement_score = summarize_field_scores(field_scores)
        requirement_rating = derive_requirement_rating(requirement_score)

        if not ownership_evidence:
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

        field_scores = [
            score_boolean_field(
                "traceability.chain_of_custody_diagram",
                chain_diagram,
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

        if chain_diagram is not True:
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

        if system_boundary is not True:
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
