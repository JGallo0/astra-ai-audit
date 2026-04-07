from typing import List, Dict, Any


def normalize_sources(sources: List[Dict[str, Any]], source_type: str) -> List[Dict]:
    normalized = []

    for s in sources:
        text = (s.get("text") or "").strip()
        if not text:
            continue

        normalized.append({
            "source_type": source_type,
            "filename": s.get("filename"),
            "page": s.get("page"),
            "text": text,
            "score": s.get("score", 0.0),
        })

    return normalized


def simple_relevance_score(query: str, text: str) -> float:
    query = (query or "").lower()
    text = (text or "").lower()

    score = 0.0

    for word in query.split():
        if word in text:
            score += 1.0

    return score / max(len(query.split()), 1)


def rank_sources(query: str, sources: List[Dict]) -> List[Dict]:
    ranked = []

    for s in sources:
        base_score = s.get("score", 0.0)
        relevance = simple_relevance_score(query, s.get("text", ""))

        weight = 1.2 if s.get("source_type") == "project" else 1.0

        final_score = (base_score * 0.6 + relevance * 0.4) * weight

        item = dict(s)
        item["final_score"] = final_score
        ranked.append(item)

    ranked.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
    return ranked


def build_smart_context(query: str, ranked_sources: List[Dict], max_items: int = 8) -> str:
    """
    Monta o contexto textual para o prompt do LLM.
    Cada evidencia e numerada com ID rastreaevel [EVIDENCIA N] que o LLM
    deve referenciar no campo citation.document ao extrair cada campo.
    """
    selected = ranked_sources[:max_items]

    if not selected:
        return (
            "Pergunta do usuario:\n"
            + str(query)
            + "\n\n"
            + "Nenhuma evidencia relevante encontrada nas bases consultadas."
        )

    blocks = []

    for i, s in enumerate(selected, 1):
        source_type = (s.get("source_type") or "unknown").upper()
        filename = s.get("filename") or "Documento sem nome"
        page = s.get("page") or "nao identificada"
        text = s.get("text") or ""

        blocks.append(
            f"[EVIDENCIA {i}] ({source_type})\n"
            f"Documento: {filename}\n"
            f"Pagina/Secao: {page}\n"
            f"Trecho:\n{text}\n"
        )

    return (
        "Pergunta do usuario:\n"
        + str(query)
        + "\n\n"
        + "Responda usando EXCLUSIVAMENTE as evidencias abaixo.\n"
        + "Compare Projeto x Metodologia quando aplicavel.\n"
        + "Se houver evidencia insuficiente, diga isso explicitamente.\n"
        + "IMPORTANTE: No campo citation, use o nome exato do documento e a pagina/secao\n"
        + "indicada no cabecalho de cada evidencia acima.\n\n"
        + "\n".join(blocks)
    )


def get_hits_index(ranked_sources: List[Dict], max_items: int = 8) -> Dict[str, List[Dict]]:
    """
    Retorna um indice {filename -> [hits]} com os metadados estruturados
    dos chunks selecionados. Usado pelos mappers para validar e enriquecer
    citacoes retornadas pelo LLM.
    """
    selected = ranked_sources[:max_items]
    index: Dict[str, List[Dict]] = {}
    for s in selected:
        filename = s.get("filename") or ""
        if filename:
            index.setdefault(filename, []).append({
                "filename": filename,
                "page": s.get("page") or "",
                "source_type": s.get("source_type") or "",
                "text": s.get("text") or "",
            })
    return index
