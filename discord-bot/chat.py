from common import logger

from langchain_openai import ChatOpenAI
import asyncio
import os
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
import dotenv

dotenv.load_dotenv()

log = logger(__name__)


class ResponseFormatter(BaseModel):
    """Final response to the user's question after using other tools to fetch relevant information."""

    answer: str = Field(description="Answer to the user's question")
    title: Optional[str] = Field(description="Title of the chat thread", default=None)


def tool_name(tool) -> str:
    if hasattr(tool, "name"):
        return tool.name.lower()
    return tool.__name__.lower()


TIMEZONE = ZoneInfo("Australia/Sydney")


def get_datetime(_):
    return datetime.now(TIMEZONE).strftime("%A %d %B, %I:%M%p")


class Chat:
    def __init__(self, llm, system_prompt_template, knowledge_base_tool):
        self.llm = llm
        self.system_prompt_template = system_prompt_template
        self.knowledge_base_tool = knowledge_base_tool
        self.tools = [self.knowledge_base_tool, ResponseFormatter]
        self.tools_by_name = {tool_name(t): t for t in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools, strict=True)
        self.llm_without_tools = self.llm.bind_tools([ResponseFormatter], strict=True)

    async def invoke(
        self, messages: list[BaseMessage]
    ) -> AsyncGenerator[ResponseFormatter, None]:
        try:
            prompt = self.system_prompt_template.replace(
                "{current_datetime}", get_datetime(None)
            )
            messages = [SystemMessage(prompt)] + messages

            MAX_TOOL_CALLS = 3
            for i in range(MAX_TOOL_CALLS):
                llm = (
                    self.llm_with_tools
                    if i < (MAX_TOOL_CALLS - 1)
                    else self.llm_without_tools
                )
                response = await llm.ainvoke(messages)
                log.info(response)
                messages.append(response)
                reflect = False

                if response.content:
                    yield ResponseFormatter(answer=str(response.content))

                for tool_call in response.tool_calls:
                    log.info(f"Calling tool: {tool_call}")
                    args = tool_call["args"]
                    try:
                        tool_instance = self.tools_by_name[tool_call["name"].lower()]
                    except KeyError:
                        # Infer tool name because DeepSeek just leaves it out sometimes
                        if "query" in args and "answer" not in args:
                            tool_instance = self.knowledge_base_tool
                        elif "answer" in args:
                            tool_instance = ResponseFormatter
                        else:
                            raise ValueError(
                                f"tool_call does not match a tool: {tool_call}"
                            )
                    is_pydantic = False
                    try:
                        is_pydantic = issubclass(tool_instance, BaseModel)
                    except TypeError:
                        pass
                    if is_pydantic:
                        tool_result = tool_instance(**args)
                        yield tool_result
                    else:
                        if "query" in args:
                            query = args["query"]
                            yield ResponseFormatter(
                                answer=f'🔍 *Searching for "{query}"...*'
                            )
                        tool_result = await tool_instance.ainvoke(tool_call)
                        reflect = True
                    messages.append(tool_result)

                if not reflect:
                    break

        except Exception as e:
            log.error(f"Error during invoke: {e}", exc_info=True)
            yield ResponseFormatter(answer="⚠️ " + str(e))


def create_chat_instance():
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "slurp")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX")

    embeddings = PineconeEmbeddings(
        model="llama-text-embed-v2",
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
            namespace=os.getenv("PINECONE_NAMESPACE", "slurp"),
        )

        documents = []
        for match in raw_results.matches:
            if match.metadata and "text" in match.metadata:
                doc = match.metadata
                documents.append(doc)

        log.info(f"Retriever found {len(documents)} documents")
        return documents

    MODEL_CLAUDE_SONNET_4 = "anthropic/claude-sonnet-4"
    MODEL_DEEPSEEK_3_1 = "deepseek/deepseek-chat-v3.1"
    MODEL_KIMI_K2 = "moonshotai/kimi-k2-0905"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    base_llm = ChatOpenAI(
        model=MODEL_DEEPSEEK_3_1,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        streaming=False,
    )

    system_prompt_template = """
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

The current date and time is {current_datetime}.
When searching the knowledge base, convert implicit dates or ranges of dates into explicit months and
dates. For example:
- "What's on tomorrow?" -> "events February 16"
- "Tell me what's coming up this week" -> "events May 7 8 9 10 11"
- "When is the next assembly?" -> "school assembly July August"
"""

    chat = Chat(
        llm=base_llm,
        system_prompt_template=system_prompt_template,
        knowledge_base_tool=knowledge_base_search,
    )

    return chat


if __name__ == "__main__":
    chat = create_chat_instance()
    messages = [HumanMessage("What is the date of the 2025 athletics carnival?")]

    async def main():
        async for response in chat.invoke(messages):
            log.info(response)

    asyncio.run(main())
