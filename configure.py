# Configuration Helper for Text-to-SQL Agents
# Allows users to easily choose their provider combination

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER_CHOICES = {
    "1": {
        "name": "Local Only (Ollama)",
        "llm": "ollama",
        "embedding": "ollama",
        "description": "Uses Mistral for LLM + Nomic Embed for embeddings (FREE, LOCAL, NO API KEY)",
        "requirements": [
            "Ollama installed and running: ollama serve",
            "Model pulled: ollama pull mistral",
            "Embedding model pulled: ollama pull nomic-embed-text"
        ]
    },
    "2": {
        "name": "Cloud Only (OpenAI)",
        "llm": "openai",
        "embedding": "openai",
        "description": "Uses GPT-4.1 for LLM + text-embedding-3-large for embeddings (PAID, CLOUD)",
        "requirements": [
            "OpenAI API key from https://platform.openai.com/api-keys",
            "Set OPENAI_API_KEY in .env",
            "Sufficient quota for GPT-4.1"
        ]
    },
    "3": {
        "name": "Hybrid (Ollama LLM + OpenAI Embeddings)",
        "llm": "ollama",
        "embedding": "openai",
        "description": "Uses Mistral for LLM + OpenAI for embeddings (MIXED)",
        "requirements": [
            "Ollama with Mistral model",
            "OpenAI API key"
        ]
    },
    "4": {
        "name": "Hybrid (OpenAI LLM + Ollama Embeddings)",
        "llm": "openai",
        "embedding": "ollama",
        "description": "Uses GPT-4.1 for LLM + Ollama for embeddings (MIXED)",
        "requirements": [
            "OpenAI API key",
            "Ollama with embedding model"
        ]
    }
}

def print_choices():
    print("\n" + "="*70)
    print("TEXT-TO-SQL AGENTS - PROVIDER CONFIGURATION")
    print("="*70 + "\n")
    
    for key, config in PROVIDER_CHOICES.items():
        print(f"Option {key}: {config['name']}")
        print(f"  Description: {config['description']}")
        print(f"  Requirements:")
        for req in config['requirements']:
            print(f"    - {req}")
        print()

def get_current_config():
    """Show currently active configuration"""
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    
    print("\n" + "="*70)
    print("CURRENT CONFIGURATION")
    print("="*70)
    print(f"LLM Provider: {llm_provider.upper()}")
    print(f"Embedding Provider: {embedding_provider.upper()}")
    print("="*70 + "\n")

def update_config(choice):
    """Update .env with selected configuration"""
    if choice not in PROVIDER_CHOICES:
        print("Invalid choice!")
        return False
    
    config = PROVIDER_CHOICES[choice]
    
    # Read current .env
    with open(".env", "r") as f:
        lines = f.readlines()
    
    # Update providers
    new_lines = []
    for line in lines:
        if line.startswith("LLM_PROVIDER="):
            new_lines.append(f"LLM_PROVIDER={config['llm']}\n")
        elif line.startswith("EMBEDDING_PROVIDER="):
            new_lines.append(f"EMBEDDING_PROVIDER={config['embedding']}\n")
        else:
            new_lines.append(line)
    
    # Write back
    with open(".env", "w") as f:
        f.writelines(new_lines)
    
    print(f"\n✓ Updated configuration to: {config['name']}")
    print(f"  LLM: {config['llm'].upper()}")
    print(f"  Embeddings: {config['embedding'].upper()}\n")
    
    return True

if __name__ == "__main__":
    get_current_config()
    print_choices()
    
    choice = input("Enter your choice (1-4) or 'q' to quit: ").strip()
    if choice.lower() == 'q':
        print("Exiting...")
    else:
        if update_config(choice):
            print("\nNext steps:")
            print("1. Ensure required services are running")
            print("2. Run: python main.py")
        else:
            print("Configuration update failed!")
