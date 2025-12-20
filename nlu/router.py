from schemas import NLUResult

def route_nlu_result(result: NLUResult):
    """
    Decides the 'Next Action' based on the NLU result.
    Returns: (Decision_String, NLUResult)
    """
    
    # 1. Handle Clarification / Low Confidence
    if result.needs_clarification:
        if result.intent == "clarification":
            return "CLARIFY_AMBIGUOUS", result
        else:
            return f"CLARIFY_MISSING_INFO_{result.intent.upper()}", result

    # 2. Handle Unknown Intents
    if result.intent == "unknown":
        return "HANDLE_UNKNOWN_REQUEST", result

    # 3. Intent-Specific Routing Logic
    entities = result.entities

    # --- File Operations ---
    if result.intent == "open_document":
        return "EXECUTE_OPEN_FILE", result
        
    if result.intent == "search_file":
        if not entities.search_query:
            return "CLARIFY_MISSING_QUERY", result
        return "EXECUTE_SEARCH", result

    # --- Navigation ---
    if result.intent == "navigate_document":
        has_page = entities.page_number is not None
        has_dir = entities.navigation_direction is not None
        
        if not has_page and not has_dir:
            return "CLARIFY_NAVIGATION_TARGET", result
            
        return "EXECUTE_NAVIGATION", result

    # --- Reading Control ---
    if result.intent == "read_document":
        # SAFETY CHECK: Ensure action exists before .upper()
        if entities.reading_action:
            return f"EXECUTE_AUDIO_{entities.reading_action.upper()}", result
        return "CLARIFY_MISSING_ACTION", result

    # --- Q&A ---
    if result.intent == "document_qa":
        return "EXECUTE_RAG_QUERY", result

    # --- Study Aids ---
    if result.intent == "generate_study_aid":
        if entities.study_aid_type:
             return f"EXECUTE_GENERATE_{entities.study_aid_type.upper()}", result
        return "EXECUTE_GENERATE_QUIZ", result # Default fallback

    if result.intent == "summarize_content":
        return "EXECUTE_SUMMARIZATION", result

    # --- System Control ---
    if result.intent == "focus_alert_control":
        if entities.focus_status:
            return f"EXECUTE_FOCUS_{entities.focus_status.upper()}", result
        return "CLARIFY_FOCUS_STATUS", result
        
    if result.intent == "ocr_request":
        return "EXECUTE_CAMERA_SCAN", result

    # Default Fallback
    return "UNHANDLED_INTENT", result