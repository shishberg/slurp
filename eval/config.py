from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import MarkdownTextSplitter

TEST_CASES = [
    {
        "name": "Baseline",
        "embedding_model": OpenAIEmbeddings(model="text-embedding-ada-002"),
        "chunking_function": MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100),
        "llm": ChatOpenAI(model="gpt-3.5-turbo"),
        "prompt_template": "default"
    }
]