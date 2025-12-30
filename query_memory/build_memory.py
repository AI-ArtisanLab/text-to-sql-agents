import json
import chromadb
import os
from dotenv import load_dotenv
import requests

load_dotenv()

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="query_memory/chroma_store"
    )
)

collection = client.get_or_create_collection(
    name="query_memory"
)

def embed(text: str):
    try:
        resp = requests.post(
            f"{OLLAMA_ENDPOINT}/api/embeddings",
            json={"model": OLLAMA_MODEL, "prompt": text}
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as e:
        print(f"Error: Ollama embedding failed ({str(e)})")
        print(f"Make sure Ollama is running: ollama serve")
        print(f"And pull the model: ollama pull {OLLAMA_MODEL}")
        raise

with open("query_memory/seed_questions.json") as f:
    examples = json.load(f)

for idx, item in enumerate(examples):
    collection.add(
        ids=[f"seed_{idx}"],
        documents=[item["question"]],
        embeddings=[embed(item["question"])],
        metadatas=[{"sql": item["sql"]}]
    )

print(f"Seeded {len(examples)} queries into Query Memory")
