
from flashrank import Ranker, RerankRequest

# Create the reranker once
ranker = Ranker()


def rerank_documents(query, documents, top_n=6):
    """Rerank documents and ensure representation across different source documents."""

    if not documents:
        return []

    passages = []

    for i, doc in enumerate(documents):
        passages.append({
            "id": i,
            "text": doc["content"],
            "meta": doc.get("metadata", {}),
        })

    request = RerankRequest(
        query=query,
        passages=passages,
    )

    results = ranker.rerank(request)

    # Pick top results while ensuring representation across different documents
    reranked_documents = []
    seen_sources = set()

    # Pass 1: Include the best chunk from each unique source document
    for result in results:
        source = result.get("meta", {}).get("source")
        if source and source not in seen_sources:
            reranked_documents.append({
                "content": result["text"],
                "metadata": result.get("meta", {}),
                "rerank_score": result.get("score", 0.0),
            })
            seen_sources.add(source)
            if len(reranked_documents) == top_n:
                break

    # Pass 2: Fill any remaining slots with the next highest-ranked chunks
    if len(reranked_documents) < top_n:
        chosen_texts = {doc["content"] for doc in reranked_documents}
        for result in results:
            if result["text"] not in chosen_texts:
                reranked_documents.append({
                    "content": result["text"],
                    "metadata": result.get("meta", {}),
                    "rerank_score": result.get("score", 0.0),
                })
                if len(reranked_documents) == top_n:
                    break

    return reranked_documents
