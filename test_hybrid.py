
from retrieval.retriever import (
    retrieve_similarity,
    retrieve_bm25,
    retrieve_hybrid,
)

query = "What health benefits do employees receive?"


def show_results(title, results):
    print(f"\n--- {title} ---")

    if not results:
        print("No results found.")
        return

    for index, item in enumerate(results, start=1):
        print(f"\n{index}. Content:", item["content"])
        print("Source:", item["metadata"].get("source"))

        if "score" in item:
            print("BM25 score:", round(item["score"], 4))

        if "hybrid_score" in item:
            print("Hybrid score:", round(item["hybrid_score"], 4))


show_results(
    "SIMILARITY SEARCH",
    retrieve_similarity(query, k=3),
)

show_results(
    "BM25 SEARCH",
    retrieve_bm25(query, k=3),
)

show_results(
    "HYBRID SEARCH",
    retrieve_hybrid(query, k=3),
)
