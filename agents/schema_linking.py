"""
Schema Linking Agent
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import json
from utils.llm import call_llm

def extract_json(text):
    """Extract JSON from text, handling markdown code blocks"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    return json.loads(text)

def schema_linking_agent(question: str, schema: str) -> dict:
    system_prompt = open("prompts/schema_linking_system.txt").read()

    user_prompt = f"""
DATABASE SCHEMA
{schema}

QUESTION
{question}

Return JSON only:"""

    response = call_llm(system_prompt, user_prompt)
    try:
        return extract_json(response)
    except json.JSONDecodeError as e:
        print(f"Warning: Schema linking returned invalid JSON. Raw:\n{response[:200]}")
        return {
            "relevant_tables": [],
            "relevant_columns": {},
            "relationships": [],
            "ambiguities": ["Unable to parse agent response"]
        }
