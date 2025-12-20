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
# Local Imports
from schemas import NLUResult, Entities
from llama_prompt import SYSTEM_PROMPT
from validator import validate_nlu_result  

# --- AUTHENTICATION ---
# Ensure your token is valid or set as environment variable
HF_TOKEN = "" 
login(token=HF_TOKEN)

# --- Singleton Logic ---
_global_pipeline: Optional[Pipeline] = None
_global_tokenizer: Optional[PreTrainedTokenizer] = None

def load_resources() -> Tuple[Pipeline, PreTrainedTokenizer]:
    global _global_pipeline, _global_tokenizer
    
    # 1. Thread-safe local reference
    current_pipeline = _global_pipeline
    current_tokenizer = _global_tokenizer

    # 2. Return cached if available
    if current_pipeline is not None and current_tokenizer is not None:
        return current_pipeline, current_tokenizer

    print("Loading Llama-3.1 Model...")
    
    model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # Configuration for 4-bit quantization (Speed & Memory Efficiency)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
    tokenizer.pad_token = tokenizer.eos_token

    # Load Model
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        token=HF_TOKEN
    )

    # Create Pipeline with STRICT GENERATION SETTINGS
    text_generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=300,
        # CRITICAL FOR LOGIC:
        do_sample=False,       # Deterministic mode (Greedy Decoding)
        temperature=None,      # Disabled because we are not sampling
        top_p=None,            # Disabled because we are not sampling
        return_full_text=False
    )
    
    # Update globals
    _global_pipeline = text_generator
    _global_tokenizer = tokenizer
    
    print("Model Loaded Successfully!")
    
    return text_generator, tokenizer

def _clean_json_output(text: str) -> str:
    """
    Robust JSON extraction: finds the first { and last } to ignore extra text.
    """
    text = text.strip()
    # DOTALL allows matching across newlines
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def llama_nlu(text: str) -> NLUResult:
    """
    Main Entry Point: Takes text, runs LLM, parses JSON, and Validates Logic.
    """
    generator, tokenizer = load_resources()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    
    # Apply Chat Template
    prompt = cast(str, tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    ))

    try:
        # Generate Response
        raw_result = generator(prompt)
        
        # Parse Output
        outputs = cast(List[Dict[str, Any]], raw_result)
        raw_output = str(outputs[0]["generated_text"])
        
        # Clean JSON string
        json_str = _clean_json_output(raw_output)
        data = json.loads(json_str)
        
        # Pydantic Parsing (Handles Type Conversion safely)
        entities_data = data.get("entities", {}) or {}
        entities_obj = Entities(**entities_data)

        # Initial Result Construction
        result = NLUResult(
            intent=data.get("intent", "unknown"),
            confidence=float(data.get("confidence", 0.0)),
            entities=entities_obj,
            needs_clarification=data.get("needs_clarification", False)
        )

        # --- STEP 2: LOGIC VALIDATION ---
        # "Did the AI forget a required field?"
        final_result = validate_nlu_result(result)

        return final_result

    except json.JSONDecodeError:
        print(f"JSON Error. Output was: {raw_output[:100]}...")
        # Fail safe to clarification
        return NLUResult(
            intent="clarification", 
            confidence=0.0, 
            entities=Entities(), 
            needs_clarification=True
        )
    except Exception as e:
        print(f"Error: {e}")
        # Fail safe to unknown
        return NLUResult(
            intent="unknown", 
            confidence=0.0, 
            entities=Entities()
        )