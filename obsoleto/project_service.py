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
               project_vector_store_id, methodology_vector_store_id,
               status, created_at
        FROM projects
        WHERE lower(owner_email) = %s
        ORDER BY created_at DESC
    """
    return fetch(query, ((owner_email or "").strip().lower(),)) or []

# =========================================================
# CHAT HISTORY
# =========================================================

def save_chat_message(project_id: str, user_email: str, role: str, message: str):
    query = """
        INSERT INTO chat_history (
            project_id,
            user_email,
            role,
            message
        )
        VALUES (%s, %s, %s, %s)
    """
    params = (
        project_id,
        (user_email or "").strip().lower(),
        (role or "").strip().lower(),
        message or "",
    )
    return db_execute(query, params)


def load_chat_history(project_id: str, user_email: str):
    query = """
        SELECT role, message
        FROM chat_history
        WHERE project_id = %s
          AND lower(user_email) = %s
        ORDER BY created_at ASC
    """
    params = (
        project_id,
        (user_email or "").strip().lower(),
    )
    return db_fetch(query, params) or []


# =========================================================
# AUDIT OUTPUTS
# =========================================================

def save_audit_output(
    project_id: str,
    user_email: str,
    output_type: str,
    title: str = "",
    question: str = "",
    answer: str = "",
    content: str = "",
):
    query = """
        INSERT INTO audit_outputs (
            project_id,
            user_email,
            output_type,
            title,
            question,
            answer,
            content
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        project_id,
        (user_email or "").strip().lower(),
        (output_type or "").strip(),
        title or "",
        question or "",
        answer or "",
        content or "",
    )
    return db_execute(query, params)


def list_audit_outputs(project_id: str, user_email: str):
    query = """
        SELECT *
        FROM audit_outputs
        WHERE project_id = %s
          AND lower(user_email) = %s
        ORDER BY created_at DESC
    """
    params = (
        project_id,
        (user_email or "").strip().lower(),
    )
    return db_fetch(query, params) or []
