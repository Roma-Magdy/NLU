import time
import arabic_reshaper
from typing import cast
from bidi.algorithm import get_display
from llama_nlu import llama_nlu
from router import route_nlu_result

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

def fix_text(text: str) -> str:
    if not text: return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return cast(str, get_display(reshaped))
    except: return text

def test_command(text: str):
    display_text = fix_text(text)
    print(f"\n{YELLOW}User says:{RESET} '{display_text}'")
    
    start = time.time()
    nlu_result = llama_nlu(text)
    decision, payload = route_nlu_result(nlu_result)
    duration = time.time() - start
    
    # Colors
    color = GREEN if "EXECUTE" in decision else (CYAN if "CLARIFY" in decision else RED)

    print(f"   Time: {duration:.2f}s")
    print(f"   Decision: {color}{decision}{RESET}")
    print(f"   Intent: {payload.intent} (Conf: {payload.confidence:.2f})")
    
    # Clean display of entities
    ents = payload.entities.model_dump(exclude_none=True)
    clean_ents = {k: fix_text(str(v)) if isinstance(v, str) else v for k, v in ents.items()}
    print(f"   Entities: {clean_ents}")

if __name__ == "__main__":
    print(f"{GREEN}=== Viora Ultimate Stress Test (All 11 Intents) ==={RESET}")

    test_suite = {
        "1. File & Search (Context Aware)": [
            "افتحلي file الـ Intro to CS",
            "دورلي على book بيتكلم عن Neural Networks",  # Should be PDF
            "هاتلي الـ slides بتاعة المحاضرة اللي فاتت", # Should be PPTX
        ],
        "2. Navigation (Logic Check)": [
            "هات Page 15",  # Must be navigate, not search
            "Next page",
            "ارجع للصفحة 4",
        ],
        "3. Reading (Audio Controls)": [
            "Start reading",
            "طب استنى",      # Pause
            "كمل قراءة",     # Resume
            "بقولك ايه .. كفاية كده", # Stop
        ],
        "4. OCR (Scanning)": [
            "اقرأ الورقة دي بالكاميرا",
            "Scan this page for me",
            "What is written in this image?",
        ],
        "5. Focus Alerts (Safety)": [
            "شغل نظام التركيز",        # Enable
            "بطل تفكرني كل شوية",      # Disable
            "Alert me every 20 minutes",
        ],
        "6. Study Intelligence": [
            "لخصلي الـ Chapter ده في نقط",
            "اعملي Quiz على الجزء اللي فات",
            "Generate flashcards for the definitions",
        ],
        "7. Q&A (Full Context)": [
            "Explain the diagram on page 20", # Must extract Page 20
            "هو يعني ايه Polymorphism ؟",     # Must keep full text
            "ايه الفرق بين Stack و Queue ؟",
        ],
        "8. Clarification & Unknown": [
            "طب وبعدين؟",     # Clarify
            "Order Pizza",    # Unknown
            "شغل أغنية لعمرو دياب", # Unknown
        ]
    }

    for category, commands in test_suite.items():
        print(f"\n{CYAN}--- {category} ---{RESET}")
        for cmd in commands:
            test_command(cmd)