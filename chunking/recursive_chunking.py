from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_chunking(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )

    return splitter.split_documents(documents)