"""Dos pruebas reales. Requiere OPENAI_API_KEY y acceso a los modelos configurados."""
import asyncio
import json

from ingest import ingest
from rag import RAGService


async def main():
    ingest()
    service = RAGService()
    cases = [
        ('¿Durante cuántos días se conservan los respaldos de Aurora?', True),
        ('¿Quién ganó el Mundial de fútbol de 2022?', False),
    ]
    results = []
    for query, known in cases:
        response = await service.get_rag_response(query)
        passed = (response.texto != 'No lo sé' and bool(response.referencias)
                  and '30 días' in response.texto) if known else (
                      response.texto == 'No lo sé' and response.referencias == [])
        results.append({'query': query, 'passed': passed,
                        'response': response.model_dump()})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not all(r['passed'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
