import json
import chromadb
import os
from dotenv import load_dotenv
import requests

import urllib3
#Disable insecure request warnings for OpenAI calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()  # "ollama" or "openai"

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="query_memory/chroma_store"
    )
)

collection = client.get_or_create_collection(
    name="query_memory"
)

def embed_with_ollama(text: str):
    try:
        resp = requests.post(
            f"{OLLAMA_ENDPOINT}/api/embeddings",
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as e:
        print(f"Error: Ollama embedding failed ({str(e)})")
        print(f"Make sure Ollama is running: ollama serve")
        print(f"And pull the model: ollama pull {OLLAMA_EMBEDDING_MODEL}")
        raise

def embed_with_openai(text: str):
    try:
        resp = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_EMBEDDING_MODEL,
                "input": text
            },
            verify=False
        )
        resp.raise_for_status()
        res =  resp.json()
        return res["data"][0]["embedding"]
    except Exception as e:
        print(f"Error: OpenAI embedding failed ({str(e)})")
        print(f"Make sure your OpenAI API key is correct and has access to the model {OPENAI_EMBEDDING_MODEL}")
        raise

def embed(text: str):
    if EMBEDDING_PROVIDER == "openai":
        return embed_with_openai(text)
    else:
        return embed_with_ollama(text)
    
print(f"Building Query Memory with {EMBEDDING_PROVIDER} embeddings...")
if EMBEDDING_PROVIDER == "openai":
    print(f"Using OpenAI Embedding Model: {OPENAI_EMBEDDING_MODEL}")
else:
    print(f"Using Ollama Embedding Model: {OLLAMA_EMBEDDING_MODEL} at {OLLAMA_ENDPOINT}")

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
