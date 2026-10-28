from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings


def semantic_chunking(documents):
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=80,
    )

    return splitter.split_documents(documents)