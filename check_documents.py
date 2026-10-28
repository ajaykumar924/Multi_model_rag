
from collections import Counter

from retrieval.retriever import get_all_text_documents


# Load documents from PostgreSQL
documents = get_all_text_documents()

print("Total stored documents:", len(documents))

if not documents:
    print("No documents found in the text collection.")

else:
    # Count documents by source file
    source_counts = Counter(
        doc["metadata"].get("source", "Unknown source")
        for doc in documents
    )

    print("\nDocuments grouped by source:")

    for source, count in source_counts.items():
        print(f"{source}: {count}")

    # Display a few real documents
    print("\n--- SAMPLE DOCUMENTS ---")

    for index, doc in enumerate(documents[:5], start=1):
        print(f"\nDocument {index}")
        print("Source:", doc["metadata"].get("source"))
        print("Content:", doc["content"][:300])
