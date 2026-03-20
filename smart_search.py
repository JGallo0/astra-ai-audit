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
    selected = ranked_sources[:max_items]

    if not selected:
        return (
            "Pergunta do usuário:\n"
            + str(query)
            + "\n\n"
            + "Nenhuma evidência relevante encontrada nas bases consultadas."
        )

    blocks = []

    for i, s in enumerate(selected, 1):
        source_type = (s.get("source_type") or "unknown").upper()
        filename = s.get("filename") or "Documento sem nome"
        page = s.get("page") or "não identificada"
        text = s.get("text") or ""

        blocks.append(
            f"[EVIDÊNCIA {i}] ({source_type})\n"
            f"Documento: {filename}\n"
            f"Página/Seção: {page}\n"
            f"Trecho:\n{text}\n"
        )

    return (
        "Pergunta do usuário:\n"
        + str(query)
        + "\n\n"
        + "Responda usando EXCLUSIVAMENTE as evidências abaixo.\n"
        + "Compare Projeto × Metodologia quando aplicável.\n"
        + "Se houver evidência insuficiente, diga isso explicitamente.\n\n"
        + "\n".join(blocks)
    )
