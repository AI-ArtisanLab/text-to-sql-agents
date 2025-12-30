"""
LLM Provider Abstraction Layer
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"

Supports multiple LLM providers: Ollama (local), OpenAI (cloud), and Together.ai
"""

import os
from dotenv import load_dotenv
import requests
from utils.logging import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger()

# Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama", "openai", or "together"

# Ollama configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "mistral")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4-turbo")

# Together.ai configuration (legacy)
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_MODEL = os.getenv("TOGETHER_MODEL", "gpt-oss/gpt-oss-120b")

def call_llm(system_prompt, user_prompt, temperature=0.0):
    """Call LLM via provider (Ollama, OpenAI, or Together.ai)"""
    if LLM_PROVIDER == "openai":
        return call_openai_llm(system_prompt, user_prompt, temperature)
    elif LLM_PROVIDER == "together":
        return call_together_llm(system_prompt, user_prompt, temperature)
    else:
        return call_ollama_llm(system_prompt, user_prompt, temperature)

def call_ollama_llm(system_prompt, user_prompt, temperature=0.0):
    """Call local Ollama LLM"""
    try:
        resp = requests.post(
            f"{OLLAMA_ENDPOINT}/api/chat",
            json={
                "model": OLLAMA_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "stream": False
            }
        )
        resp.raise_for_status()
        result = resp.json()
        return result["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Ollama LLM call failed: {str(e)}")
        raise

def call_together_llm(system_prompt, user_prompt, temperature=0.0):
    """Call Together.ai cloud LLM (GPT-OSS 120B)"""
    try:
        resp = requests.post(
            "https://api.together.xyz/inference",
            headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
            json={
                "model": TOGETHER_MODEL,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "max_tokens": 4096,
                "temperature": temperature,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1.0
            }
        )
        resp.raise_for_status()
        result = resp.json()
        return result["output"]["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Together.ai LLM call failed: {str(e)}")
        raise

def call_openai_llm(system_prompt, user_prompt, temperature=0.0):
    """Call OpenAI LLM (GPT-4)"""
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": 4096
            }
        )
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenAI LLM call failed: {str(e)}")
        raise
