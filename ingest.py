"""Ingesta idempotente: colecciones identificadas por contenido y configuración."""
import hashlib
import json

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Settings


def load_documents(settings: Settings) -> list[Document]:
    docs = []
    for path in sorted(settings.data_dir.rglob('*')):
        if path.is_file() and path.suffix.lower() in {'.md', '.txt'}:
            text = path.read_text(encoding='utf-8').strip()
            if text:
                docs.append(Document(page_content=text, metadata={
                    'source': path.relative_to(settings.data_dir).as_posix()}))
    if not docs:
        raise ValueError(f'No hay documentos .txt/.md con contenido en {settings.data_dir}')
    return docs


def index_spec(settings: Settings, docs: list[Document]) -> dict:
    return {
        'schema': 2, 'provider': 'openai', 'embedding_model': settings.embedding_model,
        'base_url': settings.base_url, 'encoding': 'cl100k_base',
        'chunk_size': settings.chunk_size, 'chunk_overlap': settings.chunk_overlap,
        'documents': [{'source': d.metadata['source'],
                       'sha256': hashlib.sha256(d.page_content.encode()).hexdigest()}
                      for d in docs],
    }


def ingest(settings: Settings | None = None, *, embeddings=None) -> dict:
    settings = settings or Settings()
    docs = load_documents(settings)
    spec = index_spec(settings, docs)
    fingerprint = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    collection = f'rag_{fingerprint[:32]}'
    settings.persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.persist_dir))
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name='cl100k_base', chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    ids = [hashlib.sha256(f'{fingerprint}:{i}'.encode()).hexdigest()
           for i in range(len(chunks))]
    for chunk, chunk_id in zip(chunks, ids):
        chunk.metadata['chunk_id'] = chunk_id
    store = Chroma(client=client, collection_name=collection,
                   embedding_function=embeddings if embeddings is not None else settings.embeddings())
    existing = set(store.get()['ids'])
    missing = [(chunk, key) for chunk, key in zip(chunks, ids) if key not in existing]
    # Upsert por IDs deterministas: una ejecución interrumpida se puede retomar.
    for start in range(0, len(missing), 64):
        batch = missing[start:start + 64]
        store.add_documents([c for c, _ in batch], ids=[key for _, key in batch])
    manifest = {'collection': collection, 'fingerprint': fingerprint,
                'spec': spec, 'chunks': len(chunks)}
    target = settings.persist_dir / 'manifest.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)  # Publicar únicamente luego de completar la colección.
    return {**manifest, 'indexed': len(missing), 'reused': len(chunks) - len(missing)}


def open_store(settings: Settings, *, embeddings=None) -> Chroma:
    target = settings.persist_dir / 'manifest.json'
    if not target.exists():
        raise RuntimeError('No hay índice. Ejecutá primero: python ingest.py')
    manifest = json.loads(target.read_text(encoding='utf-8'))
    if manifest['spec'] != index_spec(settings, load_documents(settings)):
        raise RuntimeError('Cambió el corpus o la configuración. Ejecutá python ingest.py.')
    store = Chroma(collection_name=manifest['collection'],
                   persist_directory=str(settings.persist_dir),
                   embedding_function=embeddings if embeddings is not None else settings.embeddings(),
                   create_collection_if_not_exists=False)
    if len(store.get()['ids']) != manifest['chunks']:
        raise RuntimeError('Índice incompleto. Ejecutá python ingest.py para repararlo.')
    return store


if __name__ == '__main__':
    print(json.dumps(ingest(), ensure_ascii=False, indent=2))
