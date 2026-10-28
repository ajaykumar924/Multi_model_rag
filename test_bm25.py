
from retrieval.retriever import retrieve_bm25

query = "What health benefits do employees receive?"

print("Query:", query)

results = retrieve_bm25(query, k=3)

print("Number of results:", len(results))

for result in results:
    print("\nContent:", result["content"])
    print("Source:", result["metadata"].get("source"))
    print("BM25 score:", round(result["score"], 4))
