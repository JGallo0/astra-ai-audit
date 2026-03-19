def create_project(
    supabase,
    project_name: str,
    owner_email: str,
    methodology: str,
    project_vector_store_id: str,
    methodology_vector_store_id: str,
    status: str = "active",
):
    payload = {
        "project_name": project_name.strip(),
        "owner_email": owner_email.strip().lower(),
        "methodology": methodology.strip().lower(),
        "project_vector_store_id": project_vector_store_id.strip(),
        "methodology_vector_store_id": methodology_vector_store_id.strip(),
        "status": status,
    }

    return supabase.table("projects").insert(payload).execute()


def list_projects_by_owner(supabase, owner_email: str):
    response = (
        supabase.table("projects")
        .select("*")
        .eq("owner_email", owner_email.strip().lower())
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []
