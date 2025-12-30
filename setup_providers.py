#!/usr/bin/env python3
"""
Interactive setup script to configure LLM and Embedding providers.
Allows users to choose between Ollama and OpenAI for both LLM and embeddings.

Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import os
import sys
from pathlib import Path


def load_env():
    """Load current .env file"""
    env_file = Path(".env")
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
    return env_vars


def save_env(env_vars):
    """Save environment variables to .env file"""
    content = """# Provider Configuration
# Available options: "ollama" or "openai"
LLM_PROVIDER={llm_provider}
EMBEDDING_PROVIDER={embedding_provider}

# Ollama Configuration (for LLM_PROVIDER=ollama)
OLLAMA_ENDPOINT={ollama_endpoint}
OLLAMA_LLM_MODEL={ollama_llm_model}

# Ollama Configuration (for EMBEDDING_PROVIDER=ollama)
OLLAMA_EMBEDDING_MODEL={ollama_embedding_model}

# OpenAI Configuration (for LLM_PROVIDER=openai and/or EMBEDDING_PROVIDER=openai)
# Get your API key from https://platform.openai.com/api-keys
OPENAI_API_KEY={openai_api_key}
OPENAI_LLM_MODEL={openai_llm_model}
OPENAI_EMBEDDING_MODEL={openai_embedding_model}
""".format(**env_vars)
    
    with open(".env", 'w') as f:
        f.write(content)


def display_banner():
    """Display setup banner"""
    print("\n" + "="*60)
    print(" Text-to-SQL Agent Provider Configuration Setup")
    print("="*60 + "\n")


def choose_provider(provider_type):
    """Let user choose a provider"""
    print(f"\nSelect {provider_type} Provider:")
    print("1. Ollama (local)")
    print("2. OpenAI (cloud)")
    
    while True:
        choice = input(f"\nEnter choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            return 'ollama' if choice == '1' else 'openai'
        print("Invalid choice. Please enter 1 or 2.")


def configure_ollama(env_vars, model_type):
    """Configure Ollama settings"""
    print(f"\n--- Ollama {model_type} Configuration ---")
    
    if model_type == "LLM":
        default_model = "mistral"
        model_key = "OLLAMA_LLM_MODEL"
    else:
        default_model = "nomic-embed-text"
        model_key = "OLLAMA_EMBEDDING_MODEL"
    
    endpoint = input(f"Ollama endpoint [{env_vars.get('OLLAMA_ENDPOINT', 'http://localhost:11434')}]: ").strip()
    if endpoint:
        env_vars['OLLAMA_ENDPOINT'] = endpoint
    
    model = input(f"Ollama {model_type} model [{env_vars.get(model_key, default_model)}]: ").strip()
    if model:
        env_vars[model_key] = model
    
    return env_vars


def configure_openai(env_vars, model_type):
    """Configure OpenAI settings"""
    print(f"\n--- OpenAI {model_type} Configuration ---")
    
    if model_type == "LLM":
        default_model = "gpt-4-turbo"
        model_key = "OPENAI_LLM_MODEL"
    else:
        default_model = "text-embedding-3-large"
        model_key = "OPENAI_EMBEDDING_MODEL"
    
    api_key = input(f"OpenAI API Key [{env_vars.get('OPENAI_API_KEY', 'not_set')[:10]}...]: ").strip()
    if api_key:
        env_vars['OPENAI_API_KEY'] = api_key
    elif not env_vars.get('OPENAI_API_KEY'):
        print("WARNING: No OpenAI API key provided. You'll need to set OPENAI_API_KEY in .env")
    
    model = input(f"OpenAI {model_type} model [{env_vars.get(model_key, default_model)}]: ").strip()
    if model:
        env_vars[model_key] = model
    
    return env_vars


def show_provider_combinations():
    """Show available provider combinations"""
    print("\n" + "="*60)
    print("Available Provider Combinations:")
    print("="*60)
    combinations = [
        ("Ollama", "Ollama", "Fast local inference", "Requires Ollama running locally"),
        ("Ollama", "OpenAI", "Local LLM + Cloud embeddings", "Requires Ollama + OpenAI API key"),
        ("OpenAI", "Ollama", "Cloud LLM + Local embeddings", "Requires OpenAI API key + Ollama"),
        ("OpenAI", "OpenAI", "Full cloud inference", "Requires OpenAI API key"),
    ]
    
    for i, (llm, emb, desc, req) in enumerate(combinations, 1):
        print(f"\n{i}. LLM: {llm} | Embeddings: {emb}")
        print(f"   Description: {desc}")
        print(f"   Requirement: {req}")


def setup_wizard():
    """Interactive setup wizard"""
    display_banner()
    
    show_provider_combinations()
    
    env_vars = load_env()
    
    # Set defaults if not present
    if 'LLM_PROVIDER' not in env_vars:
        env_vars['LLM_PROVIDER'] = 'ollama'
    if 'EMBEDDING_PROVIDER' not in env_vars:
        env_vars['EMBEDDING_PROVIDER'] = 'ollama'
    if 'OLLAMA_ENDPOINT' not in env_vars:
        env_vars['OLLAMA_ENDPOINT'] = 'http://localhost:11434'
    if 'OLLAMA_LLM_MODEL' not in env_vars:
        env_vars['OLLAMA_LLM_MODEL'] = 'mistral'
    if 'OLLAMA_EMBEDDING_MODEL' not in env_vars:
        env_vars['OLLAMA_EMBEDDING_MODEL'] = 'nomic-embed-text'
    if 'OPENAI_LLM_MODEL' not in env_vars:
        env_vars['OPENAI_LLM_MODEL'] = 'gpt-4-turbo'
    if 'OPENAI_EMBEDDING_MODEL' not in env_vars:
        env_vars['OPENAI_EMBEDDING_MODEL'] = 'text-embedding-3-large'
    if 'OPENAI_API_KEY' not in env_vars:
        env_vars['OPENAI_API_KEY'] = 'your_openai_api_key_here'
    
    # Choose LLM provider
    print("\n" + "-"*60)
    print("Step 1: Configure Language Model (LLM)")
    print("-"*60)
    llm_provider = choose_provider("LLM")
    env_vars['LLM_PROVIDER'] = llm_provider
    
    if llm_provider == 'ollama':
        env_vars = configure_ollama(env_vars, "LLM")
    else:
        env_vars = configure_openai(env_vars, "LLM")
    
    # Choose Embedding provider
    print("\n" + "-"*60)
    print("Step 2: Configure Embedding Model")
    print("-"*60)
    embedding_provider = choose_provider("Embedding")
    env_vars['EMBEDDING_PROVIDER'] = embedding_provider
    
    if embedding_provider == 'ollama':
        env_vars = configure_ollama(env_vars, "Embedding")
    else:
        env_vars = configure_openai(env_vars, "Embedding")
    
    # Summary
    print("\n" + "="*60)
    print("Configuration Summary:")
    print("="*60)
    print(f"LLM Provider: {env_vars['LLM_PROVIDER'].upper()}")
    if env_vars['LLM_PROVIDER'] == 'ollama':
        print(f"  - Endpoint: {env_vars['OLLAMA_ENDPOINT']}")
        print(f"  - Model: {env_vars['OLLAMA_LLM_MODEL']}")
    else:
        print(f"  - Model: {env_vars['OPENAI_LLM_MODEL']}")
    
    print(f"\nEmbedding Provider: {env_vars['EMBEDDING_PROVIDER'].upper()}")
    if env_vars['EMBEDDING_PROVIDER'] == 'ollama':
        print(f"  - Endpoint: {env_vars['OLLAMA_ENDPOINT']}")
        print(f"  - Model: {env_vars['OLLAMA_EMBEDDING_MODEL']}")
    else:
        print(f"  - Model: {env_vars['OPENAI_EMBEDDING_MODEL']}")
    
    # Save configuration
    print("\n" + "-"*60)
    confirm = input("Save configuration? (y/n): ").strip().lower()
    if confirm == 'y':
        save_env(env_vars)
        print("✓ Configuration saved to .env")
        print("\nSetup complete! You can now run: python main.py")
        return True
    else:
        print("Configuration not saved.")
        return False


if __name__ == "__main__":
    try:
        setup_wizard()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)
