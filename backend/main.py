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

        from engine.requirement_logic_map_puro_v2025 import REQUIREMENT_LOGIC_MAP_PURO_V2025
        if engine_version == "v1":
            logic_map = REQUIREMENT_LOGIC_MAP_PURO_V2025 if methodology_key == "puro_earth" else REQUIREMENT_LOGIC_MAP_V1
        else:
            logic_map = REQUIREMENT_LOGIC_MAP
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
            methodology_key=methodology_key,   # ← passa a metodologia para extração de profile
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
        result["cache_hit"] = cache_hit

        # Calcular Project Readiness Rating
        try:
            from backend.rating_service import compute_readiness_rating
            rating = compute_readiness_rating(
                results=output.get("results", []),
                overall_score=float(output.get("score_data", {}).get("score", 0)),
                audit_mode=req.audit_mode,
            )
            result["readiness_rating"] = rating
        except Exception as e:
            result["readiness_rating"] = None
            print(f"[rating] erro: {e}")

        # Validação climática via Copernicus C3S (stl1 + swvl1)
        # Executada sempre que há coordenadas — independente do modo de auditoria
        try:
            from backend.copernicus_service import validate_project_soil_conditions
            project_data_for_c3s = output.get("project_data", cached_project_data or {})
            if project_data_for_c3s:
                climate = validate_project_soil_conditions(project_data_for_c3s)
                result["climate_validation"] = climate
                print(f"[C3S] status={climate.get('status')} lat={climate.get('lat')} lon={climate.get('lon')}")
            else:
                result["climate_validation"] = {"status": "no_project_data"}
        except Exception as e:
            result["climate_validation"] = {"status": "error", "message": str(e)}
            print(f"[C3S] erro: {e}")

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

    # Detecta metodologia — do run (banco) ou dos IDs dos requisitos
    methodology_key = run.get("methodology") or result.get("methodology_key", "")
    if not methodology_key and results_list:
        first_id = (results_list[0].get("requirement_id") or "")
        methodology_key = "puro_earth" if first_id.startswith("P-") else "isometric"
    _METHODOLOGY_LABELS = {
        "isometric":  "Isometric Biochar v1.2",
        "puro_earth": "Puro.Earth Biochar Edition 2025",
        "rainbow":    "Rainbow Carbon",
        "c_sink":     "Global C-SINK / CSI-EBI",
        "verra_vcs":  "Verra VCS",
    }
    methodology_label = _METHODOLOGY_LABELS.get(methodology_key, "Isometric Biochar")

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

        # ── Nome do projeto (usado em todos os formatos) ──────────────────
        proj_name = "Projeto CO2mply"
        proj_id = run.get("project_id") or result.get("project_id")
        if proj_id:
            proj_row = _db_fetchone("SELECT name FROM ca_projects WHERE id=%s", (proj_id,))
            if proj_row and proj_row.get("name"):
                proj_name = proj_row["name"]
        if proj_name == "Projeto CO2mply":
            pd = result.get("project_data", {})
            pname = pd.get("project", {}).get("name")
            if pname and isinstance(pname, str) and len(pname) < 60:
                proj_name = pname

        # ── Rating (extrair do resultado ou calcular on-the-fly) ─────────
        rating_data = result.get("rating") or result.get("readiness_rating")
        if not rating_data and results_list and score_data:
            try:
                from backend.rating_service import compute_readiness_rating
                rating_data = compute_readiness_rating(results_list, float(score_data.get("score", 0)), audit_mode)
            except Exception:
                rating_data = None

        # ── Compliance Matrix (PDF / DOCX) ────────────────────────────────
        if format in ("pdf", "docx"):
            score_val  = score_data.get("score", 0)
            mode_label = "Desenvolvimento" if audit_mode == "development" else "Operacional"

            if format == "pdf":
                from backend.report_generator import generate_compliance_matrix_pdf
                buf = generate_compliance_matrix_pdf(
                    results=results_list,
                    score_data={**score_data, "score_label": score_label},
                    audit_mode=audit_mode,
                    project_name=proj_name,
                    methodology=methodology_label,
                    rating=rating_data,
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

        # ── Audit Summary (PDF executivo) ─────────────────────────────────
        if format == "summary_pdf":
            from backend.report_generator import generate_audit_summary_pdf
            buf = generate_audit_summary_pdf(
                results=results_list,
                score_data={**score_data, "score_label": score_label},
                audit_mode=audit_mode,
                project_name=proj_name,
                methodology=methodology_label,
                rating=rating_data,
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

        # ── Project Readiness Certificate ─────────────────────────────────
        if format == "certificate":
            rating = result.get("readiness_rating")
            if not rating:
                raise HTTPException(404, "Rating não disponível — execute uma auditoria primeiro.")
            from backend.report_generator import generate_readiness_certificate_pdf
            buf = generate_readiness_certificate_pdf(
                rating=rating,
                project_name=proj_name,
                methodology=methodology_label,
            )
            return StreamingResponse(
                io.BytesIO(buf), media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="readiness_certificate_{run_id}.pdf"'},
            )

    except Exception as e:
        raise HTTPException(500, f"Geração de relatório falhou: {e}")

    raise HTTPException(400, f"Formato não suportado: {format}. Use: json, pdf, summary_pdf, certificate")

# ── Viabilidade ───────────────────────────────────────────────────────────────

@app.on_event("startup")
def _create_viabilidade_table():
    try:
        _db_execute("""
            CREATE TABLE IF NOT EXISTS ca_viabilidade (
                project_id TEXT PRIMARY KEY,
                premissas  JSONB,
                resultado  JSONB,
                fonte      TEXT,
                cenarios   JSONB DEFAULT '[]',
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        _db_execute("ALTER TABLE ca_viabilidade ADD COLUMN IF NOT EXISTS cenarios JSONB DEFAULT '[]'")
    except Exception:
        pass

@app.get("/api/projects/{project_id}/viabilidade")
def get_viabilidade(project_id: str):
    row = _db_fetchone("SELECT * FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    if not row:
        return {"premissas": None, "resultado": None}
    for key in ("premissas", "resultado"):
        if isinstance(row.get(key), str):
            try: row[key] = json.loads(row[key])
            except: pass
    return row

@app.post("/api/projects/{project_id}/viabilidade/calculate")
def calculate_viabilidade(project_id: str, body: dict):
    from backend.viabilidade_engine import PremissasViabilidade, calcular_viabilidade, premissas_from_dict, validate_premissas
    p = premissas_from_dict(body.get("premissas", body))
    resultado = calcular_viabilidade(p)
    fonte = body.get("fonte", "manual")
    premissas_dict = {f.name: getattr(p, f.name) for f in __import__('dataclasses').fields(p)}
    _db_execute(
        """INSERT INTO ca_viabilidade (project_id, premissas, resultado, fonte, updated_at)
           VALUES (%s,%s,%s,%s,now())
           ON CONFLICT (project_id) DO UPDATE
           SET premissas=EXCLUDED.premissas, resultado=EXCLUDED.resultado,
               fonte=EXCLUDED.fonte, updated_at=now()""",
        (project_id, json.dumps(premissas_dict, default=str),
         json.dumps(resultado, default=str), fonte),
    )
    warnings = validate_premissas(premissas_dict)
    return {"resultado": resultado, "warnings": warnings, "premissas": premissas_dict}

@app.post("/api/projects/{project_id}/viabilidade/extract")
async def extract_viabilidade(project_id: str, file: UploadFile = File(...)):
    from backend.viabilidade_service import extract_premissas_from_spreadsheet
    content = await file.read()
    extracted = extract_premissas_from_spreadsheet(
        content, file.filename, openai_client, OPENAI_MODEL
    )
    from backend.viabilidade_engine import validate_premissas
    warnings = validate_premissas(extracted)
    return {"extracted": extracted, "warnings": warnings}

@app.get("/api/projects/{project_id}/viabilidade/cenarios")
def list_cenarios(project_id: str):
    row = _db_fetchone("SELECT cenarios FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    raw = (row or {}).get("cenarios") or []
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except: raw = []
    return raw

@app.post("/api/projects/{project_id}/viabilidade/cenarios")
def save_cenario(project_id: str, body: dict):
    row = _db_fetchone("SELECT cenarios FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    if not row:
        raise HTTPException(404, "Calcule a viabilidade antes de salvar um cenário.")
    raw = row.get("cenarios") or []
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except: raw = []
    cenarios = [c for c in raw if c.get("nome") != body.get("nome")]
    cenarios.append({
        "nome":      body.get("nome", "Cenário"),
        "premissas": body.get("premissas", {}),
        "resultado": body.get("resultado", {}),
        "created_at": _now(),
    })
    _db_execute(
        "UPDATE ca_viabilidade SET cenarios=%s WHERE project_id=%s",
        (json.dumps(cenarios, default=str), project_id),
    )
    return {"ok": True, "total": len(cenarios)}

@app.delete("/api/projects/{project_id}/viabilidade/cenarios/{nome}")
def delete_cenario(project_id: str, nome: str):
    row = _db_fetchone("SELECT cenarios FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    raw = (row or {}).get("cenarios") or []
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except: raw = []
    cenarios = [c for c in raw if c.get("nome") != nome]
    _db_execute(
        "UPDATE ca_viabilidade SET cenarios=%s WHERE project_id=%s",
        (json.dumps(cenarios, default=str), project_id),
    )
    return {"ok": True}

@app.get("/api/projects/{project_id}/viabilidade/memo")
def download_memo(project_id: str):
    row = _db_fetchone("SELECT * FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    if not row:
        raise HTTPException(404, "Viabilidade não calculada para este projeto.")
    premissas = row.get("premissas") or {}
    resultado  = row.get("resultado") or {}
    if isinstance(premissas, str): premissas = json.loads(premissas)
    if isinstance(resultado, str):  resultado  = json.loads(resultado)
    proj = _db_fetchone("SELECT name FROM ca_projects WHERE id=%s", (project_id,))
    proj_name = (proj or {}).get("name", "Projeto")
    from backend.viabilidade_service import generate_financial_memo_pdf
    buf = generate_financial_memo_pdf(premissas, resultado, proj_name)
    return StreamingResponse(
        io.BytesIO(buf), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="memo_{project_id[:8]}.pdf"'},
    )

@app.get("/api/projects/{project_id}/viabilidade/export")
def export_viabilidade(project_id: str):
    row = _db_fetchone("SELECT * FROM ca_viabilidade WHERE project_id=%s", (project_id,))
    if not row:
        raise HTTPException(404, "Viabilidade não calculada para este projeto")
    premissas = row.get("premissas") or {}
    resultado  = row.get("resultado")  or {}
    if isinstance(premissas, str): premissas = json.loads(premissas)
    if isinstance(resultado, str):  resultado  = json.loads(resultado)
    proj = _db_fetchone("SELECT name FROM ca_projects WHERE id=%s", (project_id,))
    proj_name = (proj or {}).get("name", "Projeto")
    from backend.viabilidade_service import generate_viabilidade_excel
    buf = generate_viabilidade_excel(premissas, resultado, proj_name)
    filename = f"viabilidade_{project_id[:8]}.xlsx"
    return StreamingResponse(
        io.BytesIO(buf), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ── Methodology Assessment (Fit Metodológico Multi-Metodologia) ───────────────

@app.post("/api/projects/{project_id}/assessment")
async def run_assessment(project_id: str, body: dict):
    """
    Avalia o projeto contra todas as metodologias disponíveis com ProjectProfile
    padronizado e dimensões universais comparáveis.
    Body: { "methodologies": ["isometric", "puro_earth"], "audit_mode": "development" }
    """
    p = _db_fetchone("SELECT * FROM ca_projects WHERE id=%s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")

    methodologies = body.get("methodologies") or ["isometric", "puro_earth"]
    audit_mode    = body.get("audit_mode", "development")
    vs_id         = p.get("project_vector_store_id", "")

    # Extrai texto do PDD via RAG
    try:
        tools = [{"type": "file_search", "vector_store_ids": [vs_id]}] if vs_id else []
        rag = openai_client.responses.create(
            model=OPENAI_MODEL,
            input=(
                "Extract the complete project description from this PDD including: "
                "project name, country, feedstock type and origin, production process, "
                "storage pathway, additionality evidence, carbon accounting approach, "
                "permanence/durability, monitoring plan, environmental and social safeguards, "
                "reactor design, biochar characterization, and any certifications mentioned."
            ),
            tools=tools,
        )
        pdd_text = rag.output_text or ""
    except Exception as e:
        pdd_text = f"[RAG falhou: {e}] Projeto: {p.get('name', '')}"

    # Busca project_data do banco — usado para Isometric (extração nativa)
    cached_pd = None
    try:
        pd_row = _db_fetchone("SELECT project_data FROM ca_projects WHERE id=%s", (project_id,))
        raw = (pd_row or {}).get("project_data")
        if raw:
            cached_pd = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass

    from backend.assessment_service import run_methodology_assessment
    result = await run_methodology_assessment(
        project_id=project_id,
        pdd_text=pdd_text,
        methodologies=methodologies,
        openai_client=openai_client,
        model=OPENAI_MODEL,
        audit_mode=audit_mode,
        cached_project_data=cached_pd,
    )

    # Salva no banco
    _db_execute(
        """INSERT INTO ca_audit_runs (id, project_id, methodology, modules, status, result, created_at, completed_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            __import__('uuid').uuid4().__str__(),
            project_id, "assessment", json.dumps(methodologies), "completed",
            json.dumps(result, default=str), _now(), _now(),
        ),
    )
    return result

# ── Credit Volume Estimation ──────────────────────────────────────────────────

@app.post("/api/projects/{project_id}/credit-volume")
def estimate_credit_volume(project_id: str, body: dict):
    """
    Estima volume de créditos de carbono por metodologia (Module 1 — Sylvera approach).
    Body: CreditVolumeInputs como dict, mais campo 'climate_data' opcional do Copernicus.
    """
    try:
        from engine.credit_volume_engine import CreditVolumeInputs, compare_methodologies, inputs_from_viabilidade

        # Tenta usar project_data ou viabilidade para preencher defaults
        climate = body.pop("climate_data", None)

        # Se vier de viabilidade (premissas), constrói automaticamente
        if "premissas" in body:
            premissas = body["premissas"]
            inputs = inputs_from_viabilidade(premissas, climate)
            # Sobrescreve com campos explícitos do body se fornecidos
            for field in ["h_c_ratio", "o_c_ratio", "carbon_fraction", "mast_celsius",
                           "pyrolysis_temp_celsius", "transport_km_feedstock",
                           "transport_km_biochar", "methodologies"]:
                if field in body:
                    setattr(inputs, field, body[field])
        else:
            # Constrói direto dos inputs
            valid = {f.name for f in __import__('dataclasses').fields(CreditVolumeInputs)}
            kwargs = {k: v for k, v in body.items() if k in valid}
            inputs = CreditVolumeInputs(**kwargs)

        result = compare_methodologies(inputs)
        return result

    except Exception as e:
        raise HTTPException(400, f"Erro no cálculo de volume de créditos: {e}")

# ── Verificação (V&V Support) ──────────────────────────────────────────────────

@app.get("/api/projects/{project_id}/verificacao")
def get_verificacao(project_id: str, role: str = Query("developer"), methodology: str = Query("isometric")):
    # Latest completed audit
    run = _db_fetchone(
        "SELECT result FROM ca_audit_runs WHERE project_id=%s AND status='completed' ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    )
    if not run:
        raise HTTPException(404, "Nenhuma auditoria concluída para este projeto. Execute uma auditoria primeiro.")
    result_raw = run.get("result") or {}
    if isinstance(result_raw, str):
        result_raw = json.loads(result_raw)
    audit_results = result_raw.get("results", result_raw.get("findings", []))
    if not audit_results:
        raise HTTPException(404, "Resultado de auditoria sem dados de requisitos.")

    from backend.verificacao_service import build_developer_plan, build_vvb_plan

    if role == "vvb":
        reqs = _load_requirements(methodology)
        return build_vvb_plan(reqs, audit_results)
    else:
        return build_developer_plan(audit_results)

# ── Dashboard Stats ───────────────────────────────────────────────────────────

@app.get("/api/dashboard/portfolio")
def dashboard_portfolio():
    """Projetos enriquecidos com dados da última auditoria — para portfolio view."""
    projects = _db_fetch("SELECT * FROM ca_projects ORDER BY created_at DESC")
    for p in projects:
        run = _db_fetchone(
            """SELECT id, result, completed_at, audit_mode
               FROM ca_audit_runs
               WHERE project_id=%s AND status='completed'
               ORDER BY created_at DESC LIMIT 1""",
            (p["id"],),
        )
        if run:
            res = run.get("result") or {}
            if isinstance(res, str):
                try: res = json.loads(res)
                except: res = {}
            rating = res.get("readiness_rating") or {}
            score  = (res.get("score_data") or {}).get("score")
            p["last_audit"] = {
                "id":           run["id"],
                "grade":        rating.get("grade"),
                "label":        rating.get("label"),
                "score":        round(float(score), 1) if score is not None else None,
                "audit_mode":   res.get("audit_mode", run.get("audit_mode", "development")),
                "completed_at": str(run.get("completed_at") or ""),
            }
        else:
            p["last_audit"] = None
    return projects

@app.get("/api/dashboard/stats")
def dashboard_stats():
    rows = _db_fetch("SELECT result FROM ca_audit_runs WHERE status='completed'")
    scores = []
    for r in rows:
        res = r.get("result") or {}
        if isinstance(res, str):
            try: res = json.loads(res)
            except: continue
        score = (res.get("score_data") or {}).get("score")
        if score is not None:
            try: scores.append(float(score))
            except: pass
    return {
        "total_audits": len(rows),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
    }

# ── Documents (Data Room) ──────────────────────────────────────────────────────

@app.get("/api/projects/{project_id}/documents")
def list_documents(project_id: str):
    p = _db_fetchone("SELECT project_vector_store_id FROM ca_projects WHERE id=%s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")
    vs_id = p.get("project_vector_store_id", "")
    if not vs_id:
        return []
    try:
        vs_files = openai_client.vector_stores.files.list(vector_store_id=vs_id)
    except Exception as e:
        raise HTTPException(500, f"Erro ao listar arquivos: {e}")
    docs = []
    for vf in vs_files.data:
        try:
            fi = openai_client.files.retrieve(vf.id)
            docs.append({
                "file_id": vf.id,
                "filename": fi.filename,
                "size_bytes": fi.bytes,
                "status": vf.status,
                "created_at": vf.created_at,
            })
        except Exception:
            docs.append({"file_id": vf.id, "filename": vf.id, "size_bytes": 0, "status": vf.status, "created_at": vf.created_at})
    docs.sort(key=lambda d: d.get("created_at") or 0, reverse=True)
    return docs

@app.delete("/api/projects/{project_id}/documents/{file_id}")
def delete_document(project_id: str, file_id: str):
    p = _db_fetchone("SELECT project_vector_store_id, doc_count FROM ca_projects WHERE id=%s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")
    vs_id = p.get("project_vector_store_id", "")
    try:
        openai_client.vector_stores.files.delete(vector_store_id=vs_id, file_id=file_id)
    except Exception:
        pass
    try:
        openai_client.files.delete(file_id)
    except Exception:
        pass
    new_count = max(0, (p.get("doc_count") or 1) - 1)
    _db_execute(
        "UPDATE ca_projects SET doc_count=%s, project_data=NULL WHERE id=%s",
        (new_count, project_id),
    )
    return {"ok": True}

# ── Pré-Viabilidade (Screening) ────────────────────────────────────────────────

_METHODOLOGY_SCREENING: dict = {
    "isometric": {
        "name": "Isometric Biochar v1.2",
        "criteria": [
            {"id": "feedstock",     "label": "Feedstock elegível",        "desc": "Biomassa residual ou resíduos (não culturas dedicadas para energia)"},
            {"id": "process",       "label": "Processo de conversão",     "desc": "Pirólise ou gaseificação gerando biochar com carbono estável"},
            {"id": "storage",       "label": "Via de armazenamento",       "desc": "Aplicação em solo, ambiente construído ou outro storage permanente"},
            {"id": "additionality", "label": "Adicionalidade financeira",  "desc": "Projeto não seria viável sem receita de créditos de carbono"},
            {"id": "baseline",      "label": "Linha de base definível",    "desc": "Contrafactual quantificável para o destino do feedstock sem o projeto"},
            {"id": "permanence",    "label": "Permanência > 200 anos",     "desc": "H/Corg < 0.5, O/Corg < 0.2 (verificável via análise elemental do biochar)"},
        ],
    },
    "puro": {
        "name": "Puro.Earth Biochar",
        "criteria": [
            {"id": "feedstock",     "label": "Feedstock certificável",     "desc": "Biomassa residual com cadeia de custódia documentável"},
            {"id": "process",       "label": "Processo de pirólise",       "desc": "Temperatura e tempo de residência monitorados e registrados"},
            {"id": "permanence",    "label": "Permanência ≥ 100 anos",     "desc": "H/Corg < 0.7; resultado de análise elemental obrigatório"},
            {"id": "additionality", "label": "Adicionalidade",             "desc": "Ausência de incentivo regulatório que tornaria o projeto viável sem carbono"},
            {"id": "monitoring",    "label": "Plano de monitoramento",     "desc": "Procedimentos de amostragem e análise laboratorial ISO 17025 definidos"},
        ],
    },
}

@app.post("/api/projects/{project_id}/screening")
async def run_screening(project_id: str, methodology: str = "isometric"):
    p = _db_fetchone("SELECT * FROM ca_projects WHERE id=%s", (project_id,))
    if not p:
        raise HTTPException(404, "Projeto não encontrado")

    cfg = _METHODOLOGY_SCREENING.get(methodology)
    if not cfg:
        raise HTTPException(400, f"Sem critérios de triagem para '{methodology}'")

    # Context: prefer cached project_data
    cached_data = p.get("project_data")
    if isinstance(cached_data, str):
        try: cached_data = json.loads(cached_data)
        except: cached_data = None

    if cached_data:
        context = json.dumps(cached_data, ensure_ascii=False, indent=2)[:7000]
    else:
        # Quick RAG via Responses API
        vs_id = p.get("project_vector_store_id", "")
        methodology_vs_id = METHODOLOGY_REGISTRY.get(methodology, {}).get("vector_store_id", "")
        vs_ids = [v for v in [vs_id, methodology_vs_id] if v]
        try:
            tools = [{"type": "file_search", "vector_store_ids": vs_ids}] if vs_ids else []
            rag = openai_client.responses.create(
                model=OPENAI_MODEL,
                input="Descreva o projeto: tipo de feedstock, processo de conversão, via de armazenamento, localização, escala e receita esperada com carbono.",
                tools=tools,
            )
            context = rag.output_text or "Informações insuficientes nos documentos."
        except Exception as e:
            context = f"Não foi possível extrair contexto do projeto ({e}). Faça uma auditoria completa primeiro."

    criteria_text = "\n".join(
        f'- {c["id"]} | {c["label"]}: {c["desc"]}' for c in cfg["criteria"]
    )
    n = len(cfg["criteria"])
    threshold_eligible = max(1, n - 1)
    threshold_possible = max(1, n // 2)

    prompt = f"""Analise se este projeto de carbono atende os critérios de elegibilidade do padrão {cfg['name']}.

DADOS DO PROJETO:
{context}

CRITÉRIOS A AVALIAR ({n} no total):
{criteria_text}

VEREDICTO:
- "elegível": {threshold_eligible} ou mais critérios = pass
- "possível": {threshold_possible}–{threshold_eligible-1} critérios = pass (restantes partial/fail)
- "inelegível": menos de {threshold_possible} critérios = pass

Retorne APENAS JSON válido (sem markdown):
{{
  "verdict": "elegível" | "possível" | "inelegível",
  "confidence": <0-100>,
  "summary": "<2-3 frases objetivas sobre o fit do projeto com o padrão>",
  "checks": [
    {{"criterion_id": "<id>", "label": "<label>", "result": "pass" | "partial" | "fail", "note": "<observação específica baseada nos dados>"}}
  ],
  "key_actions": ["<próxima ação concreta 1>", "<próxima ação concreta 2>", "<próxima ação concreta 3>"]
}}"""

    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Especialista em certificação de projetos de carbono. Responda apenas com JSON válido, sem markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content
    try:
        result = json.loads(raw)
    except Exception:
        result = {"verdict": "possível", "confidence": 0, "summary": raw, "checks": [], "key_actions": []}

    result["methodology"] = methodology
    result["methodology_name"] = cfg["name"]
    result["criteria_count"] = n
    result["used_cache"] = cached_data is not None
    return result

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
