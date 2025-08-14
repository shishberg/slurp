from common import logger
from cache import DiskCache

from langchain_aws import ChatBedrock
from ratelimit import limits
import dotenv

dotenv.load_dotenv()

log = logger(__name__)

MODEL_CLAUDE_4_SONNET = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatBedrock(
    provider="anthropic",
    model_id=MODEL_CLAUDE_4_SONNET,
    model_kwargs={},
    streaming=False,
)

PROMPT = """
You are an assistant to a parent reading a message from their children's school.
Provide a bullet point summary of the message, emphasising anything directly
relevant to the parent and their children.

The parent's children are:
- Rosemary (Rosie) in year 4 in the Grasshoppers class
- Toby in year 6 in the Bats class

Don't mention the children's names in the summary unless the point being summarized
in the message mentions them by name.

Respond in Markdown in the following format:
## [Subject/Title] Summary
_[Date]_

### For You
- [Directly relevant point for parent]
- [...]

### Events
- **[Date]**: [Event description]
- ...

### [Other sections as needed]
- ...
"""

_cache = DiskCache(cache_dir=".cache/llm_summaries")


# Rate-limited wrapper for the actual LLM invocation
@limits(calls=10, period=60 * 60 * 24)
def _invoke_llm(messages):
    """Rate-limited wrapper for LLM invocation."""
    output = llm.invoke(messages)
    return output.text()


def summarise(text):
    """Summarise text with caching and rate limiting only for fresh calls."""
    text_bytes = text.encode("utf-8")

    def fetch_summary():
        """Compute the summary on cache miss."""
        messages = [
            SystemMessage(PROMPT),
            HumanMessage(text),
        ]
        return _invoke_llm(messages).encode("utf-8")

    # Get cached result or compute and cache new result
    result = _cache.get(text_bytes, fetch_summary)
    return result.decode("utf-8")
