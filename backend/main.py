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

def _load_requirements(methodology_key: str, engine_version: str = "v1") -> list:
    """
    Carrega requisitos para a metodologia.

    engine_version:
      "v1"     → R-XXXX IDs, protocol-native (padrão para Isometric)
      "legacy" → ELIG_001 IDs, motor original
    """
    try:
        from methodology_requirements import get_requirements_for_methodology
        from engine.requirement_logic_map import REQUIREMENT_LOGIC_MAP
        from engine.requirement_logic_map_v1 import REQUIREMENT_LOGIC_MAP_V1

        logic_map = REQUIREMENT_LOGIC_MAP_V1 if engine_version == "v1" else REQUIREMENT_LOGIC_MAP
        raw = get_requirements_for_methodology(methodology_key, engine_version=engine_version)
        requirements = []
        for req in raw:
            r = dict(req)
            req_id = r.get("id") or r.get("requirement_id")
            r["logic"] = logic_map.get(req_id)
            requirements.append(r)
        return requirements
    except Exception as e:
        print(f"[_load_requirements] erro: {e}")
        return []

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Co2mply API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_origin_regex=r"https://.*\.vercel\.app",
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

@app.post("/api/projects/{project_id}/reset-cache")
def reset_project_data_cache(project_id: str):
    """Invalida o cache de project_data — próxima auditoria fará nova extração LLM."""
    _db_execute(
        "UPDATE ca_projects SET project_data = NULL WHERE id = %s", (project_id,)
    )
    return {"ok": True, "message": "Cache invalidado. Próxima auditoria fará nova extração."}

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
    # Invalida cache de project_data — novos documentos exigem nova extração
    _db_execute(
        "UPDATE ca_projects SET doc_count = %s, project_data = NULL WHERE id = %s",
        (new_count, project_id),
    )
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

        # ── Cache de project_data ─────────────────────────────────────────────
        # Se já foi extraído antes, reutiliza → auditoria 100% determinística
        # Se não, extrai via LLM (temperature=0) e salva para próximas vezes
        project_id = project["id"]
        cached_pd_row = _db_fetchone(
            "SELECT project_data FROM ca_projects WHERE id = %s", (project_id,)
        )
        cached_project_data = (cached_pd_row or {}).get("project_data")
        cache_hit = cached_project_data is not None

        engine = AuditEngine(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            project_vector_store_id=project.get("project_vector_store_id", ""),
            methodology_vector_store_id=methodology_vs_id,
            project_name=project.get("name", ""),
            requirements=requirements,
        )

        output = engine.run_structured_engine_audit(
            selected_modules=req.modules or None,
            audit_mode=req.audit_mode,
            cached_project_data=cached_project_data,
        )

        # Salva project_data no cache se foi uma extração nova
        if not cache_hit and output.get("project_data"):
            _db_execute(
                "UPDATE ca_projects SET project_data = %s WHERE id = %s",
                (json.dumps(output["project_data"], default=str), project_id),
            )

        # Remove campos de contexto grandes antes de salvar no banco
        _LARGE_FIELDS = {"project_context", "methodology_context", "project_hits",
                         "methodology_hits", "raw_extraction"}
        result = {k: v for k, v in output.items() if k not in _LARGE_FIELDS}
        result["cache_hit"] = cache_hit  # útil para debug no frontend

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
        return {"id": run_id, **_audit_runs[run_id]}  # id sempre presente
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

_STATUS_LABELS = {
    "compliant": "Conforme",
    "partial": "Parcial",
    "non_compliant": "Não conforme",
    "not_applicable": "N/A",
    "future_evidence_required": "Evidência futura",
    "error": "Erro",
}

def _build_matrix_text(results: list, score: float, score_label: str, mode_label: str) -> str:
    """Gera texto limpo da Compliance Matrix sem redundâncias."""
    counts = {}
    for r in results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    lines = [
        f"Score de Conformidade: {score:.1f}% — {score_label} | Modo: {mode_label}",
        "",
        f"Conformes: {counts.get('compliant', 0)}  |  "
        f"Parciais: {counts.get('partial', 0) + counts.get('future_evidence_required', 0)}  |  "
        f"Não conformes: {counts.get('non_compliant', 0)}  |  "
        f"N/A (operacional): {counts.get('not_applicable', 0)}",
        "",
        "─" * 60,
        "",
    ]

    for r in results:
        status = r.get("status", "")
        status_label = _STATUS_LABELS.get(status, status)
        req_score = r.get("requirement_score")
        score_str = "N/A" if (status == "not_applicable" or req_score is None) else f"{float(req_score):.0f}"
        risk = r.get("risk", "") or ""

        lines.append(f"## {r.get('requirement_id', '')} — {r.get('title', '')}")
        lines.append(f"Status: {status_label}  |  Risco: {risk}  |  Score: {score_str}")

        _GENERIC = {
            "Maintain current evidence and proceed to validation readiness.",
            "Partial evidence available; some required elements are incomplete.",
            "Core requirement not met or insufficiently evidenced.",
            "Provide missing documentation and strengthen evidence for identified gaps.",
            "Strengthen consistency and completeness of existing evidence.",
            "Establish missing core elements required for compliance.",
            "Correct failed conditions and provide full supporting evidence before validation.",
            "Providencie esta evidência quando o projeto estiver operacional.",
        }

        # Gap — só se específico
        gap = (r.get("gap") or "").strip()
        if gap and gap not in _GENERIC:
            lines.append(f"Gap: {gap}")

        # Recommendation — só se específica
        rec = (r.get("recommendation") or "").strip()
        if rec and rec not in _GENERIC:
            lines.append(f"Recomendação: {rec}")

        # Notes — limpar e mostrar
        notes = r.get("notes") or []
        if isinstance(notes, list):
            clean = [n for n in notes if n and not n.startswith("[Protocolo]") and "desenvolvimento:" not in n.lower() and "operacional:" not in n.lower()]
            if clean:
                for n in clean[:2]:  # máx 2 notas por item
                    lines.append(f"• {n}")
        elif isinstance(notes, str) and notes.strip():
            lines.append(f"• {notes}")

        lines.append("")

    return "\n".join(lines)


@app.get("/api/audit/{run_id}/report")
def download_report(run_id: str, format: str = Query("json")):
    run = _audit_runs.get(run_id)
    if not run:
        r = _db_fetchone("SELECT * FROM ca_audit_runs WHERE id=%s", (run_id,))
        if r:
            result_raw = r.get("result")
            run = {
                "id": r["id"],
                "status": r["status"],
                "result": json.loads(result_raw) if isinstance(result_raw, str) else result_raw,
            }
    if not run or run.get("status") != "completed":
        raise HTTPException(404, "Auditoria não concluída")

    result = run.get("result", {})
    results_list = result.get("results", result.get("findings", []))
    score_data  = result.get("score_data", {})
    audit_mode  = result.get("audit_mode", "development")
    score_label = result.get("score_label", "")

    if format == "json":
        content = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        return StreamingResponse(
            io.BytesIO(content), media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="audit_{run_id}.json"'},
        )

    try:
        from app_pages.validation_utils import (
            build_audit_dataframe,
            matrix_to_pdf_bytes,
            matrix_to_docx_bytes,
            build_full_audit_text,
            pdf_from_text_branded,
            docx_from_text,
        )

        # ── Compliance Matrix (PDF / DOCX) ────────────────────────────────
        if format in ("pdf", "docx"):
            score_val  = score_data.get("score", 0)
            mode_label = "Desenvolvimento" if audit_mode == "development" else "Operacional"

            if format == "pdf":
                # Buscar nome real do projeto no banco
                proj_name = "Projeto CO2mply"
                proj_id = run.get("project_id") or result.get("project_id")
                if proj_id:
                    proj_row = _db_fetchone(
                        "SELECT name FROM ca_projects WHERE id=%s", (proj_id,)
                    )
                    if proj_row and proj_row.get("name"):
                        proj_name = proj_row["name"]
                # Fallback: project.name do project_data (não certification_scheme)
                if proj_name == "Projeto CO2mply":
                    pd = result.get("project_data", {})
                    pname = pd.get("project", {}).get("name")
                    if pname and isinstance(pname, str) and len(pname) < 60:
                        proj_name = pname

                from backend.report_generator import generate_compliance_matrix_pdf
                buf = generate_compliance_matrix_pdf(
                    results=results_list,
                    score_data={**score_data, "score_label": score_label},
                    audit_mode=audit_mode,
                    project_name=proj_name,
                )
                return StreamingResponse(
                    io.BytesIO(buf), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="compliance_matrix_{run_id}.pdf"'},
                )
            else:
                # DOCX: usa texto limpo
                title = f"CO2mply | Compliance Matrix — {score_label} ({score_val:.1f}%) [{mode_label}]"
                matrix_text = _build_matrix_text(results_list, score_val, score_label, mode_label)
                buf = docx_from_text(title, matrix_text)
                return StreamingResponse(
                    io.BytesIO(buf),
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="compliance_matrix_{run_id}.docx"'},
                )

        # ── Audit Summary (PDF text) ──────────────────────────────────────
        if format == "summary_pdf":
            from scoring import summarize_results
            summary = summarize_results(results_list)
            text = build_full_audit_text(summary, results_list)
            buf = pdf_from_text_branded(
                f"CO2mply | Audit Summary", text, brand_name="CO2mply"
            )
            return StreamingResponse(
                io.BytesIO(buf), media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="audit_summary_{run_id}.pdf"'},
            )

        # ── Audit Summary (DOCX) ─────────────────────────────────────────
        if format == "summary_docx":
            from scoring import summarize_results
            summary = summarize_results(results_list)
            text = build_full_audit_text(summary, results_list)
            buf = docx_from_text("CO2mply | Audit Summary", text)
            return StreamingResponse(
                io.BytesIO(buf),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="audit_summary_{run_id}.docx"'},
            )

    except Exception as e:
        raise HTTPException(500, f"Geração de relatório falhou: {e}")

    raise HTTPException(400, f"Formato não suportado: {format}. Use: json, pdf, docx, summary_pdf, summary_docx")

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
