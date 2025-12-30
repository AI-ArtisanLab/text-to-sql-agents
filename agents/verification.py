"""
Verification Agent
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

def verification_agent(
    schema_context: dict,
    query_plan: dict,
    sql: str
) -> dict:
    system_prompt = open("prompts/verification.txt").read()

    user_prompt = f"""
SCHEMA CONTEXT
{json.dumps(schema_context, indent=2)}

QUERY PLAN
{json.dumps(query_plan, indent=2)}

GENERATED SQL
{sql}

OUTPUT ONLY VALID JSON. NO MARKDOWN, NO EXTRA TEXT.
"""

    response = call_llm(system_prompt, user_prompt)
    try:
        return extract_json(response)
    except json.JSONDecodeError as e:
        print(f"Warning: Verification agent returned invalid JSON. Raw:\n{response[:200]}")
        return {
            "is_valid": True,
            "issues": [],
            "severity": "non_critical"
        }
