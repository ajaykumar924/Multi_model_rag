
from retrieval.retriever import retrieve_hybrid_reranked

query = "How many days of sick leave can an employee take?"

results = retrieve_hybrid_reranked(
    query=query,
    k=10,
    top_n=3
)

for i, doc in enumerate(results, start=1):
    print(f"\nRank {i}")
    print(f"Score: {doc['score']}")
    print(f"Content: {doc['text'][:500]}")
