"""Configuración compartida por ingesta y consulta; rutas relativas al proyecto."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(ROOT / '.cache' / 'tiktoken'))


@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / 'data'
    persist_dir: Path = ROOT / 'vectorstore'
    embedding_model: str = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    base_url: str = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    chat_model: str = os.getenv('CHAT_MODEL', 'gpt-4o-mini')
    top_k: int = int(os.getenv('TOP_K', '4'))
    chunk_size: int = 600
    chunk_overlap: int = 50

    def __post_init__(self):
        if not 3 <= self.top_k <= 5:
            raise ValueError('TOP_K debe estar entre 3 y 5.')

    def embeddings(self):
        return OpenAIEmbeddings(model=self.embedding_model, base_url=self.base_url,
                                request_timeout=60, max_retries=2)
