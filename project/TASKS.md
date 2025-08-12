# Project Tasks

## 🍇 Grape - Ready to eat!
- Research Pinecone free tier and LangChain integration for vector store migration.

## 🍌 Banana - Needs peeling first
- Automate knowledge base sync: Implement a mechanism to sync new emails/text from S3 to the Bedrock Knowledge Base, potentially with debouncing.
- Experiment with different chunking strategies for the knowledge base to optimize RAG performance.
- Define useful metadata for the vector DB, including a semi-structured approach for storing events with dates.
- Implement other vector DB tweaks: deduping, result diversity, and recency weighting.
- Implement daily or weekly reminders from the Discord bot based on extracted event data.
- Develop a more robust approach to determine which email links to follow for content extraction.
- Break the ingestion process into stages that can be retried or replayed for improved robustness.

## 🥥 Coconut - Hard to crack
- **Multi-user Support:**
    - Design and implement a user database to store notification settings, prompt customization, and other per-user settings.
    - Integrate an authentication system (e.g., Keycloak) for user management.
    - Implement label-based access control using vector database metadata to ensure users only access their own data.
- Deduplicate common inputs (e.g., newsletters sent to multiple children) to save processing time and costs, and manage shared access.
- Develop an evaluation framework to systematically assess changes to the summary and RAG pipelines.
- Implement guardrails to prevent misuse or usage outside the intended school correspondence use case.
- Infrastructure improvements: Transition to Infrastructure-as-Code (IaC), set up Continuous Integration/Continuous Deployment (CI/CD) pipelines, and enhance observability.

## 🌱 Seedling - Not ready to harvest
- Explore and implement other interaction surfaces beyond email and Discord, such as a web application, native mobile application, Calendar integration, or browser extension.