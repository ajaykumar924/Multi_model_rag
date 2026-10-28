'''

from langchain_core.documents import Document
from vector_store.postgres_store import save_text_documents

documents = [
    Document(
        page_content="Employees receive health insurance.",
        metadata={"source": "hr_policy.pdf"},
    ),
    Document(
        page_content="The company was founded in Bengaluru.",
        metadata={"source": "company_report.pdf"},
    ),
]

try:
    store = save_text_documents(documents)
    print("Documents saved successfully!")

    results = store.similarity_search(
        "What employee benefits are available?",
        k=2,
    )

    print("\nSearch results:")
    for doc in results:
        print("Content:", doc.page_content)
        print("Metadata:", doc.metadata)

except Exception as error:
    print("Test failed:", error)
'''

#test for image store 


from pathlib import Path

from ingestion.image_ingestion import load_image
from vector_store.image_store import (
    save_image_documents,
    search_images,
)

DATA_DIR = Path("data")


def test_image_store():
    image_documents = []

    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in {
            ".png", ".jpg", ".jpeg",
            ".tif", ".tiff", ".bmp",
        }:
            print("Loading:", path.name)
            image_documents.extend(load_image(str(path)))

    print("Image documents loaded:", len(image_documents))

    saved = save_image_documents(image_documents)
    print("Image records saved:", saved)

    results = search_images("A financial report", k=3)

    print("\n--- Image Search Results ---")

    for result in results:
        print("Image:", result["image_path"])
        print("Distance:", result["distance"])
        print("OCR text:", result["content"][:150])
        print("Metadata:", result["metadata"])
        print()


if __name__ == "__main__":
    test_image_store()
