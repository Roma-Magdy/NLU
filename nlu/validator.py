from schemas import NLUResult
from intents import MASTER_INTENTS

def validate_nlu_result(result: NLUResult) -> NLUResult:
    """
    Sanity Check: 
    If the AI returns high confidence but misses a REQUIRED entity, 
    we forcibly downgrade it to 'needs_clarification'.
    """
    
    # 1. Find the definition for the detected intent
    intent_def = next((i for i in MASTER_INTENTS if i.name == result.intent), None)
    
    # If intent matches nothing (shouldn't happen) or is unknown/clarification, return as is
    if not intent_def:
        return result 

    # 2. Check for Missing Required Entities
    missing_keys = []
    # Convert Pydantic model to dict safely
    entities_dict = result.entities.model_dump()
    
    for req_key in intent_def.required_entities:
        value = entities_dict.get(req_key)
        
        # If value is strictly None, or empty string/list, it is missing
        if value is None or value == "" or value == []:
            missing_keys.append(req_key)

    # 3. ENFORCE RULES
    if missing_keys:
        print(f"VALIDATOR: Intent '{result.intent}' missing required fields {missing_keys}. Forcing Clarification.")
        
        # Force the system to ask for clarification
        result.needs_clarification = True
        result.confidence = 0.5 # Downgrade confidence
    
        
    return result