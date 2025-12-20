import torch
import json
import re
from typing import Tuple, cast, List, Dict, Any, Optional
from huggingface_hub import login
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig, 
    pipeline, 
    Pipeline,
    PreTrainedTokenizer
)
from schemas import NLUResult, Entities
from llama_prompt import SYSTEM_PROMPT
from validator import validate_nlu_result 

# --- AUTHENTICATION ---
HF_TOKEN = "" 
login(token=HF_TOKEN)

# --- Singleton Logic ---
_global_pipeline: Optional[Pipeline] = None
_global_tokenizer: Optional[PreTrainedTokenizer] = None

def load_resources() -> Tuple[Pipeline, PreTrainedTokenizer]:
    global _global_pipeline, _global_tokenizer
    
    current_pipeline = _global_pipeline
    current_tokenizer = _global_tokenizer

    if current_pipeline is not None and current_tokenizer is not None:
        return current_pipeline, current_tokenizer

    print("Loading Llama-3.1 Model...")
    
    model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        token=HF_TOKEN
    )

    # --- PRODUCTION GENERATION SETTINGS ---
    text_generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=1024,
        do_sample=True,        
        temperature=0.1,       
        top_p=0.9,             
        repetition_penalty=1.0,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        return_full_text=False
    )
    
    _global_pipeline = text_generator
    _global_tokenizer = tokenizer
    
    print("Model Loaded Successfully!")
    return text_generator, tokenizer

def _clean_json_output(text: str) -> str:
    """Robust extraction of the main JSON block."""
    text = text.strip()
    start_idx = text.find('{')
    if start_idx == -1: return text 
    
    # Try to find the last '}', but if missing, take everything
    end_idx = text.rfind('}')
    if end_idx == -1: return text[start_idx:] 
    return text[start_idx : end_idx + 1]

def _repair_json_string(json_str: str) -> str:
    """Smart Repair for missing commas."""
    # 1. Add missing comma after STRING value -> next key
    json_str = re.sub(r'"\s+"(\w+)":', r'", "\1":', json_str)

    # 2. Add missing comma after NUMBER/BOOL value -> next key
    json_str = re.sub(r'(\d+|true|false|null)\s+"(\w+)":', r'\1, "\2":', json_str)
    
    # 3. Add missing comma inside string lists
    json_str = re.sub(r'"\s+"', '", "', json_str)
    
    return json_str

def llama_nlu(text: str) -> NLUResult:
    generator, tokenizer = load_resources()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    
    prompt = cast(str, tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    ))

    try:
        raw_result = generator(prompt)
        outputs = cast(List[Dict[str, Any]], raw_result)
        raw_output = str(outputs[0]["generated_text"])
        
        json_str = _clean_json_output(raw_output)
        
        # --- SMART PARSING LOGIC ---
        data = None
        
        # Step 1: Fix Commas
        repaired_str = _repair_json_string(json_str)
        
        # Step 2: Smart Closure Loop
        # Attempts to fix cutoff JSON by trying different endings
        attempts = ["", "}", "}}", "}}}", '"}', '"}}', '"]}', '"]}}']
        
        for suffix in attempts:
            try:
                data = json.loads(repaired_str + suffix)
                break # Success!
            except json.JSONDecodeError:
                continue # Try next suffix
        
        if data is None:
            print(f"\n JSON CRASH (Unfixable). Full Output:\n{raw_output}\n")
            return NLUResult(intent="clarification", confidence=0.0, entities=Entities(), needs_clarification=True)

        entities_data = data.get("entities", {}) or {}
        entities_obj = Entities(**entities_data)

        result = NLUResult(
            intent=data.get("intent", "unknown"),
            confidence=float(data.get("confidence", 0.0)),
            entities=entities_obj,
            needs_clarification=data.get("needs_clarification", False)
        )
        
        # Inject raw user text for QA to ensure exact Arabic match
        if result.intent == "document_qa":
            result.entities.question = text

        final_result = validate_nlu_result(result)
        return final_result

    except Exception as e:
        print(f"Error processing NLU: {e}")
        return NLUResult(intent="clarification", confidence=0.0, entities=Entities(), needs_clarification=True)