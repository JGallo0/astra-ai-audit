from db import execute, fetch


def create_project_record(
    project_name: str,
    owner_email: str,
    methodology: str,
    project_vector_store_id: str,
    methodology_vector_store_id: str,
    status: str = "active",
):
    query = """
        INSERT INTO projects (
            project_name,
            owner_email,
            methodology,
            project_vector_store_id,
            methodology_vector_store_id,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """
params = (
    (project_name or "").strip(),
    (owner_email or "").strip().lower(),
    (methodology or "").strip().lower(),
    (project_vector_store_id or "").strip(),
    (methodology_vector_store_id or "").strip(),
    status,
    )
    return execute(query, params)


def list_projects_by_owner(owner_email: str):
    query = """
        SELECT id, project_name, methodology,
               project_vector_store_id, methodology_vector_store_id, status, created_at
        FROM projects
        WHERE lower(owner_email) = %s
        ORDER BY created_at DESC
    """
    return fetch(query, (owner_email.strip().lower(),)) or []
