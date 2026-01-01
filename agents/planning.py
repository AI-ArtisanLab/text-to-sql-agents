"""
Planning Agent
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

def planning_agent(question: str, schema_context: dict) -> dict:
    system_prompt = open("prompts/planning.txt").read()

    user_prompt = f"""
SCHEMA CONTEXT (approved tables and columns):
{json.dumps(schema_context, indent=2)}

QUESTION
{question}

Return JSON only:"""

    response = call_llm(system_prompt, user_prompt)
    try:
        return extract_json(response)
    except json.JSONDecodeError as e:
        print(f"Warning: Planning agent returned invalid JSON. Raw response:\n{response[:200]}")
        # Return a minimal valid plan as fallback
        return {
            "intent": question,
            "steps": ["Extract relevant data from schema"],
            "entities": [],
            "aggregations": [],
            "grouping": [],
            "ambiguities": ["Unable to parse agent response"]
        }
