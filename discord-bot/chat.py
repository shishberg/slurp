from common import logger

from langchain_openai import ChatOpenAI
import asyncio
import os
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
import dotenv

dotenv.load_dotenv()

log = logger(__name__)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "slurp")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

embeddings = PineconeEmbeddings(
    model="llama-text-embed-v2",
)

# Create Pinecone vector store and retriever
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX,
    embedding=embeddings,
    namespace=PINECONE_NAMESPACE,
    text_key="text",
)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


@tool
def knowledge_base_search(query: str, num_results: int = 5) -> dict:
    """Searches the knowledge base for results semantically matching the query."""
    log.info(f'Searching knowledge base query="{query}" k={num_results}')
    query_embedding = embeddings.embed_query(query)
    raw_results = index.query(
        vector=query_embedding,
        top_k=num_results,
        include_metadata=True,
        namespace=PINECONE_NAMESPACE,
    )

    documents = []
    for match in raw_results.matches:
        if match.metadata and "text" in match.metadata:
            doc = match.metadata
            documents.append(doc)

    log.info(f"Retriever found {len(documents)} documents")
    return documents


class ResponseFormatter(BaseModel):
    """Response to the user's question."""

    answer: str = Field(description="Answer to the user's question")
    title: Optional[str] = Field(description="Title of the chat thread", default=None)


MODEL_CLAUDE_SONNET_4 = "anthropic/claude-sonnet-4"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

base_llm = ChatOpenAI(
    model=MODEL_CLAUDE_SONNET_4,
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=OPENROUTER_BASE_URL,
    streaming=False,
)


def tool_name(tool) -> str:
    if hasattr(tool, "name"):
        return tool.name.lower()
    return tool.__name__.lower()


tools = [knowledge_base_search, ResponseFormatter]
tools_by_name = {tool_name(tool): tool for tool in tools}


llm_with_tools = base_llm.bind_tools(tools)
llm_without_tools = base_llm.bind_tools([ResponseFormatter])


def get_datetime(_):
    return datetime.now().strftime("%A %d %B, %I:%M%p")


async def invoke(messages: list[BaseMessage]):
    try:
        template = """
You are a helpful AI chatbot. Your name is Slurp. You answer parents' questions about correspondence
with their children's school. If there's something specifically relevant to the parent's children or
their class then draw attention to that, but only if it's specific. Don't mention the children at all
if the information is general to the school or relevant to all the children.

Answer as succinctly as possible.

If this is the first message, also return a title for the chat thread, in at most five words.
Examples of good titles:
- "Athletics Carnival Date"
- "Math Homework Policy"
- "School Uniform Change"

The user has two children:
  - Toby McLeish, in the Bats class in year 6
  - Rosemary (Rosie) McLeish, in the Grasshoppers class in year 4

The current date and time is {current_datetime}. You can trust this.

Answer ONLY using the ResponseFormatter tool.
"""

        prompt = template.replace(
            "{current_datetime}", get_datetime(None)
        )  # TODO: bind
        messages = [SystemMessage(prompt)] + messages
        last_response = None

        MAX_TOOL_CALLS = 3
        for i in range(MAX_TOOL_CALLS):
            llm = llm_with_tools if i < (MAX_TOOL_CALLS - 1) else llm_without_tools
            response = await llm.ainvoke(messages)
            messages.append(response)
            reflect = False

            last_response = None

            # In case the model ignores the request to format the response
            if response.content:
                last_response = ResponseFormatter(answer=str(response.content))

            for tool_call in response.tool_calls:
                log.info(f"Calling tool: {tool_call}")
                tool = tools_by_name[tool_call["name"].lower()]
                is_pydantic = False
                try:
                    is_pydantic = issubclass(tool, BaseModel)
                except TypeError:
                    pass
                if is_pydantic:
                    tool_result = tool(**tool_call["args"])
                    last_response = tool_result
                else:
                    reflect = True
                    tool_result = await tool.ainvoke(tool_call)
                messages.append(tool_result)
            if not reflect:
                break

        return last_response

    except Exception as e:
        return ResponseFormatter(answer="⚠️ " + str(e))


if __name__ == "__main__":
    messages = [HumanMessage("What is the date of the 2025 athletics carnival?")]
    log.info(asyncio.run(invoke(messages)))
