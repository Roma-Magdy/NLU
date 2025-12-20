from typing import List, Dict, Optional

class IntentDef:
    def __init__(
        self, 
        name: str, 
        description: str, 
        entities: Dict[str, str],
        required_entities: List[str], # <--- REFINEMENT: Explicit Validation Contract
        rules: List[str], 
        examples: List[Dict[str, str]]
    ):
        self.name = name
        self.description = description
        self.entities = entities
        self.required_entities = required_entities
        self.rules = rules
        self.examples = examples

MASTER_INTENTS = [
    IntentDef(
        name="open_document",
        description="Open a specific local file for reading.",
        entities={"document_name": "The exact name of the file."},
        required_entities=["document_name"],
        rules=[
            "Requires a specific filename. If user says 'Open file' (افتح ملف) without a name, return 'needs_clarification': true.",
            "If user provides a TOPIC instead of a NAME (e.g., 'Open the book about AI'), map to 'search_file' instead."
        ],
        examples=[
            {"user": "افتحلي file الـ Intro to CS", "json": '{"intent": "open_document", "confidence": 1.0, "entities": {"document_name": "Intro to CS"}}'},
            {"user": "يا فيورا افتحي الـ pdf اللي اسمه Data Structures Final Revision", "json": '{"intent": "open_document", "confidence": 1.0, "entities": {"document_name": "Data Structures Final Revision"}}'},
            {"user": "افتحلي الملف لو سمحت", "json": '{"intent": "open_document", "confidence": 0.5, "entities": {"document_name": null}, "needs_clarification": true}'}
        ]
    ),
    IntentDef(
        name="search_file",
        description="Search for resources (Books, Slides, PDFs) not currently open.",
        entities={
            "search_query": "The topic or keyword.",
            "file_types": "List of extensions. e.g. ['pdf'] or ['pptx', 'pdf']."
        },
        required_entities=["search_query"],
        rules=[
            "Extract ONLY the topic. REMOVE filler words: 'find', 'search', 'about', 'book about', 'عن', 'يخص'.",
            "Map 'Slides'/'Presentation' -> ['pptx'].",
            "Map 'Book'/'Ref' -> ['pdf'].",
            "Map 'Lectures'/'محاضرات' -> ['pptx', 'pdf'] (Search both).",
            "Map 'Word' -> ['docx'].",
            "If user says 'Files' (Generic) -> set file_types to null (Search All)."
        ],
        examples=[
            {"user": "دورلي على book بيتكلم عن Neural Networks", "json": '{"intent": "search_file", "confidence": 0.9, "entities": {"search_query": "Neural Networks", "file_types": ["pdf"]}}'},
            {"user": "عايز محاضرات الـ History", "json": '{"intent": "search_file", "confidence": 0.95, "entities": {"search_query": "History", "file_types": ["pptx", "pdf"]}}'},
            {"user": "شوفلي اي presentation عن الـ ML basics بس تكون pptx", "json": '{"intent": "search_file", "confidence": 0.95, "entities": {"search_query": "ML basics", "file_types": ["pptx"]}}'}
        ]
    ),
    IntentDef(
        name="navigate_document",
        description="Move inside the currently open document.",
        entities={
            "page_number": "Integer page number.",
            "navigation_direction": "One of ['next', 'previous', 'to']."
        },
        required_entities=[], # Logic handles this
        rules=[
            "LOGIC: If `page_number` exists, `navigation_direction` defaults to 'to'.",
            "LOGIC: If `page_number` is MISSING, `navigation_direction` is REQUIRED (e.g. 'Next' -> 'next').",
            "Context Rule: 'Get Page 15' is ALWAYS navigate_document."
        ],
        examples=[
            {"user": "هات Page 15", "json": '{"intent": "navigate_document", "confidence": 1.0, "entities": {"page_number": 15, "navigation_direction": "to"}}'},
            {"user": "Go to page 5", "json": '{"intent": "navigate_document", "confidence": 1.0, "entities": {"page_number": 5, "navigation_direction": "to"}}'},
            {"user": "ممكن تنزل للصفحة اللي بعدها", "json": '{"intent": "navigate_document", "confidence": 1.0, "entities": {"navigation_direction": "next"}}'}
        ]
    ),
    IntentDef(
        name="read_document",
        description="Control the text-to-speech audio player.",
        entities={"reading_action": "One of ['start', 'stop', 'pause', 'resume']."},
        required_entities=["reading_action"],
        rules=[
            "PAUSE: 'Wait', 'Hold on', 'استنى'.",
            "STOP: 'Stop', 'Enough', 'Silence', 'كفاية', 'اسكت'.",
            "RESUME: 'Continue', 'Resume', 'Go on', 'كمل'."
        ],
        examples=[
            {"user": "Start reading", "json": '{"intent": "read_document", "confidence": 1.0, "entities": {"reading_action": "start"}}'},
            {"user": "طب استنى دقيقة", "json": '{"intent": "read_document", "confidence": 0.9, "entities": {"reading_action": "pause"}}'},
            {"user": "خلاص كفاية صدعتني", "json": '{"intent": "read_document", "confidence": 0.95, "entities": {"reading_action": "stop"}}'}
        ]
    ),
    IntentDef(
        name="document_qa",
        description="Ask specific questions about the content.",
        entities={"question": "The full question text."},
        required_entities=["question"],
        rules=[
            "Triggers: 'Explain', 'What is', 'Define', 'Meaning of', 'يعني ايه', 'ما هو'.",
            "Capture the full sentence."
        ],
        examples=[
            {"user": "Explain the diagram on page 20", "json": '{"intent": "document_qa", "confidence": 1.0, "entities": {"question": "Explain the diagram on page 20", "page_number": 20}}'},
            {"user": "هو يعني ايه Polymorphism في الـ OOP ؟", "json": '{"intent": "document_qa", "confidence": 1.0, "entities": {"question": "هو يعني ايه Polymorphism في الـ OOP ؟"}}'}
        ]
    ),
    IntentDef(
        name="summarize_content",
        description="Generate a summary.",
        entities={"summary_format": "Optional format."},
        required_entities=[],
        rules=["Triggers: 'Summarize', 'Recap', 'tl;dr', 'لخص'."],
        examples=[
            {"user": "لخصلي الـ Chapter ده في نقط", "json": '{"intent": "summarize_content", "confidence": 1.0, "entities": {"summary_format": "bullet_points"}}'}
        ]
    ),
    IntentDef(
        name="generate_study_aid",
        description="Create study materials.",
        entities={"study_aid_type": "One of ['quiz', 'flashcards']."},
        required_entities=["study_aid_type"],
        rules=["Map 'Test'/'Exam' -> quiz. Map 'Definitions' -> flashcards."],
        examples=[
            {"user": "اعملي Quiz على الجزء ده", "json": '{"intent": "generate_study_aid", "confidence": 1.0, "entities": {"study_aid_type": "quiz"}}'}
        ]
    ),
    IntentDef(
        name="focus_alert_control",
        description="Manage study focus alerts.",
        entities={"focus_status": "One of ['enable', 'disable']."},
        required_entities=["focus_status"],
        rules=["ENABLE: 'Focus', 'شغل'. DISABLE: 'Stop reminding', 'بطل زن'."],
        examples=[
            {"user": "بطل تفكرني كل شوية", "json": '{"intent": "focus_alert_control", "confidence": 1.0, "entities": {"focus_status": "disable"}}'}
        ]
    ),
    IntentDef(
        name="ocr_request",
        description="Scan printed text via camera.",
        entities={},
        required_entities=[],
        rules=["Triggers: 'Camera', 'Scan', 'Photo', 'صور الورقة'."],
        examples=[
            {"user": "اقرأ الورقة دي بالكاميرا", "json": '{"intent": "ocr_request", "confidence": 1.0, "entities": {}}'}
        ]
    ),
    IntentDef(
        name="clarification",
        description="Handle vague inputs.",
        entities={},
        required_entities=[],
        rules=["Use when NO specific action is clear. Triggers: 'Hello', 'So?', 'طب وبعدين'."],
        examples=[
            {"user": "طب وبعدين؟", "json": '{"intent": "clarification", "confidence": 1.0, "entities": {}}'}
        ]
    ),
    IntentDef(
        name="unknown",
        description="Out of scope inputs.",
        entities={},
        required_entities=[],
        rules=["Triggers: Food, Taxi, Music, Weather, Jokes."],
        examples=[
            {"user": "Order pizza", "json": '{"intent": "unknown", "confidence": 1.0, "entities": {}}'}
        ]
    )
]