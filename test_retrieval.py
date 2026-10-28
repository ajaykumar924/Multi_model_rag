
from vector_store.postgres_store import get_text_store

store = get_text_store()

# Test 1: Search by meaning
query = "What health benefits do employees receive?"

results = store.similarity_search_with_score(query, k=3)

print("\n--- Similarity Search Results ---")

for doc, score in results:
    print("\nDocument:", doc.page_content)
    print("Metadata:", doc.metadata)
    print("Distance score:", score)

# Test 2: Search only documents from a particular source
filtered_results = store.similarity_search(
    "employee benefits",
    k=3,
    filter={"source": "hr_policy.pdf"},
)

print("\n--- Filtered Results ---")

for doc in filtered_results:
    print("Document:", doc.page_content)
    print("Metadata:", doc.metadata)
