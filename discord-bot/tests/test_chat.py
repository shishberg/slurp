import pytest
from chat import Chat, tool_name, ResponseFormatter
from pydantic import BaseModel
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage


def test_tool_name():
    def my_tool():
        pass

    assert tool_name(my_tool) == "my_tool"


class MyPydanticTool(BaseModel):
    pass


def test_pydantic_tool_name():
    assert tool_name(MyPydanticTool) == "mypydantictool"


@pytest.mark.asyncio
async def test_invoke():
    # Create mock dependencies
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_knowledge_base_tool = AsyncMock()

    # Configure the mock LLM to return a response
    mock_response = AIMessage(content="Hello, world!", tool_calls=[])
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    # Instantiate the Chat class with mock dependencies
    chat_instance = Chat(
        llm=mock_llm,
        system_prompt_template="{current_datetime}",
        knowledge_base_tool=mock_knowledge_base_tool,
    )

    # Call the invoke method
    messages = [HumanMessage("Hello")]
    responses = [response async for response in chat_instance.invoke(messages)]

    # Assert the response
    assert len(responses) == 1
    assert isinstance(responses[0], ResponseFormatter)
    assert responses[0].answer == "Hello, world!"
