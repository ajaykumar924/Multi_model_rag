from langchain_openai import OpenAIEmbeddings


def get_text_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small"
    )