import json
import time
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI


SYSTEM_AUDITOR_PROMPT = """
Você é uma auditora técnica especializada em avaliação metodológica de projetos de remoção de carbono via biochar.

Sua tarefa é avaliar UM requisito por vez, comparando:
1. trechos da documentação do projeto
2. trechos da metodologia

Regras obrigatórias:
- Use exclusivamente os trechos fornecidos.
- Não invente fatos.
- Não preencha lacunas com suposições.
- Se a evidência não estiver presente, diga explicitamente.
- Diferencie ausência documental, inconsistência documental e potencial não conformidade.
- Responda sempre em JSON válido.

Saída obrigatória:
{
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

Regras adicionais:
- score deve ser inteiro entre 0 e 100
- confidence deve ser inteiro entre 0 e 100
- status deve refletir estritamente a evidência disponível
- se houver erro técnico ou contexto insuficiente extremo, usar "Erro de análise" ou "Não evidenciado"
"""

DEFAULT_PROJECT_QUERIES_PER_REQUIREMENT = 3
DEFAULT_METHODOLOGY_QUERIES_PER_REQUIREMENT = 3
DEFAULT_PROJECT_MAX_RESULTS_PER_QUERY = 6
DEFAULT_METHODOLOGY_MAX_RESULTS_PER_QUERY = 6
DEFAULT_MAX_RETRIES = 5


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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
    if raw in {"baixo", "medio", "alto"}:
        return raw
    if raw == "médio":
        return "medio"
    return "alto"


def clip_int(value: Any, min_value: int = 0, max_value: int = 100, default: int = 0) -> int:
    try:
        v = int(value)
        return max(min_value, min(max_value, v))
    except Exception:
        return default


class AuditEngine:
    def __init__(
        self,
        api_key: str,
        model: str,
        project_vector_store_id: str,
        methodology_vector_store_id: str,
        project_name: str = "Projeto",
        project_queries_per_requirement: int = DEFAULT_PROJECT_QUERIES_PER_REQUIREMENT,
        methodology_queries_per_requirement: int = DEFAULT_METHODOLOGY_QUERIES_PER_REQUIREMENT,
        project_max_results_per_query: int = DEFAULT_PROJECT_MAX_RESULTS_PER_QUERY,
        methodology_max_results_per_query: int = DEFAULT_METHODOLOGY_MAX_RESULTS_PER_QUERY,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.project_vector_store_id = project_vector_store_id
        self.methodology_vector_store_id = methodology_vector_store_id
        self.project_name = project_name

        self.project_queries_per_requirement = project_queries_per_requirement
        self.methodology_queries_per_requirement = methodology_queries_per_requirement
        self.project_max_results_per_query = project_max_results_per_query
        self.methodology_max_results_per_query = methodology_max_results_per_query
        self.max_retries = max_retries

    # =========================================================
    # PUBLIC API
    # =========================================================

    def run_full_audit(self, selected_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        from isometric_requirements import ISOMETRIC_REQUIREMENTS

        filtered_requirements = []
        for req in ISOMETRIC_REQUIREMENTS:
            if selected_modules and req.get("module") not in selected_modules:
                continue
            filtered_requirements.append(req)

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results: List[Dict[str, Any]] = []
        trails: List[Dict[str, Any]] = []

        for req in filtered_requirements:
            result, trail = self._audit_single_requirement(req)
            results.append(result)
            trails.append(trail)

        return {
            "run_id": run_id,
            "results": results,
            "trails": trails,
        }

    def summarize_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)

        status_counts: Dict[str, int] = {}
        risk_counts: Dict[str, int] = {}
        module_scores_raw: Dict[str, List[int]] = {}

        for item in results:
            status = safe_str(item.get("status", "Erro de análise"))
            risk = safe_str(item.get("risk", "alto"))
            module = safe_str(item.get("module", "Sem módulo"))
            score = clip_int(item.get("score", 0), default=0)

            status_counts[status] = status_counts.get(status, 0) + 1
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

            module_scores_raw.setdefault(module, []).append(score)

        module_scores = {}
        for module, scores in module_scores_raw.items():
            if scores:
                module_scores[module] = round(sum(scores) / len(scores), 1)
            else:
                module_scores[module] = 0.0

        overall_score = 0.0
        if total > 0:
            overall_score = round(sum(clip_int(r.get("score", 0), default=0) for r in results) / total, 1)

        return {
            "total_requirements": total,
            "overall_score": overall_score,
            "status_counts": status_counts,
            "risk_counts": risk_counts,
            "module_scores": module_scores,
        }

    # =========================================================
    # SINGLE REQUIREMENT AUDIT
    # =========================================================

    def _audit_single_requirement(self, requirement: Dict[str, Any]):
        requirement_id = safe_str(requirement.get("id", "REQ"))
        module = safe_str(requirement.get("module", "Sem módulo"))
        title = safe_str(requirement.get("title", "Sem título"))
        description = safe_str(requirement.get("description", ""))
        keywords = requirement.get("keywords", []) or []
        if not isinstance(keywords, list):
            keywords = [safe_str(keywords)]

        project_queries = self._build_project_queries(requirement_id, module, title, description, keywords)
        methodology_queries = self._build_methodology_queries(requirement_id, module, title, description, keywords)

        project_queries = project_queries[: self.project_queries_per_requirement]
        methodology_queries = methodology_queries[: self.methodology_queries_per_requirement]

        project_hits = self._run_multi_query_file_search(
            vector_store_id=self.project_vector_store_id,
            queries=project_queries,
            max_num_results=self.project_max_results_per_query,
            source_label="project",
        )

        methodology_hits = self._run_multi_query_file_search(
            vector_store_id=self.methodology_vector_store_id,
            queries=methodology_queries,
            max_num_results=self.methodology_max_results_per_query,
            source_label="methodology",
        )

        project_context = self._format_hits_for_prompt(project_hits, "PROJETO")
        methodology_context = self._format_hits_for_prompt(methodology_hits, "METODOLOGIA")

        model_prompt = self._build_requirement_prompt(
            requirement=requirement,
            project_context=project_context,
            methodology_context=methodology_context,
        )

        raw_model_response = ""
        parsed_result = None

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
            parsed_result = try_parse_json(raw_model_response)
        except Exception as e:
            raw_model_response = json.dumps(
                {
                    "status": "Erro de análise",
                    "risk": "alto",
                    "score": 0,
                    "confidence": 0,
                    "project_evidence": "",
                    "methodology_basis": "",
                    "gap": f"Erro técnico durante análise do requisito: {str(e)}",
                    "recommendation": "Reexecutar a análise com retry e revisar limites de taxa e contexto.",
                    "notes": f"Exceção capturada pelo motor de auditoria: {str(e)}",
                },
                ensure_ascii=False,
                indent=2,
            )
            parsed_result = try_parse_json(raw_model_response)

        normalized = self._normalize_requirement_result(
            requirement=requirement,
            parsed_result=parsed_result,
            project_hits=project_hits,
            methodology_hits=methodology_hits,
            raw_model_response=raw_model_response,
        )

        trail = {
            "requirement_id": requirement_id,
            "module": module,
            "title": title,
            "project_queries": project_queries,
            "methodology_queries": methodology_queries,
            "project_query": "\n".join(project_queries),
            "methodology_query": "\n".join(methodology_queries),
            "project_hits": project_hits,
            "methodology_hits": methodology_hits,
            "project_context": project_context,
            "methodology_context": methodology_context,
            "model_prompt": model_prompt,
            "model_response_raw": raw_model_response,
            "parsed_result": normalized,
        }

        return normalized, trail

    # =========================================================
    # QUERIES
    # =========================================================

    def _build_project_queries(
        self,
        requirement_id: str,
        module: str,
        title: str,
        description: str,
        keywords: List[str],
    ) -> List[str]:
        keyword_str = " ".join([safe_str(k) for k in keywords if safe_str(k).strip()])
        queries = [
            f"{self.project_name} {title}",
            f"{module} {title} {keyword_str}",
            f"{requirement_id} {title} {description}",
            f"{title} evidence monitoring documentation",
            f"{module} project evidence {keyword_str}",
        ]
        return self._dedupe_preserve_order([q.strip() for q in queries if q.strip()])

    def _build_methodology_queries(
        self,
        requirement_id: str,
        module: str,
        title: str,
        description: str,
        keywords: List[str],
    ) -> List[str]:
        keyword_str = " ".join([safe_str(k) for k in keywords if safe_str(k).strip()])
        queries = [
            f"{requirement_id} {title}",
            f"{module} {title} {keyword_str}",
            f"{title} methodology requirement {description}",
            f"{module} methodology criteria {keyword_str}",
            f"{requirement_id} methodological basis",
        ]
        return self._dedupe_preserve_order([q.strip() for q in queries if q.strip()])

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
                safe_str(hit.get("text"))[:300],
                safe_str(hit.get("query")),
                safe_str(hit.get("source_label")),
            )
            if key not in seen:
                seen.add(key)
                unique.append(hit)

        unique.sort(key=lambda x: float(x.get("score", 0) or 0), reverse=True)
        return unique

    # =========================================================
    # PROMPT BUILDING
    # =========================================================

    def _format_hits_for_prompt(self, hits: List[Dict[str, Any]], block_name: str) -> str:
        if not hits:
            return f"[{block_name}] Nenhum trecho recuperado."

        lines = [f"[{block_name}]"]

        for i, hit in enumerate(hits, start=1):
            filename = safe_str(hit.get("filename", "Documento sem nome"))
            page = safe_str(hit.get("page", "")) or "não identificada"
            score = safe_str(hit.get("score", ""))
            query = safe_str(hit.get("query", ""))
            text = safe_str(hit.get("text", ""))
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

    def _build_requirement_prompt(
        self,
        requirement: Dict[str, Any],
        project_context: str,
        methodology_context: str,
    ) -> str:
        requirement_id = safe_str(requirement.get("id", "REQ"))
        module = safe_str(requirement.get("module", "Sem módulo"))
        title = safe_str(requirement.get("title", "Sem título"))
        description = safe_str(requirement.get("description", ""))
        rationale = safe_str(requirement.get("rationale", ""))
        keywords = requirement.get("keywords", []) or []

        return f"""
Avalie o requisito abaixo.

REQUISITO
- ID: {requirement_id}
- Módulo: {module}
- Título: {title}
- Descrição: {description}
- Racional: {rationale}
- Palavras-chave: {", ".join([safe_str(k) for k in keywords])}

INSTRUÇÕES
1. Leia a base metodológica e identifique o critério aplicável.
2. Leia os trechos do projeto e identifique a evidência disponível.
3. Compare ambos.
4. Classifique o status.
5. Atribua risco e score.
6. Explique a lacuna principal.
7. Recomende a ação corretiva mais útil.

CONTEXTO DO PROJETO
{project_context}

CONTEXTO DA METODOLOGIA
{methodology_context}
""".strip()

    # =========================================================
    # RESULT NORMALIZATION
    # =========================================================

    def _normalize_requirement_result(
        self,
        requirement: Dict[str, Any],
        parsed_result: Optional[Dict[str, Any]],
        project_hits: List[Dict[str, Any]],
        methodology_hits: List[Dict[str, Any]],
        raw_model_response: str,
    ) -> Dict[str, Any]:
        requirement_id = safe_str(requirement.get("id", "REQ"))
        module = safe_str(requirement.get("module", "Sem módulo"))
        title = safe_str(requirement.get("title", "Sem título"))

        if not parsed_result:
            parsed_result = {
                "status": "Erro de análise",
                "risk": "alto",
                "score": 0,
                "confidence": 0,
                "project_evidence": "",
                "methodology_basis": "",
                "gap": "O modelo não retornou JSON válido para este requisito.",
                "recommendation": "Reexecutar análise do requisito com contexto mais enxuto e retry.",
                "notes": raw_model_response[:3000],
            }

        result = {
            "requirement_id": requirement_id,
            "module": module,
            "title": title,
            "status": normalize_status(parsed_result.get("status", "Erro de análise")),
            "risk": normalize_risk(parsed_result.get("risk", "alto")),
            "score": clip_int(parsed_result.get("score", 0), default=0),
            "confidence": clip_int(parsed_result.get("confidence", 0), default=0),
            "project_evidence": safe_str(parsed_result.get("project_evidence", "")),
            "methodology_basis": safe_str(parsed_result.get("methodology_basis", "")),
            "gap": safe_str(parsed_result.get("gap", "")),
            "recommendation": safe_str(parsed_result.get("recommendation", "")),
            "notes": safe_str(parsed_result.get("notes", "")),
        }

        if not result["project_evidence"]:
            result["project_evidence"] = self._fallback_project_evidence(project_hits)

        if not result["methodology_basis"]:
            result["methodology_basis"] = self._fallback_methodology_basis(methodology_hits)

        if not result["gap"]:
            result["gap"] = self._infer_gap(result["status"], project_hits, methodology_hits)

        if not result["recommendation"]:
            result["recommendation"] = self._infer_recommendation(result["status"])

        return result

    def _fallback_project_evidence(self, project_hits: List[Dict[str, Any]]) -> str:
        usable = [h for h in project_hits if safe_str(h.get("text")).strip()]
        if not usable:
            return "Não foi possível identificar evidência documental suficiente do projeto nos trechos recuperados."
        return self._join_top_hits(usable, top_n=3)

    def _fallback_methodology_basis(self, methodology_hits: List[Dict[str, Any]]) -> str:
        usable = [h for h in methodology_hits if safe_str(h.get("text")).strip()]
        if not usable:
            return "Não foi possível identificar base metodológica suficiente nos trechos recuperados."
        return self._join_top_hits(usable, top_n=3)

    def _join_top_hits(self, hits: List[Dict[str, Any]], top_n: int = 3) -> str:
        parts = []
        for hit in hits[:top_n]:
            filename = safe_str(hit.get("filename", "Documento sem nome"))
            page = safe_str(hit.get("page", "")) or "não identificada"
            text = safe_str(hit.get("text", ""))
            parts.append(f"{filename} (pág./seção: {page}): {text}")
        return "\n\n".join(parts)

    def _infer_gap(
        self,
        status: str,
        project_hits: List[Dict[str, Any]],
        methodology_hits: List[Dict[str, Any]],
    ) -> str:
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
    # OPENAI HELPERS WITH RETRY
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

                sleep_seconds = self._compute_backoff_seconds(attempt)
                time.sleep(sleep_seconds)

        raise last_exception

    def _compute_backoff_seconds(self, attempt: int) -> float:
        base = min(2 ** attempt, 20)
        jitter = random.uniform(0.3, 1.2)
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
