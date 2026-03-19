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
    query = query.lower()
    text = text.lower()

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

        weight = 1.2 if s["source_type"] == "project" else 1.0

        final_score = (base_score * 0.6 + relevance * 0.4) * weight

        s["final_score"] = final_score
        ranked.append(s)

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked


def build_smart_context(query: str, ranked_sources: List[Dict], max_items=8) -> str:
    selected = ranked_sources[:max_items]

    if not selected:
        return "Nenhuma evidência relevante encontrada."

    blocks = []

    for i, s in enumerate(selected, 1):
        blocks.append(
            f"[EVIDÊNCIA {i}] ({s['source_type'].upper()})\n"
            f"Documento: {s.get('filename')}\n"
            f"Trecho:\n{s.get('text')}\n"
        )

    return f"""
Pergunta:
{query}

Use EXCLUSIVAMENTE as evidências abaixo.

{chr(10).join(blocks)}
"""
