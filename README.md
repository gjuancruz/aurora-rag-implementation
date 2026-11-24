# RAG con ChromaDB local y OpenAI: Aurora

Flujo de ingesta → embeddings → ChromaDB persistente → recuperación top-k →
prompt → chat asíncrono → `PydanticOutputParser` → verificación de referencias.
Incluye tres manuales ficticios originales en español dentro de `data/`.

## Instalación

Requiere Python 3.11 o 3.12 y una API key de OpenAI con acceso a los modelos configurados.
Desde la carpeta de este proyecto, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Editar .env y completar OPENAI_API_KEY con tu clave de API
```

`requirements-lock.txt` registra las versiones instaladas y verificadas con Python
3.12 en Windows. Para reproducir ese entorno, usar `pip install -r requirements-lock.txt`
en lugar de `requirements.txt`.

El provider es OpenAI: `OpenAIEmbeddings` usa `text-embedding-3-small` y
`ChatOpenAI` usa `gpt-4o-mini` por defecto. Ambos se pueden cambiar en `.env`.
También se puede definir `OPENAI_API_KEY` como variable de entorno. No subir
la clave al repositorio: `.env` está excluido por `.gitignore`.

ChromaDB y los documentos se guardan localmente. La ingesta envía los textos
a OpenAI para obtener embeddings; las consultas envían la pregunta para su
embedding y los fragmentos recuperados para generar la respuesta. Las llamadas
requieren Internet y consumen saldo de la API. Las pruebas con dobles no hacen llamadas.

Si ya existía un índice generado con Ollama, ejecutar otra vez `ingest.py`.
La configuración del provider y del modelo forman parte del identificador de
la colección, por lo que los vectores anteriores no se mezclan con los nuevos.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe ingest.py
.\.venv\Scripts\python.exe ingest.py  # indexed: 0; reutiliza el índice
.\.venv\Scripts\python.exe rag.py "¿Durante cuántos días se conservan los respaldos de Aurora?"
.\.venv\Scripts\python.exe rag.py "¿Quién ganó el Mundial de fútbol de 2022?"
.\.venv\Scripts\python.exe evaluate.py
```

`evaluate.py` ejecuta las dos preguntas contra los modelos reales y termina con
código 1 si alguna falla. La respuesta conocida debe incluir `30 días` y referencias;
la pregunta trampa debe devolver exactamente `No lo sé` y una lista vacía.
No se necesita que la pregunta ausente tenga baja similitud: aun recuperando manuales,
el modelo debe abstenerse porque esos textos no contienen la respuesta.

Uso desde Python:

```python
import asyncio
from rag import get_rag_response

response = asyncio.run(get_rag_response("¿Durante cuántos días se conservan los respaldos?"))
print(response.model_dump_json(indent=2))
```

En un notebook con loop activo, usar `await get_rag_response(...)`. Para varias
consultas, instanciar `RAGService` una vez y reutilizar su método asíncrono.

Salida de ejemplo esperada (el ID real depende del corpus):

```json
{
  "texto": "Los respaldos se conservan durante 30 días.",
  "referencias": [{
    "chunk_id": "<sha256 del fragmento>",
    "fuente": "02_respaldos.md",
    "cita": "Los respaldos se conservan durante 30 días."
  }]
}
```

## Decisiones de implementación

- `RecursiveCharacterTextSplitter` cuenta tokens con `cl100k_base`: tamaño objetivo
  de **600 tokens** y overlap configurado de **50 tokens**. El tamaño es un máximo,
  no un mínimo obligatorio por fragmento: los finales y las divisiones naturales
  pueden ser más cortos. El overlap efectivo depende de los separadores recursivos.
  El tokenizador del modelo puede diferir; se limita el contexto a 3–5 fragmentos.
- `TOP_K=4` por defecto, validado entre 3 y 5. Con pocos documentos puede recuperar
  menos. No se utiliza un umbral de distancia arbitrario como prueba de veracidad.
- Ingesta y consultas comparten `Settings.embeddings()`. Un manifiesto registra
  modelo, endpoint, tokenizador, chunking y hashes de documentos. Si cambian,
  la consulta pide ejecutar la ingesta. La identidad del modelo se controla por
  nombre y endpoint; si se reemplazan los pesos bajo el mismo nombre, hay que usar
  otro nombre de modelo y volver a ingerir.
- Cada versión del corpus tiene su propia colección. IDs deterministas permiten
  reutilizar embeddings y retomar cargas interrumpidas sin duplicar fragmentos.
  El manifiesto se publica al terminar. Versiones anteriores quedan en disco,
  pero no se consultan. Ejecutar una sola ingesta a la vez; no hay bloqueo de escritores.
- La cadena LCEL usa recuperación asíncrona, `RunnablePassthrough.assign`, prompt,
  `ChatOpenAI`, `PydanticOutputParser` y un verificador. Cada consulta conserva su
  contexto por separado, incluso cuando hay varias consultas concurrentes.
- La respuesta es **extractiva**: el LLM selecciona citas; el texto final debe ser
  exactamente esas citas. Se verifican ID, fuente y presencia literal en el fragmento.
  JSON inválido, texto añadido o citas inventadas producen `No lo sé`.
  Esto restringe el contenido al corpus, pero no garantiza que una cita sea pertinente
  a cualquier pregunta. La selección y la abstención semántica siguen dependiendo
  del modelo. El corpus también puede contener errores. Las pruebas no constituyen
  una garantía universal contra alucinaciones o instrucciones maliciosas.
- Errores de conexión o del índice se propagan: no se presentan como si fueran
  ausencia de información. El README es toda la documentación del proyecto.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Las pruebas automáticas usan Chroma persistente y LCEL reales con dobles explícitos
de embeddings y chat para poder correr sin API key ni llamadas a OpenAI. Cubren la pregunta conocida,
la pregunta trampa, concurrencia, persistencia sin recalcular embeddings, cambios
de configuración/corpus, límites de tokens y rechazo de respuestas inválidas.
No evalúan la calidad de embeddings ni la abstención de un modelo real.
`evaluate.py` es la evaluación end-to-end con el provider seleccionado.

La evaluación con modelos reales requiere una `OPENAI_API_KEY` válida. Ejecutar
`evaluate.py` después de configurarla. Los ejemplos anteriores son resultados
esperados, no una transcripción de una generación real de OpenAI.

Verificación ejecutada: **9 pruebas automáticas aprobadas** y `pip check` sin
incompatibilidades. En el entorno restringido de Codex, las pruebas asíncronas se
ejecutaron fuera del sandbox porque el loop de Windows requiere sockets locales.

## Referencias técnicas

- [Chroma en LangChain](https://reference.langchain.com/python/langchain-chroma/vectorstores/Chroma)
- [Integración OpenAI](https://reference.langchain.com/python/langchain-openai)
- [Embeddings de OpenAI](https://developers.openai.com/api/docs/guides/embeddings)
- [PydanticOutputParser](https://reference.langchain.com/python/langchain-core/output_parsers/pydantic/PydanticOutputParser)
