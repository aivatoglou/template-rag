"""Assistant agent with two RAG tools."""

import os

from agno.agent import Agent
from openai import AzureOpenAI
from agno.models.azure import AzureOpenAI as AgnoAzureOpenAI

from src.db.store import hybrid_search
from src.models import AgentResponse

_embed_client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
_embed_deployment = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")


def _embed(query: str) -> list[float]:
    return _embed_client.embeddings.create(model=_embed_deployment, input=[query]).data[0].embedding


def search_kpn_news(query: str) -> str:
    """
    Search KPN news articles and press releases.
    Use for questions about recent KPN events, network updates, product launches,
    company news, or partnerships.
    """
    return hybrid_search(_embed(query), query, source="news", k=5)


def search_kpn_vacancies(query: str) -> str:
    """
    Search KPN's current job openings.
    Use for questions about available positions, required skills, salaries,
    work locations, or career opportunities at KPN.
    """
    return hybrid_search(_embed(query), query, source="vacancies", k=5)


SYSTEM_MESSAGE = """You are a helpful assistant for KPN customers and job seekers.
You have two tools: one for KPN news and one for KPN job vacancies.

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


def build_agent() -> Agent:
    return Agent(
        model=AgnoAzureOpenAI(
            id=os.environ.get("AZURE_GPT_DEPLOYMENT", "gpt-4.1"),
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        ),
        tools=[search_kpn_news, search_kpn_vacancies],
        system_message=SYSTEM_MESSAGE,
        markdown=True,
        output_schema=AgentResponse,
    )
