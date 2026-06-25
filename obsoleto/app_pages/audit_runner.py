from audit_engine import AuditEngine
from app_pages.validation_utils import build_audit_dataframe


def execute_full_audit(
    api_key,
    model,
    requirements,
    project_vector_store_id,
    methodology_vector_store_id,
    project_name,
    engine_params,
    selected_modules,
    callback,
):
    engine = AuditEngine(
        api_key=api_key,
        model=model,
        requirements=requirements,
        project_vector_store_id=project_vector_store_id,
        methodology_vector_store_id=methodology_vector_store_id,
        project_name=project_name,
        module_project_queries=engine_params["module_project_queries"],
        module_methodology_queries=engine_params["module_methodology_queries"],
        project_max_results_per_query=engine_params["project_max_results_per_query"],
        methodology_max_results_per_query=engine_params["methodology_max_results_per_query"],
        max_project_hits_in_prompt=engine_params["max_project_hits_in_prompt"],
        max_methodology_hits_in_prompt=engine_params["max_methodology_hits_in_prompt"],
        max_text_chars_per_hit=engine_params["max_text_chars_per_hit"],
        progress_callback=callback,
    )

    audit_output = engine.run_full_audit(
        selected_modules=selected_modules,
        enable_auto_reanalysis=True,
    )

    results = audit_output["results"]
    trails = audit_output["trails"]
    summary = engine.summarize_results(results)
    df = build_audit_dataframe(results)

    return {
        "engine": engine,
        "audit_output": audit_output,
        "results": results,
        "trails": trails,
        "summary": summary,
        "df": df,
    }


def execute_rerun_failures(
    api_key,
    model,
    requirements,
    project_vector_store_id,
    methodology_vector_store_id,
    project_name,
    selected_modules,
    previous_results,
    callback,
):
    engine = AuditEngine(
        api_key=api_key,
        model=model,
        requirements=requirements,
        project_vector_store_id=project_vector_store_id,
        methodology_vector_store_id=methodology_vector_store_id,
        project_name=project_name,
        module_project_queries=3,
        module_methodology_queries=3,
        project_max_results_per_query=4,
        methodology_max_results_per_query=4,
        max_project_hits_in_prompt=5,
        max_methodology_hits_in_prompt=5,
        max_text_chars_per_hit=1100,
        progress_callback=callback,
    )

    rerun_output = engine.rerun_failed_items(
        previous_results=previous_results,
        selected_modules=selected_modules,
    )

    rerun_results = rerun_output["results"]
    prev_by_id = {str(x.get("requirement_id", "")): x for x in previous_results}

    for item in rerun_results:
        prev_by_id[str(item.get("requirement_id", ""))] = item

    merged_results = list(prev_by_id.values())
    merged_results = sorted(
        merged_results,
        key=lambda x: (str(x.get("module", "")), str(x.get("requirement_id", "")))
    )

    summary = engine.summarize_results(merged_results)
    df = build_audit_dataframe(merged_results)

    return {
        "engine": engine,
        "rerun_output": rerun_output,
        "rerun_results": rerun_results,
        "merged_results": merged_results,
        "summary": summary,
        "df": df,
    }
