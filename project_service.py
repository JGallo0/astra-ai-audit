from db import db_execute, db_fetch


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
        project_name.strip(),
        owner_email.strip().lower(),
        methodology.strip().lower(),
        project_vector_store_id.strip(),
        methodology_vector_store_id.strip(),
        status,
    )
    return db_execute(query, params)


def list_projects_by_owner(owner_email: str):
    query = """
        SELECT id, project_name, methodology,
               project_vector_store_id, methodology_vector_store_id, status, created_at
        FROM projects
        WHERE lower(owner_email) = %s
        ORDER BY created_at DESC
    """
    return db_fetch(query, (owner_email.strip().lower(),)) or []
