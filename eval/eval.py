import asyncio
import os
import sys
from langchain_core.messages import HumanMessage
import dotenv

dotenv.load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingest.kb import upload_to_pinecone
from src.chat import Chat, create_knowledge_base_tool
from eval.config import TEST_CASES
from eval.questions import QUESTIONS
from eval.canonical_answers import CANONICAL_ANSWERS


async def main():
    test_data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../ingest/testdata")
    )
    for test_case in TEST_CASES:
        print(f"Running test case: {test_case['name']}")

        # 1. Ingest data
        for filename in os.listdir(test_data_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(test_data_dir, filename)
                with open(file_path, "r") as f:
                    content = f.read()
                print(f"  Ingesting {filename}...")
                upload_to_pinecone(
                    filename=filename,
                    md=content,
                    embedding_model=test_case["embedding_model"],
                    chunking_function=test_case["chunking_function"],
                )

        # 2. Ask questions
        chat = Chat(
            llm=test_case["llm"],
            system_prompt_template=(
                """
            You are a helpful AI chatbot. Your name is Slurp. You answer parents' questions about correspondence
            with their children's school.
            """
                if test_case["prompt_template"] == "default"
                else test_case["prompt_template"]
            ),
            knowledge_base_tool=create_knowledge_base_tool(
                test_case["embedding_model"]
            ),
        )

        results = []
        for question in QUESTIONS:
            print(f"  Asking: {question['question']}")
            messages = [HumanMessage(question["question"])]
            answer = ""
            async for response in chat.invoke(messages):
                answer += response.answer

            results.append({"question": question["question"], "answer": answer})
            print(f"    Answer: {answer}")


if __name__ == "__main__":
    asyncio.run(main())
