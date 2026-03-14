# audit_engine.py

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI
from isometric_requirements import ISOMETRIC_REQUIREMENTS


ALLOWED_STATUS = ["Conforme", "Parcial", "Não conforme", "Não evidenciado"]
ALLOWED_RISK = ["Baixo", "Médio", "Alto"]


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Tenta extrair um objeto JSON válido a partir da resposta do modelo.
    """
    if not text:
        raise ValueError("Resposta vazia do modelo.")

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise ValueError("Não foi possível extrair JSON válido da resposta.")


def normalize_status(value: Optional[str]) -> str:
    if not value:
        return "Não evidenciado"

    v = value.strip().lower()
    mapping = {
        "conforme": "Conforme",
        "parcial": "Parcial",
        "não conforme": "Não conforme",
        "nao conforme": "Não conforme",
        "não evidenciado": "Não evidenciado",
        "nao evidenciado": "Não evidenciado",
    }
    return mapping.get(v, "Não evidenciado")


def normalize_risk(value: Optional[str], status: Optional[str] = None) -> str:
    if not value:
        if status in ["Não conforme", "Não evidenciado"]:
            return "Alto"
        if status == "Parcial":
            return "Médio"
        return "Baixo"

    v = value.strip().lower()
    mapping = {
        "baixo": "Baixo",
        "médio": "Médio",
        "medio": "Médio",
        "alto": "Alto",
    }
    risk = mapping.get(v)

    if risk:
        if status == "Não evidenciado" and risk == "Baixo":
            return "Alto"
        if status == "Não conforme" and risk == "Baixo":
            return "Alto"
        return risk

    if status in ["Não conforme", "Não evidenciado"]:
        return "Alto"
    if status == "Parcial":
        return "Médio"
    return "Baixo"


def score_from_status(status: str) -> int:
    mapping = {
        "Conforme": 100,
        "Parcial": 50,
        "Não conforme": 0,
        "Não evidenciado": 0,
    }
    return mapping.get(status, 0)


class AuditEngine:
    def __init__(
        self,
        api_key: str,
        model: str,
        project_vector_store_id: str,
        methodology_vector_store_id: str,
        project_name: str = "Projeto analisado",
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.project_vector_store_id = project_vector_store_id
        self.methodology_vector_store_id = methodology_vector_store_id
        self.project_name = project_name
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _search_vector_store(
        self,
        vector_store_id: str,
        query: str,
        max_results: int = 6
    ):
        return self.client.vector_stores.search(
            vector_store_id=vector_store_id,
            query=query,
            max_num_results=max_results,
        )

    def _format_search_results(self, search_result) -> str:
        """
        Converte a resposta de vector_stores.search em texto legível para usar no prompt.
        """
        if not search_result:
            return "Nenhum resultado recuperado."

        data = getattr(search_result, "data", None)
        if not data:
            return "Nenhum resultado recuperado."

        lines = []
        for i, item in enumerate(data, start=1):
            filename = getattr(item, "filename", None) or getattr(item, "file_id", "arquivo_desconhecido")
            score = getattr(item, "score", None)
            attributes = getattr(item, "attributes", None)

            parts = []
            content_blocks = getattr(item, "content", []) or []
            for block in content_blocks:
                text_value = getattr(block, "text", None)
                if text_value:
                    parts.append(text_value.strip())

            excerpt = "\n".join([p for p in parts if p]).strip()
            if not excerpt:
                excerpt = "[Sem trecho textual recuperado]"

            header = f"[{i}] Fonte: {filename}"
            if isinstance(score, (int, float)):
                header += f" | score={score:.3f}"
            if attributes:
                header += f" | attrs={attributes}"

            lines.append(f"{header}\n{excerpt}")

        return "\n\n".join(lines)

    def _build_project_query(self, requirement: Dict[str, Any]) -> str:
        keywords = " OR ".join(requirement.get("keywords_project", []))
        expected_docs = ", ".join(requirement.get("expected_documents", []))
        return (
            f"{requirement['title']} {requirement['description']} "
            f"{keywords} documentos esperados: {expected_docs}"
        )

    def _build_methodology_query(self, requirement: Dict[str, Any]) -> str:
        keywords = " OR ".join(requirement.get("keywords_methodology", []))
        return f"{requirement['title']} {requirement['description']} {keywords}"

    def _build_evaluation_prompt(
        self,
        requirement: Dict[str, Any],
        project_context: str,
        methodology_context: str,
    ) -> str:
        return f"""
Você é um auditor técnico especializado em projetos de remoção de carbono via biochar.

O objetivo é avaliar UM requisito metodológico de forma conservadora e objetiva.

PROJETO
Nome: {self.project_name}

REQUISITO
ID: {requirement['id']}
Módulo: {requirement['module']}
Título: {requirement['title']}
Descrição: {requirement['description']}
Severidade: {requirement.get('severity', 'medium')}
Documentos esperados: {", ".join(requirement.get('expected_documents', []))}

TRECHOS RECUPERADOS DO PROJETO
{project_context}

TRECHOS RECUPERADOS DA METODOLOGIA
{methodology_context}

INSTRUÇÕES CRÍTICAS
- Use apenas os trechos mostrados.
- Se a evidência não estiver claramente presente nos trechos recuperados, classifique como "Não evidenciado" ou "Parcial".
- Nunca invente evidência, seção, anexo, tabela, dado ou referência.
- Seja conservador.
- A "evidência do projeto" deve ser um resumo curto da principal evidência encontrada.
- A "base metodológica" deve ser um resumo curto da principal exigência aplicável.
- A "lacuna" deve ser objetiva.
- A "recomendação" deve ser específica e acionável.
- O campo "confidence" é uma nota de 0 a 100 sobre a robustez da conclusão com base APENAS nos trechos recuperados.

REGRAS DE STATUS
- "Conforme" = requisito claramente atendido pelos trechos recuperados.
- "Parcial" = há evidência incompleta, ambígua ou insuficiente.
- "Não conforme" = os trechos indicam conflito claro com a exigência.
- "Não evidenciado" = não há evidência suficiente nos trechos recuperados.

REGRAS DE RISCO
- "Baixo" = baixa chance de objeção de auditoria para este requisito.
- "Médio" = risco moderado ou lacunas relevantes.
- "Alto" = alta chance de objeção, bloqueio ou necessidade de correção material.

Responda SOMENTE em JSON válido com esta estrutura exata:
{{
  "requirement_id": "{requirement['id']}",
  "module": "{requirement['module']}",
  "title": "{requirement['title']}",
  "status": "Conforme | Parcial | Não conforme | Não evidenciado",
  "risk": "Baixo | Médio | Alto",
  "project_evidence": "string",
  "methodology_basis": "string",
  "gap": "string",
  "recommendation": "string",
  "confidence": 0,
  "notes": "string"
}}
""".strip()

    def evaluate_requirement(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        project_query = self._build_project_query(requirement)
        methodology_query = self._build_methodology_query(requirement)

        project_search = self._search_vector_store(
            self.project_vector_store_id,
            project_query,
            max_results=6,
        )
        methodology_search = self._search_vector_store(
            self.methodology_vector_store_id,
            methodology_query,
            max_results=6,
        )

        project_context = self._format_search_results(project_search)
        methodology_context = self._format_search_results(methodology_search)

        prompt = self._build_evaluation_prompt(
            requirement=requirement,
            project_context=project_context,
            methodology_context=methodology_context,
        )

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        raw_text = getattr(response, "output_text", "") or ""
        parsed = extract_json_object(raw_text)

        status = normalize_status(parsed.get("status"))
        risk = normalize_risk(parsed.get("risk"), status=status)

        result = {
            "requirement_id": requirement["id"],
            "module": requirement["module"],
            "title": requirement["title"],
            "status": status,
            "risk": risk,
            "project_evidence": (parsed.get("project_evidence") or "").strip(),
            "methodology_basis": (parsed.get("methodology_basis") or "").strip(),
            "gap": (parsed.get("gap") or "").strip(),
            "recommendation": (parsed.get("recommendation") or "").strip(),
            "confidence": int(parsed.get("confidence", 0)) if str(parsed.get("confidence", "")).isdigit() else 0,
            "notes": (parsed.get("notes") or "").strip(),
            "score": score_from_status(status),
        }

        audit_trail = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "requirement_id": requirement["id"],
            "module": requirement["module"],
            "title": requirement["title"],
            "project_query": project_query,
            "methodology_query": methodology_query,
            "project_context": project_context,
            "methodology_context": methodology_context,
            "model_response_raw": raw_text,
            "parsed_result": result,
        }

        return {
            "result": result,
            "trail": audit_trail,
        }

    def run_full_audit(self, selected_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        requirements = ISOMETRIC_REQUIREMENTS

        if selected_modules:
            requirements = [r for r in requirements if r["module"] in selected_modules]

        results = []
        trails = []

        for requirement in requirements:
            try:
                evaluation = self.evaluate_requirement(requirement)
                results.append(evaluation["result"])
                trails.append(evaluation["trail"])
            except Exception as e:
                fallback = {
                    "requirement_id": requirement["id"],
                    "module": requirement["module"],
                    "title": requirement["title"],
                    "status": "Não evidenciado",
                    "risk": "Alto",
                    "project_evidence": "",
                    "methodology_basis": "",
                    "gap": f"Erro na avaliação automática: {str(e)}",
                    "recommendation": "Revisar logs, trechos recuperados e resposta bruta do modelo.",
                    "confidence": 0,
                    "notes": "",
                    "score": 0,
                }
                results.append(fallback)
                trails.append({
                    "run_id": self.run_id,
                    "timestamp": datetime.now().isoformat(),
                    "requirement_id": requirement["id"],
                    "module": requirement["module"],
                    "title": requirement["title"],
                    "project_query": "",
                    "methodology_query": "",
                    "project_context": "",
                    "methodology_context": "",
                    "model_response_raw": "",
                    "parsed_result": fallback,
                    "error": str(e),
                })

        return {
            "run_id": self.run_id,
            "results": results,
            "trails": trails,
        }

    @staticmethod
    def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {
                "total_requirements": 0,
                "overall_score": 0,
                "status_counts": {},
                "risk_counts": {},
                "module_scores": {},
            }

        status_counts = {k: 0 for k in ALLOWED_STATUS}
        risk_counts = {k: 0 for k in ALLOWED_RISK}
        module_buckets = {}

        for row in results:
            status = row.get("status", "Não evidenciado")
            risk = row.get("risk", "Alto")
            module = row.get("module", "Sem módulo")
            score = row.get("score", 0)

            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts["Não evidenciado"] += 1

            if risk in risk_counts:
                risk_counts[risk] += 1
            else:
                risk_counts["Alto"] += 1

            module_buckets.setdefault(module, [])
            module_buckets[module].append(score)

        module_scores = {
            module: round(sum(scores) / len(scores), 1)
            for module, scores in module_buckets.items()
        }

        overall_score = round(sum([r.get("score", 0) for r in results]) / len(results), 1)

        return {
            "total_requirements": len(results),
            "overall_score": overall_score,
            "status_counts": status_counts,
            "risk_counts": risk_counts,
            "module_scores": module_scores,
        }