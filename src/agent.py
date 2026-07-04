"""Assistant agent with two RAG tools."""

import os

from agno.agent import Agent
from openai import AzureOpenAI, OpenAI
from agno.models.azure import AzureOpenAI as AgnoAzureOpenAI
from agno.models.openrouter import OpenRouter

from src.db.store import hybrid_search
from src.models import AgentResponse

_USE_OPENROUTER = os.environ.get("LLM_PROVIDER", "azure").lower() == "openrouter"

if _USE_OPENROUTER:
    _embed_client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    _embed_deployment = os.environ.get("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-large")
else:
    _embed_client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )
    _embed_deployment = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")


def _embed(query: str) -> list[float]:
    return _embed_client.embeddings.create(model=_embed_deployment, input=[query]).data[0].embedding


def search_ars_technica(query: str) -> str:
    """
    Search Ars Technica articles.
    Use for questions about technology, science, computing, gadgets, space,
    and in-depth tech industry coverage.
    """
    return hybrid_search(_embed(query), query, source="ars", k=5)


def search_bbc_news(query: str) -> str:
    """
    Search BBC world news articles.
    Use for questions about current events, politics, world affairs,
    business, and general breaking news.
    """
    return hybrid_search(_embed(query), query, source="bbc", k=5)


SYSTEM_MESSAGE = """You are a helpful news assistant.
You have two tools: one for Ars Technica (technology and science) and one for BBC (world news).

Rules:
- Always call the relevant tool before answering. Never answer from memory.
- If the tools return nothing relevant, say so — never fabricate facts.
- Be concise. Use bullet points for lists.
- Respond in the same language as the user's question.
- Always reply in English.

Response format (strictly JSON):
- "answer": your response to the user
- "sources": list of source URLs used (empty list if no tools were called)
"""


def _build_model():
    if _USE_OPENROUTER:
        return OpenRouter(id=os.environ.get("OPENROUTER_MODEL", "gpt-5.4-mini"))
    return AgnoAzureOpenAI(
        id=os.environ.get("AZURE_GPT_DEPLOYMENT", "gpt-4.1"),
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )


def build_agent() -> Agent:
    return Agent(
        model=_build_model(),
        tools=[search_ars_technica, search_bbc_news],
        system_message=SYSTEM_MESSAGE,
        markdown=True,
        output_schema=AgentResponse,
    )
