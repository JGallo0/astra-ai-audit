import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI

from compliance_rules import (
    calculate_score,
    calculate_confidence,
    classify_status,
    classify_risk,
)

from smart_search import normalize_sources, rank_sources, build_smart_context
from engine.document_mapper import extract_project_data_from_contexts
from engine.requirement_logic import run_engine
from scoring import calculate_compliance_score, classify_compliance_score


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


def classify_risk(score: int, confidence: int, status: str) -> str:
    if status in {"Não conforme", "Não evidenciado", "Erro de análise", "Inconsistência documental"}:
        return "alto"
    if confidence < 50 or score < 70:
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

def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        value = safe_str(item)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def compact_list(values: List[Any], limit: Optional[int] = None) -> List[str]:
    cleaned = [safe_str(v) for v in values if safe_str(v)]
    cleaned = unique_preserve_order(cleaned)
    if limit is not None:
        cleaned = cleaned[:limit]
    return cleaned
    
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
    # STRUCTURED ENGINE AUDIT (V2)
    # =========================================================

    def _call_llm_json_extraction(self, prompt: str) -> str:
        """
        Wrapper dedicado para extração estruturada.
        Reaproveita o mesmo cliente/modelo do engine atual.
        """
        return self._call_llm_json(prompt)

    def _build_structured_query_bundle(self) -> List[str]:
        return [
            "reactor design diagram",
            "maintenance plan",
            "sampling plan",
            "durability option",
            "chain of custody",
            "biochar chemical analysis",
            "required measurements",
            "emissions monitoring",
            "environmental legal requirements",
            "product standard compliance",
            "deployment method",
        ]

    def _build_structured_contexts(
        self,
        query_bundle: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        queries = query_bundle or self._build_structured_query_bundle()

        project_hits = self._run_multi_query_file_search(
            vector_store_id=self.project_vector_store_id,
            queries=queries,
            max_num_results=self.project_max_results_per_query,
            source_label="project",
        )

        methodology_hits = self._run_multi_query_file_search(
            vector_store_id=self.methodology_vector_store_id,
            queries=queries,
            max_num_results=self.methodology_max_results_per_query,
            source_label="methodology",
        )

        project_sources = normalize_sources(project_hits, "project")
        methodology_sources = normalize_sources(methodology_hits, "methodology")

        ranked_project = rank_sources(" ".join(queries), project_sources)
        ranked_methodology = rank_sources(" ".join(queries), methodology_sources)

        project_context = build_smart_context(
            query="Structured project evidence extraction",
            ranked_sources=ranked_project,
            max_items=self.max_project_hits_in_prompt,
        )

        methodology_context = build_smart_context(
            query="Methodology requirements extraction",
            ranked_sources=ranked_methodology,
            max_items=self.max_methodology_hits_in_prompt,
        )

        return {
            "queries": queries,
            "project_hits": project_hits,
            "methodology_hits": methodology_hits,
            "project_context": project_context,
            "methodology_context": methodology_context,
            "ranked_project_sources": ranked_project,
            "ranked_methodology_sources": ranked_methodology,
        }
    def run_structured_engine_audit(
        self,
        selected_modules: Optional[List[str]] = None,
        audit_mode: str = "development",
    ) -> Dict[str, Any]:
        """
        Nova rota de auditoria:
        vector stores -> contextos -> mapper -> schema -> engine determinística

        audit_mode:
        - development -> projeto em desenvolvimento / pré-operação
        - operational -> projeto em operação / certificação
        """
        if not self.requirements:
            raise ValueError("Nenhum requisito estruturado foi carregado para a metodologia selecionada.")

        filtered_requirements = [
            req for req in self.requirements
            if not selected_modules or req.get("module") in selected_modules
        ]

        contexts = self._build_structured_contexts()

        mapped = extract_project_data_from_contexts(
            ai_client=self._call_llm_json_extraction,
            project_context=contexts["project_context"],
            methodology_context=contexts["methodology_context"],
        )

        project_data = mapped["project_data"]
        results = run_engine(project_data, filtered_requirements)

        # =========================================================
        # AJUSTE INICIAL POR MODO DE AUDITORIA
        # =========================================================
        if audit_mode == "development":
            adjusted_results = []

            for r in results:
                item = dict(r)

                if item.get("status") == "non_compliant":
                    missing_fields = item.get("missing_fields", []) or []
                    failed_fields = item.get("failed_fields", []) or []

                    if missing_fields and not failed_fields:
                        missing_fields_text = " ".join(missing_fields).lower()

                        # Se for claramente evidência operacional ainda não esperada
                        if any(k in missing_fields_text for k in [
                            "lab",
                            "monitoring",
                            "measurement",
                            "data",
                            "testing",
                            "emissions",
                        ]):
                            item["status"] = "future_evidence_required"

                            original_notes = item.get("notes", []) or []
                            item["notes"] = list(original_notes) + [
                                "Projeto em desenvolvimento: evidência operacional e/ou documental futura ainda requerida."
                            ]
                        else:
                            # Pode ser problema de desenho/estrutura do projeto,
                            # então não reclassificamos como evidência futura.
                            item["status"] = "partial"

                            original_notes = item.get("notes", []) or []
                            item["notes"] = list(original_notes) + [
                                "Projeto em desenvolvimento: lacuna de desenho, definição ou estrutura documental ainda precisa ser fortalecida."
                            ]

                adjusted_results.append(item)

            results = adjusted_results
            
        score_data = calculate_compliance_score(results)
        score_label = classify_compliance_score(score_data["score"])

        self.last_run_stats = {
            "mode": "structured_engine_v2",
            "audit_mode": audit_mode,
            "queries": contexts["queries"],
            "project_hits_count": len(contexts["project_hits"]),
            "methodology_hits_count": len(contexts["methodology_hits"]),
            "score": score_data["score"],
            "applicable_requirements": score_data["applicable_requirements"],
        }

        return {
            "project_data": project_data,
            "results": results,
            "score_data": score_data,
            "score_label": score_label,
            "audit_mode": audit_mode,
            "selected_modules": selected_modules or [],
            "queries": contexts["queries"],
            "project_context": contexts["project_context"],
            "methodology_context": contexts["methodology_context"],
            "project_hits": contexts["project_hits"],
            "methodology_hits": contexts["methodology_hits"],
            "normalized_fields": mapped.get("normalized_fields", []),
            "raw_extraction": mapped.get("raw_extraction", {}),
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
            "requirement_ids": [safe_str(r.get("id", "")) for r in requirements],
            "expected_evidence_types": self._collect_requirement_keywords(
                requirements,
                key="expected_evidence_types",
                per_requirement_limit=3,
                total_limit=12,
            ),
            "evaluation_criteria": self._collect_requirement_keywords(
                requirements,
                key="evaluation_criteria",
                per_requirement_limit=2,
                total_limit=12,
            ),
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
            expected_evidence_types = compact_list(requirement.get("expected_evidence_types", []), limit=6)
            evaluation_criteria = compact_list(requirement.get("evaluation_criteria", []), limit=5)
            
            if not normalized["project_evidence"]:
                normalized["project_evidence"] = self._fallback_project_evidence(project_hits)

            if not normalized["methodology_basis"]:
                normalized["methodology_basis"] = self._fallback_methodology_basis(methodology_hits)

            if not normalized["notes"]:
                note_parts = []

                if expected_evidence_types:
                    note_parts.append(
                        "Tipos de evidência esperados: " + ", ".join(expected_evidence_types) + "."
                    )

                if evaluation_criteria:
                    note_parts.append(
                        "Critérios centrais considerados: " + "; ".join(evaluation_criteria[:3]) + "."
                    )

                normalized["notes"] = " ".join(note_parts).strip()

            evidence_present = self._has_real_evidence(normalized["project_evidence"])
            methodology_present = self._has_real_methodology_basis(normalized["methodology_basis"])

            raw_conf = raw.get("confidence")

            if (
                raw_conf is None
                or safe_str(raw_conf) == ""
                or clip_int(raw_conf, default=0) <= 1
            ):
                normalized["confidence"] = calculate_confidence(
                    project_evidence=normalized["project_evidence"],
                    methodology_basis=normalized["methodology_basis"],
                    gap=normalized["gap"],
                    recommendation=normalized["recommendation"],
                    notes=normalized["notes"],
                )
            else:
                normalized["confidence"] = clip_int(raw_conf, default=50)

            normalized["score"] = calculate_score(
                project_evidence=normalized["project_evidence"],
                methodology_basis=normalized["methodology_basis"],
                gap=normalized["gap"],
                recommendation=normalized["recommendation"],
                notes=normalized["notes"],
            )

            normalized["status"] = classify_status(
                score=normalized["score"],
                confidence=normalized["confidence"],
                evidence_present=evidence_present,
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
    def _has_real_evidence(self, text: str) -> bool:
        text = safe_str(text).lower()
        if not text:
            return False

        negative_markers = [
            "não foi possível identificar evidência",
            "nao foi possivel identificar evidencia",
            "nenhuma evidência",
            "nenhuma evidencia",
            "não identificado",
            "nao identificado",
            "not identified",
            "not found",
            "insufficient evidence",
            "sem evidência",
            "sem evidencia",
        ]
        return not any(marker in text for marker in negative_markers)

    def _has_real_methodology_basis(self, text: str) -> bool:
        text = safe_str(text).lower()
        if not text:
            return False

        negative_markers = [
            "não foi possível identificar base metodológica",
            "nao foi possivel identificar base metodologica",
            "nenhuma base metodológica",
            "nenhuma base metodologica",
            "não identificado",
            "nao identificado",
            "not identified",
            "not found",
            "insufficient evidence",
        ]
        return not any(marker in text for marker in negative_markers)

        # =========================================================
        # 1. EVIDÊNCIA DO PROJETO (0–40)
        # =========================================================
        if self._has_real_evidence(pe):
            score += 25

            if len(pe) >= 120:
                score += 5
            if len(pe) >= 220:
                score += 5
            if len(pe) >= 400:
                score += 5

        # =========================================================
        # 2. BASE METODOLÓGICA (0–30)
        # =========================================================
        if self._has_real_methodology_basis(mb):
            score += 20

            if len(mb) >= 100:
                score += 4
            if len(mb) >= 180:
                score += 3
            if len(mb) >= 300:
                score += 3

        # =========================================================
        # 3. GAP (-30 até +10)
        # =========================================================
        if gp:
            if "no material gap" in gp_lower or "não foi identificada lacuna" in gp_lower:
                score += 8
            else:
                score -= 10

                if any(x in gp_lower for x in ["missing", "ausência", "incomplete", "não especifica"]):
                    score -= 5

                if any(x in gp_lower for x in ["not compliant", "não atende", "insufficient"]):
                    score -= 10

        # =========================================================
        # 4. RECOMENDAÇÃO (+0–5)
        # =========================================================
        if rc:
            score += 2

        # =========================================================
        # 5. NOTAS (+0–5)
        # =========================================================
        if nt:
            score += 2

        # =========================================================
        # 6. NORMALIZAÇÃO FINAL
        # =========================================================
        return clip_int(score, default=0, min_value=0, max_value=100)        

    
    # =========================================================
    # ENGINE SUPPORT / SEARCH / FORMATTING
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

    def _collect_requirement_keywords(
        self,
        requirements: List[Dict[str, Any]],
        key: str,
        per_requirement_limit: Optional[int] = None,
        total_limit: Optional[int] = None,
    ) -> List[str]:
        collected: List[str] = []

        for req in requirements:
            values = req.get(key, []) or []
            if not isinstance(values, list):
                continue

            cleaned = compact_list(values, limit=per_requirement_limit)
            collected.extend(cleaned)

        collected = unique_preserve_order(collected)

        if total_limit is not None:
            collected = collected[:total_limit]

        return collected

    def _format_requirement_brief(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "requirement_id": safe_str(req.get("id", "")),
            "module": safe_str(req.get("module", "")),
            "title": safe_str(req.get("title", "")),
            "description": safe_str(req.get("description", "")),
            "rationale": safe_str(req.get("rationale", "")),
            "keywords": compact_list(req.get("keywords", [])),
            "evaluation_criteria": compact_list(req.get("evaluation_criteria", [])),
            "expected_evidence_types": compact_list(req.get("expected_evidence_types", [])),
        }

    def _summarize_requirement_expectations(
        self,
        requirements: List[Dict[str, Any]],
    ) -> str:
        lines: List[str] = []

        for req in requirements:
            rid = safe_str(req.get("id", ""))
            title = safe_str(req.get("title", ""))
            criteria = compact_list(req.get("evaluation_criteria", []), limit=5)
            evidence_types = compact_list(req.get("expected_evidence_types", []), limit=6)

            lines.append(f"- {rid} | {title}")

            if criteria:
                lines.append("  Evaluation criteria:")
                for item in criteria:
                    lines.append(f"    - {item}")

            if evidence_types:
                lines.append("  Expected evidence types:")
                for item in evidence_types:
                    lines.append(f"    - {item}")

        return "\n".join(lines).strip()
    def _build_module_project_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        base_terms = compact_list(
            [safe_str(r.get("title", "")) for r in requirements[:4]],
            limit=4,
        )
        keywords = self._collect_requirement_keywords(
            requirements,
            key="keywords",
            per_requirement_limit=3,
            total_limit=8,
        )
        evidence_types = self._collect_requirement_keywords(
            requirements,
            key="expected_evidence_types",
            per_requirement_limit=3,
            total_limit=8,
        )

        primary_parts = [module_name] + base_terms + keywords[:5] + evidence_types[:4]
        primary_query = " | ".join([p for p in primary_parts if p])

        secondary_parts = [module_name] + evidence_types[:5] + [
            "evidência documental",
            "registro",
            "plano",
            "contrato",
            "relatório",
        ]
        secondary_query = " | ".join([p for p in secondary_parts if p])

        if query_boost:
            primary_query += " | evidência objetiva | prova | rastreabilidade | documento fonte"
            secondary_query += " | verificação | anexo | comprovação"

        return unique_preserve_order([primary_query, secondary_query, module_name])
        
    def _build_module_methodology_queries(
        self,
        module_name: str,
        requirements: List[Dict[str, Any]],
        query_boost: bool = False,
    ) -> List[str]:
        descriptions = compact_list(
            [safe_str(req.get("description", ""))[:180] for req in requirements[:4]],
            limit=4,
        )
        criteria = self._collect_requirement_keywords(
            requirements,
            key="evaluation_criteria",
            per_requirement_limit=3,
            total_limit=10,
        )
        evidence_types = self._collect_requirement_keywords(
            requirements,
            key="expected_evidence_types",
            per_requirement_limit=2,
            total_limit=6,
        )

        primary_parts = [module_name] + descriptions[:3] + criteria[:5]
        primary_query = " | ".join([p for p in primary_parts if p])

        secondary_parts = [module_name] + criteria[:5] + evidence_types[:4] + [
            "requirement",
            "criteria",
            "methodology",
        ]
        secondary_query = " | ".join([p for p in secondary_parts if p])

        if query_boost:
            primary_query += " | compliance criteria | requirement basis | methodology requirement"
            secondary_query += " | eligibility | verification | evidence requirement"

        return unique_preserve_order([primary_query, secondary_query, module_name])
        
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
                    self._format_requirement_brief(req),
                    ensure_ascii=False,
                )
            )

        req_block = "\n".join(req_lines)
        expectation_block = self._summarize_requirement_expectations(requirements)

        return f"""
Você está avaliando requisitos metodológicos de auditoria documental para um projeto de carbono.

OBJETIVO:
Avaliar cada requisito com base APENAS nos trechos recuperados do projeto e da metodologia.

REGRAS CRÍTICAS:
- Retorne APENAS JSON válido.
- Não escreva explicações fora do JSON.
- Não invente fatos ausentes.
- Use somente os trechos fornecidos.
- Não defina status, score ou risk.
- Seja conservador quando a evidência for fraca.
- Diferencie claramente:
  - evidência do projeto
  - base metodológica
  - lacuna
  - recomendação
- Considere explicitamente os evaluation_criteria e expected_evidence_types de cada requisito.
- Se a evidência encontrada for apenas indireta, incompleta ou genérica, deixe isso claro em gap ou notes.
- Não trate narrativa genérica como conformidade robusta.

INSTRUÇÕES DE AVALIAÇÃO:
Para cada requisito:
1. Identifique a evidência documental do projeto mais relevante.
2. Identifique a base metodológica mais relevante.
3. Avalie se a evidência atende substancialmente aos critérios esperados.
4. Considere se os tipos de evidência esperados aparecem de forma explícita ou implícita.
5. Descreva a principal lacuna remanescente.
6. Recomende a ação mais útil para auditoria, validação ou robustez documental.
7. Defina confidence entre 0 e 100 com conservadorismo.

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

Requisitos estruturados:
{req_block}

Resumo das expectativas por requisito:
{expectation_block}

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
