import json
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from openai import OpenAI


SYSTEM_AUDITOR_PROMPT = """
Você é uma auditora técnica especializada em avaliação metodológica de projetos de remoção de carbono via biochar.

Sua tarefa é avaliar um CONJUNTO DE REQUISITOS DE UM MESMO MÓDULO, comparando:
1. trechos da documentação do projeto
2. trechos da metodologia

Regras obrigatórias:
- Use exclusivamente os trechos fornecidos.
- Não invente fatos.
- Não preencha lacunas com suposições.
- Se a evidência não estiver presente, diga explicitamente.
- Diferencie ausência documental, inconsistência documental e potencial não conformidade.
- Responda sempre em JSON válido.
- Avalie cada requisito individualmente.
- Seja econômico, técnico e auditável.

Formato obrigatório:
{
  "module": "string",
  "items": [
    {
      "requirement_id": "string",
      "status": "Conforme|Parcialmente conforme|Não conforme|Não evidenciado|Inconsistência documental|Erro de análise",
      "risk": "baixo|medio|alto",
      "score": 0,
      "confidence": 0,
      "project_evidence": "string",
      "methodology_basis": "string",
      "gap": "string",
      "recommendation": "string",
      "notes": "string"
    }
  ]
}

Regras adicionais:
- score deve ser inteiro entre 0 e 100
- confidence deve ser inteiro entre 0 e 100
- cada item deve corresponder a um requirement_id fornecido
- se a evidência estiver ausente, usar "Não evidenciado"
- se houver conflito material entre trechos, usar "Inconsistência documental"
- se houver falha técnica de interpretação, usar "Erro de análise"
"""

DEFAULT_MODULE_PROJECT_QUERIES = 4
DEFAULT_MODULE_METHODOLOGY_QUERIES = 4
DEFAULT_PROJECT_MAX_RESULTS_PER_QUERY = 5
DEFAULT_METHODOLOGY_MAX_RESULTS_PER_QUERY = 5
DEFAULT_MAX_RETRIES = 5
DEFAULT_MAX_PROJECT_HITS_IN_PROMPT = 8
DEFAULT_MAX_METHODOLOGY_HITS_IN_PROMPT = 8
DEFAULT_MAX_TEXT_CHARS_PER_HIT = 1800

DEFAULT_LOW_CONFIDENCE_THRESHOLD = 45
DEFAULT_REANALYZE_STATUSES = {
    "Não evidenciado",
    "Erro de análise",
    "Inconsistência documental",
}


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def clip_int(value: Any, min_value: int = 0, max_value: int = 100, default: int = 0) -> int:
    try:
        v = int(value)
        return max(min_value, min(max_value, v))
    except Exception:
        return default


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            return None

    return None


def normalize_status(status: str) -> str:
    raw = safe_str(status).strip().lower()

    mapping = {
        "conforme": "Conforme",
        "parcialmente conforme": "Parcialmente conforme",
        "não conforme": "Não conforme",
        "nao conforme": "Não conforme",
        "não evidenciado": "Não evidenciado",
        "nao evidenciado": "Não evidenciado",
        "inconsistência documental": "Inconsistência documental",
        "inconsistencia documental": "Inconsistência documental",
        "erro de análise": "Erro de análise",
        "erro de analise": "Erro de análise",
    }

    return mapping.get(raw, "Erro de análise")


def normalize_risk(risk: str) -> str:
    raw = safe_str(risk).strip().lower()
    if raw == "médio":
        return "medio"
    if raw in {"baixo", "medio", "alto"}:
        return raw
    return "alto"


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
        self.max_retries = max_retries

        self.max_project_hits_in_prompt = max_project_hits_in_prompt
        self.max_methodology_hits_in_prompt = max_methodology_hits_in_prompt
        self.max_text_chars_per_hit = max_text_chars_per_hit
        self.progress_callback = progress_callback
        self.session_cost_estimate = 0.0
        self.last_execution_cost_estimate = 0.0
        self.last_run_stats: Dict[str, Any] = {}

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

    filtered_requirements = []
    for req in self.requirements:
        if selected_modules and req.get("module") not in selected_modules:
            continue
        filtered_requirements.append(req)

        grouped = self._group_requirements_by_module(filtered_requirements)
        modules = list(grouped.keys())

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results: List[Dict[str, Any]] = []
        trails: List[Dict[str, Any]] = []

        initial_modules = len(modules)
        current_module_index = 0

        self.last_execution_cost_estimate = 0.0

        for module_name in modules:
            current_module_index += 1

            self._emit_progress(
                stage="module_start",
                module=module_name,
                current=current_module_index,
                total=initial_modules,
                percent=self._compute_percent(current_module_index - 1, initial_modules),
                message=f"Iniciando módulo {module_name}",
            )

            module_results, module_trail = self._audit_single_module(
                module_name=module_name,
                requirements=grouped[module_name],
                analysis_label="primary",
                current=current_module_index,
                total=initial_modules,
            )

            results.extend(module_results)
            trails.append(module_trail)

            if enable_auto_reanalysis and self._module_needs_reanalysis(module_results):
                self._emit_progress(
                    stage="module_reanalysis",
                    module=module_name,
                    current=current_module_index,
                    total=initial_modules,
                    percent=self._compute_percent(current_module_index - 0.5, initial_modules),
                    message=f"Reanalisando módulo {module_name} por baixa robustez",
                )

                refined_results, refined_trail = self._audit_single_module(
                    module_name=module_name,
                    requirements=grouped[module_name],
                    analysis_label="reanalysis",
                    current=current_module_index,
                    total=initial_modules,
                    query_boost=True,
                )

                merged_results = self._merge_module_results(module_results, refined_results)
                results = [r for r in results if r.get("module") != module_name] + merged_results
                trails.append(refined_trail)

            self._emit_progress(
                stage="module_complete",
                module=module_name,
                current=current_module_index,
                total=initial_modules,
                percent=self._compute_percent(current_module_index, initial_modules),
                message=f"Módulo {module_name} concluído",
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
            current=initial_modules,
            total=initial_modules,
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
        idx = 0

        self.last_execution_cost_estimate = 0.0

        for module_name in modules:
            idx += 1

            self._emit_progress(
                stage="rerun_start",
                module=module_name,
                current=idx,
                total=total_modules,
                percent=self._compute_percent(idx - 1, total_modules),
                message=f"Reanalisando falhas do módulo {module_name}",
            )

            module_results, module_trail = self._audit_single_module(
                module_name=module_name,
                requirements=grouped[module_name],
                analysis_label="rerun_failed_items",
                current=idx,
                total=total_modules,
                query_boost=True,
            )
            results.extend(module_results)
            trails.append(module_trail)

            self._emit_progress(
                stage="rerun_complete_module",
                module=module_name,
                current=idx,
                total=total_modules,
                percent=self._compute_percent(idx, total_modules),
                message=f"Falhas do módulo {module_name} reanalisadas",
            )

        self.last_execution_cost_estimate = round(self.last_execution_cost_estimate, 4)
        self.session_cost_estimate = round(self.session_cost_estimate, 4)

        self.last_run_stats = {
            "run_id": run_id,
            "modules": modules,
            "module_count": len(modules),
            "requirement_count": len(requirements_to_retry),
            "estimated_cost": self.last_execution_cost_estimate,
            "mode": "rerun_failed_items",
        }

        return {
            "run_id": run_id,
            "results": results,
            "trails": trails,
            "estimated_cost": self.last_execution_cost_estimate,
            "session_estimated_cost": self.session_cost_estimate,
            "stats": self.last_run_stats,
        }

    def summarize_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)

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
        ) if total else 0.0

        overall_confidence = round(
            sum(clip_int(r.get("confidence", 0), default=0) for r in results) / total, 1
        ) if total else 0.0

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

        if execution_mode.lower().startswith("ráp"):
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
        module_queries_project = self._build_module_project_queries(module_name, requirements, query_boost=query_boost)
        module_queries_methodology = self._build_module_methodology_queries(module_name, requirements, query_boost=query_boost)

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

        model_prompt = self._build_module_prompt(
            module_name=module_name,
            requirements=requirements,
            project_context=project_context,
            methodology_context=methodology_context,
            analysis_label=analysis_label,
        )

        self._emit_progress(
            stage="model_analysis",
            module=module_name,
            current=current,
            total=total,
            percent=self._compute_percent(current - 0.1, total),
            message=f"{module_name}: analisando módulo",
        )

        raw_model_response = ""
        parsed_json = None

        try:
            response = self._responses_create_with_retry(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_AUDITOR_PROMPT},
                    {"role": "user", "content": model_prompt},
                ],
                temperature=0,
            )
            raw_model_response = self._get_response_text(response)
            parsed_json = try_parse_json(raw_model_response)
        except Exception as e:
            raw_model_response = json.dumps(
                {
                    "module": module_name,
                    "items": [],
                    "error": str(e),
                },
                ensure_ascii=False,
                indent=2,
            )

        normalized_results = self._normalize_module_results(
            module_name=module_name,
            requirements=requirements,
            parsed_json=parsed_json,
            project_hits=project_hits,
            methodology_hits=methodology_hits,
            raw_model_response=raw_model_response,
        )

        trail = {
            "module": module_name,
            "analysis_label": analysis_label,
            "requirement_ids": [safe_str(r.get("id", "")) for r in requirements],
            "title": f"Módulo {module_name}",
            "project_queries": module_queries_project,
            "methodology_queries": module_queries_methodology,
            "project_query": "\n".join(module_queries_project),
            "methodology_query": "\n".join(module_queries_methodology),
            "project_hits": project_hits,
            "methodology_hits": methodology_hits,
            "project_context": project_context,
            "methodology_context": methodology_context,
            "model_prompt": model_prompt,
            "model_response_raw": raw_model_response,
            "parsed_result": {
                "module": module_name,
                "items": normalized_results,
            },
        }

        return normalized_results, trail

    # =========================================================
    # MODULE HEALTH / REANALYSIS
    # =========================================================

    def _module_needs_reanalysis(self, module_results: List[Dict[str, Any]]) -> bool:
        if not module_results:
            return True

        weak_count = 0
        for item in module_results:
            status = safe_str(item.get("status", ""))
            confidence = clip_int(item.get("confidence", 0), default=0)

            if status in DEFAULT_REANALYZE_STATUSES or confidence < self.low_confidence_threshold:
                weak_count += 1

        ratio = weak_count / max(len(module_results), 1)
        return ratio >= 0.4

    def _merge_module_results(
        self,
        original_results: List[Dict[str, Any]],
        refined_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        refined_by_id = {
            safe_str(r.get("requirement_id", "")): r
            for r in refined_results
        }

        merged = []
        for item in original_results:
            rid = safe_str(item.get("requirement_id", ""))
            refined = refined_by_id.get(rid)

            if not refined:
                merged.append(item)
                continue

            original_status = safe_str(item.get("status", ""))
            refined_status = safe_str(refined.get("status", ""))
            original_conf = clip_int(item.get("confidence", 0), default=0)
            refined_conf = clip_int(refined.get("confidence", 0), default=0)

            if (
                refined_status not in {"Erro de análise", "Não evidenciado"}
                and refined_conf >= original_conf
            ):
                merged.append(refined)
            elif refined_conf > original_conf + 10:
                merged.append(refined)
            else:
                merged.append(item)

        return merged

    # =========================================================
    # REQUIREMENTS GROUPING
    # =========================================================

    def _group_requirements_by_module(self, requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for req in requirements:
            module = safe_str(req.get("module", "Sem módulo"))
            grouped.setdefault(module, []).append(req)
        return grouped

    # =========================================================
    # QUERY BUILDING
    # =========================================================

    def _build_module_project_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        titles = " ".join(safe_str(r.get("title", "")) for r in requirements[:5])
        descriptions = " ".join(safe_str(r.get("description", "")) for r in requirements[:3])
        keywords = self._collect_keywords(requirements)
        req_ids = " ".join(safe_str(r.get("id", "")) for r in requirements)

        queries = [
            f"{self.project_name} {module_name}",
            f"{module_name} {titles}",
            f"{module_name} project evidence {keywords}",
            f"{module_name} {descriptions}",
            f"{self.project_name} {module_name} documentation",
        ]

        if query_boost:
            queries.extend([
                f"{module_name} {req_ids} monitoring records procedures evidence",
                f"{self.project_name} {module_name} batch traceability QAQC evidence {keywords}",
            ])

        return self._dedupe_preserve_order([q.strip() for q in queries if q.strip()])

    def _build_module_methodology_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        req_ids = " ".join(safe_str(r.get("id", "")) for r in requirements)
        titles = " ".join(safe_str(r.get("title", "")) for r in requirements[:5])
        keywords = self._collect_keywords(requirements)

        queries = [
            f"{module_name} methodology",
            f"{req_ids} {module_name}",
            f"{module_name} {titles}",
            f"{module_name} methodology requirements {keywords}",
            f"{module_name} methodological basis",
        ]

        if query_boost:
            queries.extend([
                f"{module_name} criteria eligibility monitoring quality permanence {keywords}",
                f"{req_ids} requirement criteria evidence methodological basis",
            ])

        return self._dedupe_preserve_order([q.strip() for q in queries if q.strip()])

    def _collect_keywords(self, requirements: List[Dict[str, Any]]) -> str:
        seen = set()
        output = []
        for req in requirements:
            for kw in req.get("keywords", []) or []:
                k = safe_str(kw).strip()
                if k and k.lower() not in seen:
                    seen.add(k.lower())
                    output.append(k)
        return " ".join(output[:20])

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        seen = set()
        output = []
        for item in items:
            key = item.lower().strip()
            if key not in seen:
                seen.add(key)
                output.append(item)
        return output

    # =========================================================
    # FILE SEARCH
    # =========================================================

    def _run_multi_query_file_search(
        self,
        vector_store_id: str,
        queries: List[str],
        max_num_results: int,
        source_label: str,
    ) -> List[Dict[str, Any]]:
        all_hits: List[Dict[str, Any]] = []

        for query in queries:
            try:
                response = self._responses_create_with_retry(
                    model=self.model,
                    input=[{"role": "user", "content": query}],
                    temperature=0,
                    include=["file_search_call.results"],
                    tools=[
                        {
                            "type": "file_search",
                            "vector_store_ids": [vector_store_id],
                            "max_num_results": max_num_results,
                        }
                    ],
                )
                hits = self._extract_file_search_results(response, source_label=source_label, query=query)
                all_hits.extend(hits)
            except Exception as e:
                all_hits.append(
                    {
                        "source_label": source_label,
                        "query": query,
                        "filename": "SEARCH_ERROR",
                        "file_id": "",
                        "score": 0,
                        "page": "",
                        "text": "",
                        "attributes": {},
                        "error": str(e),
                    }
                )

        return self._deduplicate_hits(all_hits)

    def _extract_file_search_results(self, response: Any, source_label: str, query: str) -> List[Dict[str, Any]]:
        extracted: List[Dict[str, Any]] = []

        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "file_search_call":
                continue

            for result in getattr(item, "results", []) or []:
                extracted.append(
                    {
                        "source_label": source_label,
                        "query": query,
                        "filename": safe_str(
                            getattr(result, "filename", None)
                            or getattr(result, "file_name", None)
                            or "Documento sem nome"
                        ),
                        "file_id": safe_str(getattr(result, "file_id", "")),
                        "score": getattr(result, "score", 0),
                        "page": self._extract_page_from_result(result),
                        "text": self._extract_result_text(result),
                        "attributes": getattr(result, "attributes", {}) or {},
                    }
                )
        return extracted

    def _extract_page_from_result(self, result: Any) -> str:
        attrs = getattr(result, "attributes", {}) or {}
        for key in [
            "page",
            "page_number",
            "page_index",
            "start_page",
            "end_page",
            "section",
            "heading",
            "pagina",
            "página",
            "seção",
            "secao",
        ]:
            if key in attrs and attrs[key] is not None:
                return safe_str(attrs[key])
        return ""

    def _extract_result_text(self, result: Any) -> str:
        content = getattr(result, "content", None)

        if isinstance(content, list):
            texts = []
            for item in content:
                item_type = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
                item_text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
                if item_type == "text" and item_text:
                    texts.append(safe_str(item_text))
            if texts:
                return "\n".join(texts).strip()

        direct_text = getattr(result, "text", None)
        if isinstance(direct_text, str) and direct_text.strip():
            return direct_text.strip()

        return ""

    def _deduplicate_hits(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []

        for hit in hits:
            key = (
                safe_str(hit.get("filename")),
                safe_str(hit.get("page")),
                safe_str(hit.get("text"))[:250],
                safe_str(hit.get("source_label")),
            )
            if key not in seen:
                seen.add(key)
                unique.append(hit)

        unique.sort(key=lambda x: float(x.get("score", 0) or 0), reverse=True)
        return unique

    # =========================================================
    # PROMPT
    # =========================================================

    def _truncate_text(self, text: str, max_chars: Optional[int] = None) -> str:
        max_chars = max_chars or self.max_text_chars_per_hit
        text = safe_str(text)
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rstrip() + " ...[trecho truncado]"

    def _format_hits_for_prompt(self, hits: List[Dict[str, Any]], block_name: str) -> str:
        if not hits:
            return f"[{block_name}] Nenhum trecho recuperado."

        lines = [f"[{block_name}]"]

        for i, hit in enumerate(hits, start=1):
            filename = safe_str(hit.get("filename", "Documento sem nome"))
            page = safe_str(hit.get("page", "")) or "não identificada"
            score = safe_str(hit.get("score", ""))
            query = safe_str(hit.get("query", ""))
            text = self._truncate_text(safe_str(hit.get("text", "")))
            error = safe_str(hit.get("error", ""))

            lines.append(f"Trecho {i}")
            lines.append(f"- Documento: {filename}")
            lines.append(f"- Página/Seção: {page}")
            lines.append(f"- Score: {score}")
            lines.append(f"- Query: {query}")

            if error:
                lines.append(f"- Erro de busca: {error}")
            else:
                lines.append("- Conteúdo:")
                lines.append(text if text else "Não identificado.")
            lines.append("")

        return "\n".join(lines)

    def _build_module_prompt(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        project_context: str,
        methodology_context: str,
        analysis_label: str,
    ) -> str:
        req_lines = []
        for req in requirements:
            req_lines.append(
                f"- ID: {safe_str(req.get('id', ''))}\n"
                f"  Título: {safe_str(req.get('title', ''))}\n"
                f"  Descrição: {safe_str(req.get('description', ''))}\n"
                f"  Racional: {safe_str(req.get('rationale', ''))}\n"
                f"  Palavras-chave: {', '.join([safe_str(k) for k in (req.get('keywords', []) or [])])}"
            )

        return f"""
Avalie o módulo abaixo.

MÓDULO
- Nome: {module_name}
- Tipo de análise: {analysis_label}

REQUISITOS DO MÓDULO
{chr(10).join(req_lines)}

INSTRUÇÕES
1. Leia a base metodológica e identifique o critério aplicável para cada requisito.
2. Leia os trechos do projeto e identifique a evidência disponível para cada requisito.
3. Compare ambos individualmente.
4. Gere um item JSON para cada requirement_id.
5. Não omita nenhum requirement_id fornecido.
6. Se a evidência for insuficiente, use "Não evidenciado".
7. Seja sintético, mas suficientemente informativo para auditoria.
8. Se a primeira leitura parecer fraca, dê preferência aos trechos mais objetivos, específicos e auditáveis.

CONTEXTO DO PROJETO
{project_context}

CONTEXTO DA METODOLOGIA
{methodology_context}
""".strip()

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalize_module_results(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        parsed_json: Optional[Dict[str, Any]],
        project_hits: List[Dict[str, Any]],
        methodology_hits: List[Dict[str, Any]],
        raw_model_response: str,
    ) -> List[Dict[str, Any]]:
        parsed_items = []
        if parsed_json and isinstance(parsed_json.get("items"), list):
            parsed_items = parsed_json["items"]

        parsed_by_id = {}
        for item in parsed_items:
            rid = safe_str(item.get("requirement_id", "")).strip()
            if rid:
                parsed_by_id[rid] = item

        normalized_results: List[Dict[str, Any]] = []

        for requirement in requirements:
            requirement_id = safe_str(requirement.get("id", "REQ"))
            title = safe_str(requirement.get("title", "Sem título"))

            parsed_item = parsed_by_id.get(requirement_id)

            if not parsed_item:
                parsed_item = {
                    "requirement_id": requirement_id,
                    "status": "Erro de análise",
                    "risk": "alto",
                    "score": 0,
                    "confidence": 0,
                    "project_evidence": "",
                    "methodology_basis": "",
                    "gap": "O modelo não retornou item estruturado para este requisito dentro da análise modular.",
                    "recommendation": "Reexecutar o módulo ou isolar este requisito para análise individual.",
                    "notes": raw_model_response[:2000],
                }

            normalized = {
                "requirement_id": requirement_id,
                "module": module_name,
                "title": title,
                "status": normalize_status(parsed_item.get("status", "Erro de análise")),
                "risk": normalize_risk(parsed_item.get("risk", "alto")),
                "score": clip_int(parsed_item.get("score", 0), default=0),
                "confidence": clip_int(parsed_item.get("confidence", 0), default=0),
                "project_evidence": safe_str(parsed_item.get("project_evidence", "")),
                "methodology_basis": safe_str(parsed_item.get("methodology_basis", "")),
                "gap": safe_str(parsed_item.get("gap", "")),
                "recommendation": safe_str(parsed_item.get("recommendation", "")),
                "notes": safe_str(parsed_item.get("notes", "")),
            }

            if not normalized["project_evidence"]:
                normalized["project_evidence"] = self._fallback_project_evidence(project_hits)

            if not normalized["methodology_basis"]:
                normalized["methodology_basis"] = self._fallback_methodology_basis(methodology_hits)

            if not normalized["gap"]:
                normalized["gap"] = self._infer_gap(normalized["status"])

            if not normalized["recommendation"]:
                normalized["recommendation"] = self._infer_recommendation(normalized["status"])

            normalized_results.append(normalized)

        return normalized_results

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
        return "A análise não pôde ser concluída de forma robusta."

    def _infer_recommendation(self, status: str) -> str:
        if status == "Conforme":
            return "Manter a evidência organizada e rastreável para futura validação e verificação."
        if status == "Parcialmente conforme":
            return "Complementar a documentação, reforçar rastreabilidade e detalhar procedimentos operacionais/MRV."
        if status == "Não conforme":
            return "Revisar o desenho documental e operacional do requisito, alinhando explicitamente o projeto ao critério metodológico."
        if status == "Não evidenciado":
            return "Produzir ou localizar documentação primária que evidencie o atendimento ao requisito."
        if status == "Inconsistência documental":
            return "Reconciliar as fontes conflitantes e consolidar uma versão documental única e auditável."
        return "Reexecutar a análise com retry, menor contexto e revisão de busca."

    # =========================================================
    # COST / PROGRESS
    # =========================================================

    def _register_cost_estimate(self, analysis_label: str):
        if analysis_label == "primary":
            cost = 0.055
        elif analysis_label == "reanalysis":
            cost = 0.035
        elif analysis_label == "rerun_failed_items":
            cost = 0.03
        else:
            cost = 0.04

        self.last_execution_cost_estimate += cost
        self.session_cost_estimate += cost

    def _compute_percent(self, current: float, total: int) -> int:
        if total <= 0:
            return 0
        pct = int(round((current / total) * 100))
        return max(0, min(100, pct))

    def _emit_progress(
        self,
        stage: str,
        module: str,
        current: int,
        total: int,
        percent: int,
        message: str,
    ):
        if self.progress_callback is None:
            return

        payload = {
            "stage": stage,
            "module": module,
            "current": current,
            "total": total,
            "percent": max(0, min(100, int(percent))),
            "message": message,
            "execution_estimated_cost": round(self.last_execution_cost_estimate, 4),
            "session_estimated_cost": round(self.session_cost_estimate, 4),
        }

        try:
            self.progress_callback(payload)
        except Exception:
            pass

    # =========================================================
    # OPENAI HELPERS
    # =========================================================

    def _responses_create_with_retry(self, **kwargs):
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return self.client.responses.create(**kwargs)
            except Exception as e:
                last_exception = e
                message = safe_str(e).lower()

                retryable = any(
                    token in message
                    for token in [
                        "rate_limit",
                        "429",
                        "temporarily unavailable",
                        "timeout",
                        "connection",
                        "server error",
                        "internal error",
                    ]
                )

                if not retryable or attempt == self.max_retries:
                    raise

                time.sleep(self._compute_backoff_seconds(attempt))

        raise last_exception

    def _compute_backoff_seconds(self, attempt: int) -> float:
        base = min(2 ** attempt, 20)
        jitter = random.uniform(0.3, 1.1)
        return base + jitter

    def _get_response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        parts = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for content_item in getattr(item, "content", []) or []:
                    if isinstance(content_item, dict):
                        text = content_item.get("text", "")
                    else:
                        text = getattr(content_item, "text", "")
                    if text:
                        parts.append(safe_str(text))
        return "\n\n".join(parts).strip()
