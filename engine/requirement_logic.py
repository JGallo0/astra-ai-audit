def run_engine(project_data, requirements):
    results = []

    for req in requirements:
        logic_fn = get_logic(req["logic"])
        status = logic_fn(project_data)

        results.append({
            "id": req["id"],
            "status": status
        })

    return results
