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
    prompt += "- **0.9 - 1.0**: High Confidence. The intent is clear. NOTE: Dialect (Egyptian) and Mixed Arabic/English (Code-Switching) are considered VALID and should score high (0.9+).\n"
    prompt += "- **0.7 - 0.8**: Medium Confidence. Intent is understood but contains typos, stuttering, or grammar errors.\n"
    prompt += "- **< 0.7**: Low Confidence. Ambiguous intent or missing REQUIRED entities (set 'needs_clarification': true).\n"

    prompt += "\n### 3. SMART REASONING RULES\n"
    prompt += "- ARABIC INTEGRITY: Copy Arabic text EXACTLY as spoken. Do not rephrase. Do not translate.\n"
    prompt += "- DATA TYPES: 'page_number' MUST be an Integer (e.g., 15).\n"
    prompt += "- DATA TYPES: 'file_types' MUST be a List of strings (e.g., ['pdf']).\n"

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

    # --- NEW CRITICAL SECTION ---
    prompt += "\n### 5. CRITICAL JSON SYNTAX RULES (MUST FOLLOW)\n"
    prompt += "1. **COMMAS**: You MUST place a comma `,` after every key-value pair. Example: `\"confidence\": 0.9, \"entities\": ...`\n"
    prompt += "2. **CLOSURE**: You MUST close the JSON object with `}}`. Do not stop early.\n"
    prompt += "3. **NO TRAILING COMMAS**: Do not put a comma after the last item in a list or object.\n"
    prompt += "4. **PURE JSON**: Output ONLY the JSON string. No markdown, no explanations.\n"
    
    prompt += "\n### REAL TASK:\nAnalyze the following user input and return the VALID JSON.\n"
    return prompt

SYSTEM_PROMPT = build_system_prompt()