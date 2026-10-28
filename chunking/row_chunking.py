def row_chunking(documents):
    return [
        doc for doc in documents
        if doc.page_content.strip()
    ]