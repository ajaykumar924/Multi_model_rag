def image_chunking(documents):
    return [
        doc for doc in documents
        if doc.metadata.get("image_path")
    ]
    