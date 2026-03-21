import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI


DEFAULT_LOW_CONFIDENCE_THRESHOLD = 45
DEFAULT_REANALYZE_STATUSES = {
    "Não conforme",
    "Não evidenciado",
    "Inconsistência documental",
    "Erro de análise",
}


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clip_int(value: Any, default: int = 0, min_value: int = 0, max_value: int = 100) -> int:
    try:
        out = int(round(float(value)))
    except Exception:
        out = default
    return max(min_value, min(max_value, out))


def normalize_status(status: str) -> str:
    raw = safe_str(status).lower()

    mapping = {
        "conforme": "Conforme",
        "compliant": "Conforme",
        "parcial": "Parcialmente conforme",
        "partial": "Parcialmente conforme",
        "partially compliant": "Parcialmente conforme",
        "parcialmente conforme": "Parcialmente conforme",
        "não conforme": "Não conforme",
        "nao conforme": "Não conforme",
        "non-compliant": "Não conforme",
        "not compliant": "Não conforme",
        "não evidenciado": "Não evidenciado",
        "nao evidenciado": "Não evidenciado",
        "not evidenced": "Não evidenciado",
        "insufficient evidence": "Não evidenciado",
        "inconsistência documental": "Inconsistência documental",
        "inconsistencia documental": "Inconsistência documental",
        "document inconsistency": "Inconsistência documental",
        "erro de análise": "Erro de análise",
        "erro de analise": "Erro de análise",
        "analysis error": "Erro de análise",
    }
    return mapping.get(raw, "Erro de análise")


def normalize_risk(risk: str) -> str:
    raw = safe_str(risk).lower()
    if raw == "médio":
        return "medio"
    if raw in {"baixo", "medio", "alto"}:
        return raw
    return "alto"


def classify_status(score: int, evidence_present: bool, methodology_present: bool) -> str:
    if not evidence_present:
        return "Não evidenciado"
    if not methodology_present and score < 80:
        return "Parcialmente conforme"
    if score >= 80:
        return "Conforme"
    if score >= 50:
        return "Parcialmente conforme"
    if score > 0:
        return "Não conforme"
    return "Não evidenciado"


def classify_risk(score: int, confidence: int, status: str) -> str:
    if status in {"Não conforme", "Não evidenciado", "Erro de análise", "Inconsistência documental"}:
        return "alto"
    if confidence < 50 or score < 80:
        return "medio"
    return "baixo"


def default_result(requirement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "requirement_id": safe_str(requirement.get("id", "")),
        "module": safe_str(requirement.get("module", "")),
        "title": safe_str(requirement.get("title", "")),
        "status": "Não evidenciado",
        "risk": "alto",
        "score": 0,
        "confidence": 0,
        "project_evidence": "",
        "methodology_basis": "",
        "gap": "",
        "recommendation": "",
        "notes": "",
    }


class AuditEngine:
    def __init__(
        self,
        api_key: str,
        model: str,
        project_vector_store_id: str,
        methodology_vector_store_id: str,
        project_name: str,
        requirements: Optional[List[Dict[str, Any]]] = None,
        module_project_queries: int = 2,
        module_methodology_queries: int = 2,
        project_max_results_per_query: int = 3,
        methodology_max_results_per_query: int = 3,
        max_project_hits_in_prompt: int = 4,
        max_methodology_hits_in_prompt: int = 4,
        max_text_chars_per_hit: int = 900,
        progress_callback=None,
        max_retries: int = 2,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.project_vector_store_id = project_vector_store_id
        self.methodology_vector_store_id = methodology_vector_store_id
        self.project_name = project_name
        self.requirements = requirements or []

        self.module_project_queries = module_project_queries
        self.module_methodology_queries = module_methodology_queries
        self.project_max_results_per_query = project_max_results_per_query
        self.methodology_max_results_per_query = methodology_max_results_per_query
        self.max_project_hits_in_prompt = max_project_hits_in_prompt
        self.max_methodology_hits_in_prompt = max_methodology_hits_in_prompt
        self.max_text_chars_per_hit = max_text_chars_per_hit
        self.progress_callback = progress_callback
        self.max_retries = max_retries

        self.session_cost_estimate = 0.0
        self.last_execution_cost_estimate = 0.0
        self.last_run_stats: Dict[str, Any] = {}
        self.low_confidence_threshold = DEFAULT_LOW_CONFIDENCE_THRESHOLD

    # =========================================================
    # PUBLIC API
    # =========================================================

    def run_full_audit(
        self,
        selected_modules: Optional[List[str]] = None,
        enable_auto_reanalysis: bool = True,
    ) -> Dict[str, Any]:
        if not self.requirements:
            raise ValueError("Nenhum requisito estruturado foi carregado para a metodologia selecionada.")

        filtered_requirements = [
            req for req in self.requirements
            if not selected_modules or req.get("module") in selected_modules
        ]

        grouped = self._group_requirements_by_module(filtered_requirements)
        modules = list(grouped.keys())

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results: List[Dict[str, Any]] = []
        trails: List[Dict[str, Any]] = []

        total_modules = len(modules)
        self.last_execution_cost_estimate = 0.0

        for idx, module_name in enumerate(modules, start=1):
            self._emit_progress(
                stage="module_start",
                module=module_name,
                current=idx,
                total=total_modules,
                percent=self._compute_percent(idx - 1, total_modules),
                message=f"Iniciando módulo {module_name}",
            )

            module_results, module_trail = self._audit_single_module(
                module_name=module_name,
                requirements=grouped[module_name],
                analysis_label="initial",
                current=idx,
                total=total_modules,
                query_boost=False,
            )

            results.extend(module_results)
            trails.append(module_trail)

            if enable_auto_reanalysis and self._module_needs_reanalysis(module_results):
                self._emit_progress(
                    stage="module_reanalysis",
                    module=module_name,
                    current=idx,
                    total=total_modules,
                    percent=self._compute_percent(idx - 0.5, total_modules),
                    message=f"Reanalisando módulo {module_name} por baixa robustez",
                )

                refined_results, refined_trail = self._audit_single_module(
                    module_name=module_name,
                    requirements=grouped[module_name],
                    analysis_label="reanalysis",
                    current=idx,
                    total=total_modules,
                    query_boost=True,
                )

                merged_results = self._merge_module_results(module_results, refined_results)
                results = [r for r in results if r.get("module") != module_name] + merged_results
                trails.append(refined_trail)

            self._emit_progress(
                stage="module_complete",
                module=module_name,
                current=idx,
                total=total_modules,
                percent=self._compute_percent(idx, total_modules),
                message=f"Módulo {module_name} concluído",
            )

        results = sorted(
            results,
            key=lambda x: (safe_str(x.get("module", "")), safe_str(x.get("requirement_id", "")))
        )

        self.last_execution_cost_estimate = round(self.last_execution_cost_estimate, 4)
        self.session_cost_estimate = round(self.session_cost_estimate, 4)

        self.last_run_stats = {
            "run_id": run_id,
            "modules": modules,
            "module_count": len(modules),
            "requirement_count": len(filtered_requirements),
            "estimated_cost": self.last_execution_cost_estimate,
        }

        self._emit_progress(
            stage="run_complete",
            module="",
            current=total_modules,
            total=total_modules,
            percent=100,
            message="Auditoria concluída",
        )

        return {
            "run_id": run_id,
            "results": results,
            "trails": trails,
            "estimated_cost": self.last_execution_cost_estimate,
            "session_estimated_cost": self.session_cost_estimate,
            "stats": self.last_run_stats,
        }

    def rerun_failed_items(
        self,
        previous_results: List[Dict[str, Any]],
        selected_modules: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        previous_by_id = {
            safe_str(item.get("requirement_id", "")): item
            for item in previous_results
        }

        requirements_to_retry = []
        for req in self.requirements:
            if selected_modules and req.get("module") not in selected_modules:
                continue

            rid = safe_str(req.get("id", ""))
            prev = previous_by_id.get(rid)
            if not prev:
                continue

            status = safe_str(prev.get("status", ""))
            confidence = clip_int(prev.get("confidence", 0), default=0)

            if status in DEFAULT_REANALYZE_STATUSES or confidence < self.low_confidence_threshold:
                requirements_to_retry.append(req)

        grouped = self._group_requirements_by_module(requirements_to_retry)
        modules = list(grouped.keys())

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results: List[Dict[str, Any]] = []
        trails: List[Dict[str, Any]] = []

        total_modules = len(modules)
        self.last_execution_cost_estimate = 0.0

        for idx, module_name in enumerate(modules, start=1):
            module_results, module_trail = self._audit_single_module(
                module_name=module_name,
                requirements=grouped[module_name],
                analysis_label="rerun_failed",
                current=idx,
                total=total_modules,
                query_boost=True,
            )
            results.extend(module_results)
            trails.append(module_trail)

        results = sorted(
            results,
            key=lambda x: (safe_str(x.get("module", "")), safe_str(x.get("requirement_id", "")))
        )

        self.last_execution_cost_estimate = round(self.last_execution_cost_estimate, 4)
        self.session_cost_estimate = round(self.session_cost_estimate, 4)

        return {
            "run_id": run_id,
            "results": results,
            "trails": trails,
            "estimated_cost": self.last_execution_cost_estimate,
            "session_estimated_cost": self.session_cost_estimate,
        }

    def summarize_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        if total == 0:
            return {
                "total_requirements": 0,
                "overall_score": 0.0,
                "overall_confidence": 0.0,
                "status_counts": {},
                "risk_counts": {},
                "module_scores": {},
                "module_confidence": {},
            }

        status_counts: Dict[str, int] = {}
        risk_counts: Dict[str, int] = {}
        module_scores_raw: Dict[str, List[int]] = {}
        module_confidence_raw: Dict[str, List[int]] = {}

        for item in results:
            status = safe_str(item.get("status", "Erro de análise"))
            risk = safe_str(item.get("risk", "alto"))
            module = safe_str(item.get("module", "Sem módulo"))
            score = clip_int(item.get("score", 0), default=0)
            confidence = clip_int(item.get("confidence", 0), default=0)

            status_counts[status] = status_counts.get(status, 0) + 1
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            module_scores_raw.setdefault(module, []).append(score)
            module_confidence_raw.setdefault(module, []).append(confidence)

        module_scores = {
            module: round(sum(scores) / len(scores), 1) if scores else 0.0
            for module, scores in module_scores_raw.items()
        }
        module_confidence = {
            module: round(sum(scores) / len(scores), 1) if scores else 0.0
            for module, scores in module_confidence_raw.items()
        }

        overall_score = round(
            sum(clip_int(r.get("score", 0), default=0) for r in results) / total, 1
        )
        overall_confidence = round(
            sum(clip_int(r.get("confidence", 0), default=0) for r in results) / total, 1
        )

        return {
            "total_requirements": total,
            "overall_score": overall_score,
            "overall_confidence": overall_confidence,
            "status_counts": status_counts,
            "risk_counts": risk_counts,
            "module_scores": module_scores,
            "module_confidence": module_confidence,
        }

    def estimate_run_cost(
        self,
        selected_modules: Optional[List[str]] = None,
        execution_mode: str = "Rápido",
    ) -> Dict[str, Any]:
        if not self.requirements:
            return {
                "module_count": 0,
                "requirement_count": 0,
                "estimated_min_cost": 0.0,
                "estimated_max_cost": 0.0,
                "estimated_cost": 0.0,
            }

        requirements = [
            r for r in self.requirements
            if not selected_modules or r.get("module") in selected_modules
        ]
        grouped = self._group_requirements_by_module(requirements)
        module_count = len(grouped)
        requirement_count = len(requirements)

        if execution_mode.lower().startswith("ráp") or execution_mode.lower().startswith("rap"):
            base_per_module = 0.035
            min_factor = 0.8
            max_factor = 1.15
        else:
            base_per_module = 0.085
            min_factor = 0.9
            max_factor = 1.35

        min_cost = round(module_count * base_per_module * min_factor, 4)
        max_cost = round(module_count * base_per_module * max_factor, 4)
        est_cost = round((min_cost + max_cost) / 2, 4)

        return {
            "module_count": module_count,
            "requirement_count": requirement_count,
            "estimated_min_cost": min_cost,
            "estimated_max_cost": max_cost,
            "estimated_cost": est_cost,
        }

    # =========================================================
    # MODULE AUDIT
    # =========================================================

    def _audit_single_module(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        analysis_label: str,
        current: int,
        total: int,
        query_boost: bool = False,
    ):
        module_queries_project = self._build_module_project_queries(
            module_name, requirements, query_boost=query_boost
        )
        module_queries_methodology = self._build_module_methodology_queries(
            module_name, requirements, query_boost=query_boost
        )

        self._register_cost_estimate(analysis_label)

        self._emit_progress(
            stage="project_search",
            module=module_name,
            current=current,
            total=total,
            percent=self._compute_percent(current - 0.66, total),
            message=f"{module_name}: buscando evidências do projeto",
        )

        project_hits = self._run_multi_query_file_search(
            vector_store_id=self.project_vector_store_id,
            queries=module_queries_project[: self.module_project_queries],
            max_num_results=self.project_max_results_per_query,
            source_label="project",
        )

        self._emit_progress(
            stage="methodology_search",
            module=module_name,
            current=current,
            total=total,
            percent=self._compute_percent(current - 0.33, total),
            message=f"{module_name}: buscando base metodológica",
        )

        methodology_hits = self._run_multi_query_file_search(
            vector_store_id=self.methodology_vector_store_id,
            queries=module_queries_methodology[: self.module_methodology_queries],
            max_num_results=self.methodology_max_results_per_query,
            source_label="methodology",
        )

        project_context = self._format_hits_for_prompt(
            hits=project_hits[: self.max_project_hits_in_prompt],
            block_name="PROJETO",
        )
        methodology_context = self._format_hits_for_prompt(
            hits=methodology_hits[: self.max_methodology_hits_in_prompt],
            block_name="METODOLOGIA",
        )

        prompt = self._build_audit_prompt(
            module_name=module_name,
            requirements=requirements,
            project_context=project_context,
            methodology_context=methodology_context,
        )

        self._emit_progress(
            stage="llm_analysis",
            module=module_name,
            current=current,
            total=total,
            percent=self._compute_percent(current - 0.1, total),
            message=f"{module_name}: avaliando conformidade",
        )

        raw_text = self._call_llm_json(prompt)
        parsed = self._parse_llm_output(raw_text)
        normalized_results = self._normalize_module_results(
            requirements=requirements,
            parsed_items=parsed,
            module_name=module_name,
            project_hits=project_hits,
            methodology_hits=methodology_hits,
        )

        trail = {
            "module": module_name,
            "analysis_label": analysis_label,
            "project_query": " | ".join(module_queries_project),
            "methodology_query": " | ".join(module_queries_methodology),
            "project_hits_count": len(project_hits),
            "methodology_hits_count": len(methodology_hits),
        }

        return normalized_results, trail

    def _normalize_module_results(
        self,
        requirements: List[Dict[str, Any]],
        parsed_items: Any,
        module_name: str,
        project_hits: List[Dict[str, Any]],
        methodology_hits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        parsed_by_id: Dict[str, Dict[str, Any]] = {}

        if isinstance(parsed_items, list):
            for item in parsed_items:
                if not isinstance(item, dict):
                    continue
                rid = safe_str(item.get("requirement_id", ""))
                if rid:
                    parsed_by_id[rid] = item

        normalized_results: List[Dict[str, Any]] = []

        for requirement in requirements:
            rid = safe_str(requirement.get("id", ""))
            raw = parsed_by_id.get(rid, {}) if parsed_by_id else {}

            normalized = default_result(requirement)

            normalized["project_evidence"] = safe_str(raw.get("project_evidence", ""))
            normalized["methodology_basis"] = safe_str(raw.get("methodology_basis", ""))
            normalized["gap"] = safe_str(raw.get("gap", ""))
            normalized["recommendation"] = safe_str(raw.get("recommendation", ""))
            normalized["notes"] = safe_str(raw.get("notes", ""))
            normalized["confidence"] = clip_int(raw.get("confidence", 0), default=0)

            if not normalized["project_evidence"]:
                normalized["project_evidence"] = self._fallback_project_evidence(project_hits)

            if not normalized["methodology_basis"]:
                normalized["methodology_basis"] = self._fallback_methodology_basis(methodology_hits)

            evidence_present = bool(safe_str(normalized["project_evidence"]))
            methodology_present = bool(safe_str(normalized["methodology_basis"]))

            normalized["score"] = self._derive_score(
                project_evidence=normalized["project_evidence"],
                methodology_basis=normalized["methodology_basis"],
                gap=normalized["gap"],
                recommendation=normalized["recommendation"],
                notes=normalized["notes"],
            )
            normalized["status"] = classify_status(
                score=normalized["score"],
                evidence_present=evidence_present,
                methodology_present=methodology_present,
            )
            normalized["risk"] = classify_risk(
                score=normalized["score"],
                confidence=normalized["confidence"],
                status=normalized["status"],
            )

            if not normalized["gap"]:
                normalized["gap"] = self._infer_gap(normalized["status"])

            if not normalized["recommendation"]:
                normalized["recommendation"] = self._infer_recommendation(normalized["status"])

            normalized_results.append(normalized)

        return normalized_results

    def _derive_score(
        self,
        project_evidence: str,
        methodology_basis: str,
        gap: str,
        recommendation: str,
        notes: str,
    ) -> int:
        score = 0

        if safe_str(project_evidence):
            score += 45
        if safe_str(methodology_basis):
            score += 25

        gap_text = safe_str(gap).lower()
        rec_text = safe_str(recommendation).lower()
        notes_text = safe_str(notes).lower()
        combined = " ".join([gap_text, rec_text, notes_text])

        negative_markers = [
            "não foi possível",
            "nao foi possivel",
            "ausência",
            "ausencia",
            "insuficiente",
            "falt",
            "missing",
            "not identified",
            "not found",
            "incomplete",
            "inconsist",
            "conflict",
        ]
        positive_markers = [
            "robusto",
            "consistente",
            "adequado",
            "claro",
            "suficiente",
            "evidenciado",
            "documentado",
        ]

        neg_hits = sum(1 for marker in negative_markers if marker in combined)
        pos_hits = sum(1 for marker in positive_markers if marker in combined)

        score += pos_hits * 8
        score -= neg_hits * 10

        return clip_int(score, default=0)

    # =========================================================
    # SUPPORT
    # =========================================================

    def _group_requirements_by_module(self, requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for req in requirements:
            grouped.setdefault(safe_str(req.get("module", "Sem módulo")), []).append(req)
        return grouped

    def _module_needs_reanalysis(self, module_results: List[Dict[str, Any]]) -> bool:
        for item in module_results:
            status = safe_str(item.get("status", ""))
            confidence = clip_int(item.get("confidence", 0), default=0)
            if status in DEFAULT_REANALYZE_STATUSES or confidence < self.low_confidence_threshold:
                return True
        return False

    def _merge_module_results(
        self,
        original_results: List[Dict[str, Any]],
        refined_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        original_by_id = {
            safe_str(item.get("requirement_id", "")): item for item in original_results
        }
        for item in refined_results:
            original_by_id[safe_str(item.get("requirement_id", ""))] = item
        return list(original_by_id.values())

    def _build_module_project_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        base_terms = [safe_str(r.get("title", "")) for r in requirements[:3]]
        keywords = []
        for req in requirements:
            keywords.extend(req.get("keywords", [])[:3])

        parts = [module_name] + base_terms + keywords[:6]
        query = " | ".join([p for p in parts if p])

        if query_boost:
            query += " | evidência documental | prova | registro | rastreabilidade"

        return [query, module_name]

    def _build_module_methodology_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        parts = [module_name]
        for req in requirements[:4]:
            parts.append(safe_str(req.get("description", ""))[:180])

        query = " | ".join([p for p in parts if p])
        if query_boost:
            query += " | requirement | criteria | methodology | eligibility"

        return [query, module_name]

    def _run_multi_query_file_search(
        self,
        vector_store_id: str,
        queries: List[str],
        max_num_results: int,
        source_label: str,
    ) -> List[Dict[str, Any]]:
        if not vector_store_id:
            return []

        collected: List[Dict[str, Any]] = []

        for query in queries:
            try:
                response = self.client.vector_stores.search(
                    vector_store_id=vector_store_id,
                    query=query,
                    max_num_results=max_num_results,
                )
                data = getattr(response, "data", []) or []

                for item in data:
                    text = safe_str(getattr(item, "content", ""))
                    filename = safe_str(getattr(item, "filename", "")) or f"{source_label}_document"
                    score = getattr(item, "score", None)
                    file_id = safe_str(getattr(item, "file_id", ""))
                    attributes = getattr(item, "attributes", {}) or {}
                    page = attributes.get("page") or attributes.get("section") or ""

                    collected.append({
                        "source_group": source_label,
                        "query": query,
                        "filename": filename,
                        "text": self._truncate_text(text, self.max_text_chars_per_hit),
                        "score": score,
                        "file_id": file_id,
                        "attributes": attributes,
                        "page": page,
                    })
            except Exception:
                continue

        unique = []
        seen = set()
        for hit in collected:
            key = (
                safe_str(hit.get("filename", "")),
                safe_str(hit.get("page", "")),
                safe_str(hit.get("text", ""))[:200],
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(hit)

        return unique

    def _format_hits_for_prompt(self, hits: List[Dict[str, Any]], block_name: str) -> str:
        if not hits:
            return f"[{block_name}]\nNenhum trecho recuperado."
        lines = [f"[{block_name}]"]
        for i, hit in enumerate(hits, start=1):
            filename = safe_str(hit.get("filename", "Documento sem nome"))
            page = safe_str(hit.get("page", "")) or "não identificada"
            text = self._truncate_text(safe_str(hit.get("text", "")), self.max_text_chars_per_hit)
            lines.append(f"{i}. {filename} | pág./seção: {page}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)

    def _build_audit_prompt(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        project_context: str,
        methodology_context: str,
    ) -> str:
        req_lines = []
        for req in requirements:
            req_lines.append(
                json.dumps(
                    {
                        "requirement_id": safe_str(req.get("id", "")),
                        "module": safe_str(req.get("module", "")),
                        "title": safe_str(req.get("title", "")),
                        "description": safe_str(req.get("description", "")),
                        "rationale": safe_str(req.get("rationale", "")),
                        "keywords": req.get("keywords", []),
                    },
                    ensure_ascii=False,
                )
            )

        req_block = "\n".join(req_lines)

        return f"""
Você está avaliando requisitos metodológicos de auditoria documental.

IMPORTANTE:
- Retorne APENAS JSON válido.
- Não escreva explicações fora do JSON.
- Não invente fatos ausentes.
- Use somente os trechos fornecidos.
- Não defina status, score ou risk.
- Para cada requisito, preencha:
  requirement_id, project_evidence, methodology_basis, gap, recommendation, confidence, notes

Formato obrigatório:
[
  {{
    "requirement_id": "ID",
    "project_evidence": "trecho ou síntese objetiva da evidência do projeto",
    "methodology_basis": "trecho ou síntese objetiva da base metodológica",
    "gap": "lacuna principal",
    "recommendation": "ação recomendada",
    "confidence": 0,
    "notes": "observações adicionais"
  }}
]

Módulo:
{module_name}

Requisitos:
{req_block}

{project_context}

{methodology_context}
""".strip()

    def _call_llm_json(self, prompt: str) -> str:
        last_error = None
        for _ in range(self.max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                )
                text = getattr(response, "output_text", "") or ""
                if text.strip():
                    return text
            except Exception as e:
                last_error = e
                continue
        raise RuntimeError(f"Falha ao chamar o modelo: {last_error}")

    def _parse_llm_output(self, raw_text: str) -> Any:
        text = safe_str(raw_text)

        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            return []

    def _fallback_project_evidence(self, project_hits: List[Dict[str, Any]]) -> str:
        usable = [h for h in project_hits if safe_str(h.get("text")).strip()]
        if not usable:
            return "Não foi possível identificar evidência documental suficiente do projeto nos trechos recuperados."
        return self._join_top_hits(usable, top_n=2)

    def _fallback_methodology_basis(self, methodology_hits: List[Dict[str, Any]]) -> str:
        usable = [h for h in methodology_hits if safe_str(h.get("text")).strip()]
        if not usable:
            return "Não foi possível identificar base metodológica suficiente nos trechos recuperados."
        return self._join_top_hits(usable, top_n=2)

    def _join_top_hits(self, hits: List[Dict[str, Any]], top_n: int = 2) -> str:
        parts = []
        for hit in hits[:top_n]:
            filename = safe_str(hit.get("filename", "Documento sem nome"))
            page = safe_str(hit.get("page", "")) or "não identificada"
            text = self._truncate_text(safe_str(hit.get("text", "")), max_chars=900)
            parts.append(f"{filename} (pág./seção: {page}): {text}")
        return "\n\n".join(parts)

    def _infer_gap(self, status: str) -> str:
        if status == "Conforme":
            return "Não foi identificada lacuna material relevante com base nos trechos analisados."
        if status == "Parcialmente conforme":
            return "Há evidência parcial, porém ainda faltam elementos documentais e/ou operacionais para robustez metodológica."
        if status == "Não conforme":
            return "A evidência disponível do projeto não atende adequadamente ao critério metodológico recuperado."
        if status == "Não evidenciado":
            return "Não foi possível localizar evidência documental suficiente do projeto para suportar o requisito."
        if status == "Inconsistência documental":
            return "Os trechos recuperados apresentam conflito ou ambiguidade relevante."
        return "Não foi possível estabelecer lacuna com segurança."

    def _infer_recommendation(self, status: str) -> str:
        if status == "Conforme":
            return "Manter os registros e evidências organizados para futura verificação."
        if status == "Parcialmente conforme":
            return "Complementar a documentação e fortalecer a rastreabilidade/evidência do requisito."
        if status == "Não conforme":
            return "Revisar a aderência metodológica e incluir evidências objetivas que atendam ao requisito."
        if status == "Não evidenciado":
            return "Inserir documentação específica e evidência verificável para o requisito."
        if status == "Inconsistência documental":
            return "Reconciliar as inconsistências entre documentos e consolidar uma versão controlada."
        return "Revisar manualmente o item."

    def _truncate_text(self, text: str, max_chars: int) -> str:
        text = safe_str(text)
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def _register_cost_estimate(self, analysis_label: str) -> None:
        if analysis_label == "initial":
            increment = 0.035
        elif analysis_label in {"reanalysis", "rerun_failed"}:
            increment = 0.02
        else:
            increment = 0.015

        self.last_execution_cost_estimate += increment
        self.session_cost_estimate += increment

    def _compute_percent(self, current: float, total: int) -> int:
        if total <= 0:
            return 0
        percent = int(round((current / total) * 100))
        return max(0, min(100, percent))

    def _emit_progress(
        self,
        stage: str,
        module: str,
        current: int,
        total: int,
        percent: int,
        message: str,
    ) -> None:
        if not self.progress_callback:
            return

        payload = {
            "stage": stage,
            "module": module,
            "current": current,
            "total": total,
            "percent": percent,
            "message": message,
            "execution_estimated_cost": round(self.last_execution_cost_estimate, 4),
            "session_estimated_cost": round(self.session_cost_estimate, 4),
        }
        try:
            self.progress_callback(payload)
        except Exception:
            pass
