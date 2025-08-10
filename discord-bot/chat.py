from langchain_aws import ChatBedrock
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain.chains import RetrievalQA
import asyncio
import logging
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

MODEL_NOVA_PRO = "amazon.nova-pro-v1:0"
MODEL_CLAUDE_SONNET_4 = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
REGION = "ap-southeast-2"

llm = ChatBedrock(
    model_id=MODEL_CLAUDE_SONNET_4,
    model_kwargs={},
    streaming=True,
    region_name=REGION,
)

kb = AmazonKnowledgeBasesRetriever(
    knowledge_base_id="ROWFWHJMAF",
    region_name=REGION,
    retrieval_config={
        "vectorSearchConfiguration": {
            "numberOfResults": 4,
        },
    },
)


def get_datetime(_):
    return datetime.now().strftime("%A %d %B, %I:%M%p")


async def invoke(msg, context_messages=None):
    try:
        template = """
You are a helpful AI chatbot. Your name is Slurp. You answer parents' questions about correspondence
with their children's school. If there's something specifically relevant to the parent's children or
their class then draw attention to that, but only if it's specific. Don't mention the children at all
if the information is general to the school or relevant to all the children.

Answer as succinctly as possible. Every word in the answer should be necessary to convey information.

The user has two children:
    * Toby McLeish, in the Bats class in year 6
    * Rosemary (Rosie) McLeish, in the Grasshoppers class in year 4

{conversation_history}
Answer the question using the following documents:
{context}

Current date and time: {current_datetime}

Question: {question}

Provide your response in this exact format:

<answer>
[Your full answer here]
</answer>

<title>
[3-5 word title summarizing the question or answer]
</title>

Examples of good titles:
- "Athletics Carnival Date"
- "Math Homework Policy"
- "School Uniform Change"
"""

        prompt = ChatPromptTemplate.from_template(template)

        # Format conversation history
        conversation_history = (
            "Previous conversation history:\n" + "\n".join(context_messages) + "\n\n"
            if context_messages
            else ""
        )

        chain = (
            RunnableParallel(
                {
                    "context": kb,
                    "question": RunnablePassthrough(),
                    "current_datetime": RunnableLambda(get_datetime),
                    "conversation_history": RunnableLambda(
                        lambda _: conversation_history
                    ),
                }
            )
            .assign(response=prompt | llm | StrOutputParser())
            .pick(["response", "context"])
            .with_retry(stop_after_attempt=3)  # Added retry for parsing failures
        )

        for i in range(3):
            try:
                response = await chain.ainvoke(msg)
                break
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]
                if (
                    error_code == "ValidationException"
                    and "auto-paused" in error_message
                    and i < 3
                ):
                    wait_time = 2 ** (i + 1)
                    logger.info(
                        "Knowledge base is resuming. Retrying in %s seconds...",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

        # Parse the response to extract both answer and title
        full_response = response["response"]

        try:
            # Extract answer from XML tags
            answer_start = full_response.find("<answer>") + len("<answer>")
            answer_end = full_response.find("</answer>")
            answer = full_response[answer_start:answer_end].strip()

            # Extract title from XML tags
            title_start = full_response.find("<title>") + len("<title>")
            title_end = full_response.find("</title>")
            title = full_response[title_start:title_end].strip()
        except Exception:
            # Fallback if parsing fails
            logger.warning("Failed to parse XML output, using fallback title")
            answer = full_response
            # Generate title from first 5 words
            words = full_response.split()[:5]
            title = " ".join(words)

        return {"answer": answer, "title": title}

    except Exception as e:
        logger.exception("Error during chat invocation")
        return str(e)


if __name__ == "__main__":
    logger.info(asyncio.run(invoke("What is the date of the 2025 athletics carnival?")))
