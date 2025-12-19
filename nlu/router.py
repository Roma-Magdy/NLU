from schemas import NLUResult

def route_nlu_result(result: NLUResult) -> tuple[str, NLUResult]:
    """
    Decides what to do based on Llama 3's confidence score.
    Returns: (Decision_String, NLUResult_Payload)
    """
    
    # 1. SCOPE CHECK (Priority #1): 
    # If the model explicitly says "unknown", reject it immediately.
    # We do this BEFORE clarification check to avoid asking "Did you mean...?" for music/uber.
    if result.intent == "unknown":
        return "OUT_OF_SCOPE", result

    # 2. SAFETY CHECK:
    # If the model flagged confusion for a VALID intent (e.g. read vs navigate), ask user.
    if result.needs_clarification:
        return "CLARIFY (Model Request)", result

    # 3. CONFIDENCE ZONES
    score = result.confidence

    if score >= 0.85:
        # High Confidence -> Do it
        return "EXECUTE_DIRECTLY", result
    
    elif score >= 0.50:
        # Medium Confidence -> Confirm with user
        return "EXECUTE_WITH_CONFIRMATION", result
    
    else:
        # Low Confidence -> Ask clarification
        return "ASK_USER_CLARIFICATION", result