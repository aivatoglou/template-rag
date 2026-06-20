from dataclasses import dataclass

@dataclass
class DocChunk:
    content: str
    embedding: list[float]
    source: str
    source_url: str
    title: str


@dataclass
class SearchResult:
    content: str
    source: str
    source_url: str
    title: str
    score: float
