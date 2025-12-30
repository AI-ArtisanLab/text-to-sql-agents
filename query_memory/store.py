"""
Query Memory Store with Semantic Search
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"

Supports embeddings from both Ollama and OpenAI providers
"""

import chromadb
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Embedding provider configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()  # "ollama" or "openai"

# Ollama configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

try:
    client = chromadb.Client(
        chromadb.config.Settings(
            persist_directory="query_memory/chroma_store"
        )
    )
    collection = client.get_or_create_collection("query_memory")
    QUERY_MEMORY_ENABLED = True
except Exception as e:
    print(f"Warning: Query Memory disabled ({str(e)})")
    QUERY_MEMORY_ENABLED = False

def embed_with_ollama(text: str):
    """Generate embeddings using Ollama"""
    try:
        resp = requests.post(
            f"{OLLAMA_ENDPOINT}/api/embeddings",
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text}
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as e:
        print(f"Warning: Ollama embedding failed ({str(e)}). Make sure Ollama is running on {OLLAMA_ENDPOINT}")
        return None

def embed_with_openai(text: str):
    """Generate embeddings using OpenAI"""
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
            }
        )
        resp.raise_for_status()
        result = resp.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"Warning: OpenAI embedding failed ({str(e)}). Check your API key and internet connection.")
        return None

def embed(text: str):
    if not QUERY_MEMORY_ENABLED:
        return None
    
    if EMBEDDING_PROVIDER == "openai":
        return embed_with_openai(text)
    else:
        return embed_with_ollama(text)

def retrieve(question: str, threshold: float = 0.8) -> str:
    if not QUERY_MEMORY_ENABLED:
        return ""
    try:
        emb = embed(question)
        if emb is None:
            return ""
        result = collection.query(
            embeddings=[emb],
            n_results=1
        )

        if not result["distances"]:
            return ""

        similarity = 1 - result["distances"][0][0]
        if similarity >= threshold:
            return result["metadatas"][0][0]["sql"]
    except Exception:
        pass
    return ""

def add(question: str, sql: str):
    if not QUERY_MEMORY_ENABLED:
        return
    try:
        emb = embed(question)
        if emb is not None:
            collection.add(
                documents=[question],
                embeddings=[emb],
                metadatas=[{"sql": sql}]
            )
    except Exception as e:
        print(f"Warning: Could not add to Query Memory ({str(e)})")
