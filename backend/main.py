import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import uuid
from datetime import datetime
import io
import importlib
import psycopg2
import psycopg2.extras

from backend.config import (
    OPENAI_API_KEY, OPENAI_MODEL, FRONTEND_URL, METHODOLOGY_REGISTRY,
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT,
)

from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

try:
    from audit_engine import AuditEngine
    HAS_ENGINE = True
except Exception:
    HAS_ENGINE = False

_audit_runs: dict = {}

# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER,
        password=DB_PASSWORD, port=DB_PORT,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

def _db_execute(sql: str, params=None):
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
    finally:
        conn.close()

def _db_fetch(sql: str, params=None) -> list:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def _db_fetchone(sql: str, params=None) -> Optional[dict]:
    rows = _db_fetch(sql, params)
    return rows[0] if rows else None

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _load_requirements(methodology_key: str) -> list:
    mod_path = METHODOLOGY_REGISTRY.get(methodology_key, {}).get("requirements_module")
    if not mod_path:
        return []
    try:
        mod = importlib.import_module(mod_path)
        return getattr(mod, "REQUIREMENTS", [])
    except Exception:
        return []

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Co2mply API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    try:
        _db_fetchone("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok, "engine": HAS_ENGINE}

# ── Methodologies ─────────────────────────────────────────────────────────────

@app.get("/api/methodologies")
def list_methodologies():
    return [
        {"key": k, "label": v["label"], "version": v["version"]}
        for k, v in METHODOLOGY_REGISTRY.items()
    ]

@app.get("/api/methodologies/{key}/requirements")
def get_requirements(key: str):
    return _load_requirements(key)

# ── Projects ──────────────────────────────────────────────────────────────────

@app.get("/api/projects")
def list_projects():
    return _db_fetch(
        "SELECT * FROM ca_projects ORDER BY created_at DESC"
    )

@app.post("/api/projects")
async def create_project(
    name: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    vs = openai_client.vector_stores.create(name=f"[Co2mply] {name}")
    vs_id = vs.id

    for f in files:
        content = await f.read()
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vs_id,
            file=(f.filename, io.BytesIO(content), f.content_type or "application/octet-stream"),
        )

    project_id = str(uuid.uuid4())
    _db_execute(
        """INSERT INTO ca_projects
           (id, name, project_vector_store_id, doc_count, created_at)
           VALUES (%s, %s, %s, %s, %s)""",
        (project_id, name, vs_id, len(files), _now()),
    )
    return _db_fetchone("SELECT * FROM ca_projects WHERE id = %s", (project_id,))

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    p = _db_fetchone("SELECT * FROM ca_projects WHERE id = %s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")
    return p

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    _db_execute("DELETE FROM ca_projects WHERE id = %s", (project_id,))
    return {"ok": True}

@app.post("/api/projects/{project_id}/documents")
async def upload_documents(project_id: str, files: List[UploadFile] = File(...)):
    p = _db_fetchone("SELECT project_vector_store_id, doc_count FROM ca_projects WHERE id = %s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")
    vs_id = p["project_vector_store_id"]

    for f in files:
        content = await f.read()
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vs_id,
            file=(f.filename, io.BytesIO(content), f.content_type or "application/octet-stream"),
        )

    new_count = (p.get("doc_count") or 0) + len(files)
    _db_execute("UPDATE ca_projects SET doc_count = %s WHERE id = %s", (new_count, project_id))
    return {"uploaded": [f.filename for f in files]}

# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditRequest(BaseModel):
    methodology: str = "isometric"
    modules: Optional[List[str]] = None
    audit_mode: str = "development"   # "development" | "operational"

@app.post("/api/projects/{project_id}/audit")
async def start_audit(project_id: str, req: AuditRequest, background_tasks: BackgroundTasks):
    p = _db_fetchone("SELECT * FROM ca_projects WHERE id = %s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")

    run_id = str(uuid.uuid4())
    _audit_runs[run_id] = {"status": "running", "project_id": project_id, "started_at": _now()}

    _db_execute(
        "INSERT INTO ca_audit_runs (id, project_id, methodology, modules, status, created_at) VALUES (%s,%s,%s,%s,%s,%s)",
        (run_id, project_id, req.methodology, json.dumps(req.modules), "running", _now()),
    )

    background_tasks.add_task(_run_audit, run_id, dict(p), req)
    return {"run_id": run_id, "status": "running"}

def _run_audit(run_id: str, project: dict, req: AuditRequest):
    try:
        methodology_key = req.methodology
        requirements = _load_requirements(methodology_key)
        methodology_vs_id = METHODOLOGY_REGISTRY.get(methodology_key, {}).get("vector_store_id", "")

        if not HAS_ENGINE:
            raise RuntimeError("AuditEngine não disponível.")

        engine = AuditEngine(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            project_vector_store_id=project.get("project_vector_store_id", ""),
            methodology_vector_store_id=methodology_vs_id,
            project_name=project.get("name", ""),
            requirements=requirements,
        )

        # Usa o mesmo método que o Streamlit: motor determinístico estruturado
        output = engine.run_structured_engine_audit(
            selected_modules=req.modules or None,
            audit_mode=req.audit_mode,
        )

        # Remove campos de contexto grandes antes de salvar no banco
        _LARGE_FIELDS = {"project_context", "methodology_context", "project_hits",
                         "methodology_hits", "raw_extraction"}
        result = {k: v for k, v in output.items() if k not in _LARGE_FIELDS}

        _audit_runs[run_id].update({"status": "completed", "result": result})
        _db_execute(
            "UPDATE ca_audit_runs SET status=%s, result=%s, completed_at=%s WHERE id=%s",
            ("completed", json.dumps(result, default=str), _now(), run_id),
        )
    except Exception as e:
        _audit_runs[run_id].update({"status": "error", "error": str(e)})
        _db_execute(
            "UPDATE ca_audit_runs SET status=%s, result=%s WHERE id=%s",
            ("error", json.dumps({"error": str(e)}), run_id),
        )

@app.get("/api/audit/{run_id}")
def get_audit_run(run_id: str):
    if run_id in _audit_runs:
        return _audit_runs[run_id]
    r = _db_fetchone("SELECT * FROM ca_audit_runs WHERE id = %s", (run_id,))
    if not r:
        raise HTTPException(404, "Run não encontrado")
    if isinstance(r.get("result"), str):
        r["result"] = json.loads(r["result"])
    return r

@app.get("/api/projects/{project_id}/audits")
def list_audit_runs(project_id: str):
    rows = _db_fetch(
        "SELECT id, status, methodology, created_at, completed_at FROM ca_audit_runs WHERE project_id=%s ORDER BY created_at DESC",
        (project_id,),
    )
    return rows

@app.get("/api/audit/{run_id}/report")
def download_report(run_id: str, format: str = Query("json")):
    run = _audit_runs.get(run_id)
    if not run:
        r = _db_fetchone("SELECT * FROM ca_audit_runs WHERE id=%s", (run_id,))
        if r:
            result_raw = r.get("result")
            run = {"status": r["status"], "result": json.loads(result_raw) if isinstance(result_raw, str) else result_raw}
    if not run or run.get("status") != "completed":
        raise HTTPException(404, "Auditoria não concluída")

    result = run.get("result", {})

    if format == "json":
        content = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        return StreamingResponse(
            io.BytesIO(content), media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="audit_{run_id}.json"'},
        )
    try:
        from aia import generate_compliance_matrix_pdf, generate_compliance_matrix_docx
        if format == "pdf":
            buf = generate_compliance_matrix_pdf(result)
            return StreamingResponse(io.BytesIO(buf), media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="audit_{run_id}.pdf"'})
        if format == "docx":
            buf = generate_compliance_matrix_docx(result)
            return StreamingResponse(io.BytesIO(buf),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="audit_{run_id}.docx"'})
    except Exception as e:
        raise HTTPException(500, f"Geração de relatório falhou: {e}")
    raise HTTPException(400, "Formato não suportado")

# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None

@app.post("/api/projects/{project_id}/chat")
async def chat(project_id: str, req: ChatRequest):
    p = _db_fetchone("SELECT * FROM ca_projects WHERE id=%s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")

    vs_id = p.get("project_vector_store_id", "")
    method_vs_id = p.get("methodology_vector_store_id", "")

    messages = [{"role": h["role"], "content": h["content"]} for h in (req.history or [])]
    messages.append({"role": "user", "content": req.message})

    try:
        tools = [{"type": "file_search", "vector_store_ids": [v for v in [vs_id, method_vs_id] if v]}]
        response = openai_client.responses.create(model=OPENAI_MODEL, input=messages, tools=tools)
        answer = response.output_text
    except Exception as e:
        answer = f"Erro: {e}"

    _db_execute(
        "INSERT INTO ca_chat_messages (project_id, role, content, created_at) VALUES (%s,%s,%s,%s)",
        (project_id, "user", req.message, _now()),
    )
    _db_execute(
        "INSERT INTO ca_chat_messages (project_id, role, content, created_at) VALUES (%s,%s,%s,%s)",
        (project_id, "assistant", answer, _now()),
    )
    return {"answer": answer}

@app.get("/api/projects/{project_id}/chat/history")
def chat_history(project_id: str):
    return _db_fetch(
        "SELECT role, content, created_at FROM ca_chat_messages WHERE project_id=%s ORDER BY created_at",
        (project_id,),
    )

@app.delete("/api/projects/{project_id}/chat/history")
def clear_chat(project_id: str):
    _db_execute("DELETE FROM ca_chat_messages WHERE project_id=%s", (project_id,))
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
