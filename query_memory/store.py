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

import urllib3
#Disable insecure request warnings for OpenAI calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import hashlib
from datetime import datetime

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
            },
            verify=False
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
        try:
            result = collection.query(
                embeddings=[emb],
                n_results=1
            )
        except TypeError:
            # Fallback for older chromadb versions
            result = collection.query(
                query_embeddings=[emb],
                n_results=1
            )
        if not result["distances"] or not result["distances"][0]:
            return ""

        similarity = 1 - result["distances"][0][0]
        if similarity >= threshold:
            similar_question = result["documents"][0][0] if result["documents"] else "N/A"
            retrieved_sql = result["metadatas"][0][0]["sql"]
            print(f" Found similar query in memory (similarity: {similarity:.2f}): '{similar_question}'")
            return retrieved_sql
        else:
            print(f" No similar query found in memory (highest similarity: {similarity:.2f}, threshold: {threshold})")
    except Exception as e:
        print(f"  Query Memory retrieval failed ({str(e)})")
    return ""

def add(question: str, sql: str):
    if not QUERY_MEMORY_ENABLED:
        return
    try:
        emb = embed(question)
        if emb is not None:
            print(" Could not generate embedding, skipping addition to Query Memory.")
            return
        
        #Generate unique ID using hash of question and current timestamp
        question_hash = hashlib.md5(question.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = f"qmem_{question_hash}_{timestamp}"

        collection.add(
            ids=[unique_id],
            documents=[question],
            embeddings=[emb],
            metadatas=[{"sql": sql}]
        )
        print(" Added new query to Query Memory (ID: {unique_id}).")
    except Exception as e:
        print(f"Warning: Could not add to Query Memory ({str(e)})")
