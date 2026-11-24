"""Chroma y LCEL reales; dobles explícitos solo para embeddings y chat."""
import asyncio
import hashlib
import json
from dataclasses import replace

import pytest
import tiktoken
from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableLambda

from config import Settings
from ingest import ingest, open_store
from rag import RAGService


class OfflineEmbeddings(Embeddings):
    """Vectorización determinista de prueba; no mide calidad semántica."""
    calls = 0

    def embed_documents(self, texts):
        self.calls += len(texts)
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text):
        digest = hashlib.sha256(text.encode()).digest()
        return [(b - 127.5) / 128 for b in digest]


@pytest.fixture
def indexed(tmp_path):
    settings = Settings(persist_dir=tmp_path / 'db', top_k=5)
    embeddings = OfflineEmbeddings()
    report = ingest(settings, embeddings=embeddings)
    return settings, embeddings, report


def model_response(prompt):
    """Doble de chat: usa el contexto de la invocación, no respuestas del LLM real."""
    human = prompt.to_messages()[-1].content
    context_text, question = human.split('\n\nPREGUNTA:\n')
    context = json.loads(context_text.split('CONTEXTO (JSON):\n')[1])
    if 'Mundial' in question:
        return json.dumps({'texto': 'No lo sé', 'referencias': []})
    quote = 'Los respaldos se conservan durante 30 días.'
    doc = next(d for d in context if quote in d['contenido'])
    return json.dumps({'texto': quote, 'referencias': [
        {'chunk_id': doc['chunk_id'], 'fuente': doc['fuente'], 'cita': quote}]})


def test_known_question_and_trap(indexed):
    settings, embeddings, _ = indexed
    service = RAGService(settings, store=open_store(settings, embeddings=embeddings),
                         llm=RunnableLambda(model_response))

    async def run():
        known, trap = await asyncio.gather(
            service.get_rag_response('¿Cuántos días se conservan los respaldos?'),
            service.get_rag_response('¿Quién ganó el Mundial de 2022?'))
        assert known.texto == 'Los respaldos se conservan durante 30 días.'
        assert known.referencias[0].fuente == '02_respaldos.md'
        assert trap.texto == 'No lo sé' and trap.referencias == []
    asyncio.run(run())


def test_persistence_idempotence_and_token_chunks(indexed):
    settings, embeddings, first = indexed
    previous = embeddings.calls
    second = ingest(settings, embeddings=embeddings)
    assert second['indexed'] == 0
    assert second['reused'] == first['chunks']
    assert embeddings.calls == previous
    store = open_store(settings, embeddings=embeddings)
    chunks = store.get()['documents']
    encoder = tiktoken.get_encoding('cl100k_base')
    assert all(len(encoder.encode(c)) <= 600 for c in chunks)
    assert len(chunks) >= 3


def test_reject_changed_embedding_and_changed_corpus(indexed, tmp_path):
    settings, embeddings, _ = indexed
    with pytest.raises(RuntimeError, match='Cambió'):
        open_store(replace(settings, embedding_model='otro'), embeddings=embeddings)
    data = tmp_path / 'data'
    data.mkdir()
    (data / 'nuevo.md').write_text('Nuevo corpus', encoding='utf-8')
    with pytest.raises(RuntimeError, match='Cambió'):
        open_store(replace(settings, data_dir=data), embeddings=embeddings)


@pytest.mark.parametrize('response', [
    '{no es JSON',
    json.dumps({'texto': 'Inventado', 'referencias': [
        {'chunk_id': 'falso', 'fuente': 'inventado.md', 'cita': 'Inventado'}]}),
    json.dumps({'texto': 'Respuesta inventada', 'referencias': []}),
])
def test_invalid_output_fails_closed(indexed, response):
    settings, embeddings, _ = indexed
    service = RAGService(settings, store=open_store(settings, embeddings=embeddings),
                         llm=RunnableLambda(lambda _: response))
    result = asyncio.run(service.get_rag_response('¿Cuál es la retención?'))
    assert result.texto == 'No lo sé' and result.referencias == []


def test_reject_fabricated_quote_with_real_id(indexed):
    settings, embeddings, _ = indexed

    def fake_quote(prompt):
        data = json.loads(model_response(prompt))
        data['texto'] = data['referencias'][0]['cita'] = 'Se conservan durante 900 días.'
        return json.dumps(data)

    service = RAGService(settings, store=open_store(settings, embeddings=embeddings),
                         llm=RunnableLambda(fake_quote))
    result = asyncio.run(service.get_rag_response('¿Cuántos días?'))
    assert result.texto == 'No lo sé'


def test_empty_dataset(tmp_path):
    with pytest.raises(ValueError, match='No hay documentos'):
        ingest(Settings(data_dir=tmp_path, persist_dir=tmp_path / 'db'),
               embeddings=OfflineEmbeddings())


def test_openai_provider_configuration(monkeypatch):
    from langchain_openai import OpenAIEmbeddings

    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-not-a-real-key')
    settings = Settings(embedding_model='text-embedding-3-small',
                        chat_model='gpt-4o-mini', base_url='https://api.openai.com/v1')
    embeddings = settings.embeddings()
    assert isinstance(embeddings, OpenAIEmbeddings)
    assert embeddings.model == 'text-embedding-3-small'
    service = RAGService(settings, store=object())
    assert service.llm.bound.model_name == 'gpt-4o-mini'
    assert service.llm.kwargs['response_format'] == {'type': 'json_object'}
