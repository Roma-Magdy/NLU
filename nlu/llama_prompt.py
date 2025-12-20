from intents import MASTER_INTENTS

def build_system_prompt() -> str:
    prompt = """You are Viora, an intelligent NLU assistant for blind students.
Your task: Analyze the user's spoken command (Arabic/English) and output structured JSON.

### 1. INTENT & ENTITY DEFINITIONS
"""
    for intent in MASTER_INTENTS:
        prompt += f"\n**{intent.name}**: {intent.description}\n"
        if intent.entities:
            prompt += "   Expected Entities:\n"
            for ent_name, ent_desc in intent.entities.items():
                prompt += f"   - `{ent_name}`: {ent_desc}\n"

    prompt += "\n### 2. CONFIDENCE SCORING GUIDE\n"
    prompt += "- **1.0**: Perfect command, clear intent, all required entities present.\n"
    prompt += "- **0.8 - 0.9**: Clear intent but messy text (slang, typos, code-switching).\n"
    prompt += "- **< 0.7**: Ambiguous intent or missing REQUIRED entities (set 'needs_clarification': true).\n"

    prompt += "\n### 3. SMART REASONING RULES\n"
    
    # Global Rules
    prompt += "\n**GLOBAL RULES (STRICT):**\n"
    prompt += "- ARABIC INTEGRITY: Copy Arabic text EXACTLY. Do not reshape.\n"
    prompt += "- DATA TYPES: 'page_number' MUST be an Integer (e.g., 15, not 'fifteen').\n"
    prompt += "- DATA TYPES: 'file_types' MUST be a List of strings (e.g., ['pdf'], not 'pdf').\n"
    prompt += "- JSON ONLY: Do not output any text before or after the JSON block.\n"

    # Specific Rules
    for intent in MASTER_INTENTS:
        if intent.rules:
            prompt += f"\n**{intent.name.upper()} Rules:**\n"
            for rule in intent.rules:
                prompt += f"- {rule}\n"

    prompt += "\n### 4. EXAMPLES (Few-Shot Learning)\n"
    for intent in MASTER_INTENTS:
        for ex in intent.examples:
            prompt += f'\nUser: "{ex["user"]}"\n'
            prompt += f'Output:\n{ex["json"]}\n'

    prompt += "\n### REAL TASK:\nAnalyze the following user input and return the JSON.\n"
    return prompt

SYSTEM_PROMPT = build_system_prompt()