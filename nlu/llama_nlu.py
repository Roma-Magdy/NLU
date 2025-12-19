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

# --- AUTHENTICATION ---
HF_TOKEN = ""
login(token=HF_TOKEN)

# --- Singleton Logic ---
# Initialize as None, typed optionally
_global_pipeline: Optional[Pipeline] = None
_global_tokenizer: Optional[PreTrainedTokenizer] = None

def load_resources() -> Tuple[Pipeline, PreTrainedTokenizer]:
    global _global_pipeline, _global_tokenizer
    
    # 1. Use local references for thread safety and type narrowing
    current_pipeline = _global_pipeline
    current_tokenizer = _global_tokenizer

    # 2. Return immediately if already loaded
    if current_pipeline is not None and current_tokenizer is not None:
        return current_pipeline, current_tokenizer

    print("Loading Llama-3.1 Model...")
    
    model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # Configuration for 4-bit quantization
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

    # Create Pipeline
    text_generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=300,
        temperature=0.1,
        return_full_text=False
    )
    
    # Update globals
    _global_pipeline = text_generator
    _global_tokenizer = tokenizer
    
    # Update locals for return
    current_pipeline = text_generator
    current_tokenizer = tokenizer
    
    print("Model Loaded Successfully!")
    
    # 3. Strict assertions to satisfy the return type 'Tuple[Pipeline, PreTrainedTokenizer]'
    assert current_pipeline is not None
    assert current_tokenizer is not None
    
    return current_pipeline, current_tokenizer

def _clean_json_output(text: str) -> str:
    """
    Robust JSON extraction: finds the first { and last } to ignore extra text.
    """
    text = text.strip()
    
    # Regex to find the largest outer block starting with { and ending with }
    # DOTALL allows matching across newlines
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
        
    return text

def llama_nlu(text: str) -> NLUResult:
    generator, tokenizer = load_resources()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    
    # Apply chat template
    prompt = cast(str, tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    ))

    try:
        # Generate
        raw_result = generator(prompt)
        
        # Explicit cast to tell linter this is a List[Dict]
        outputs = cast(List[Dict[str, Any]], raw_result)
        raw_output = str(outputs[0]["generated_text"])
        
        # Clean and Parse
        json_str = _clean_json_output(raw_output)
        data = json.loads(json_str)
        
        # Handle entities safely
        entities_data = data.get("entities", {}) or {}
        entities_obj = Entities(**entities_data)

        return NLUResult(
            intent=data.get("intent", "unknown"),
            confidence=float(data.get("confidence", 0.0)),
            entities=entities_obj,
            needs_clarification=data.get("needs_clarification", False)
        )

    except json.JSONDecodeError:
        print(f"JSON Error. Output was: {raw_output[:100]}...")
        return NLUResult(
            intent="clarification",
            confidence=0.0,
            entities=Entities(),
            needs_clarification=True
        )
    except Exception as e:
        print(f"Error: {e}")
        return NLUResult(
            intent="unknown",
            confidence=0.0,
            entities=Entities(),
            needs_clarification=False
        )