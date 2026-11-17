"""
Pillar 2: 2-4 Clearly Described Tools
Educational and computational tools for the AI Study Buddy Agent.
Each tool has explicit schemas, input validation, and self-contained error handling.
"""

import math
import os
import re
import json
import time
from typing import Dict, Any, List, Optional

# Comprehensive curated educational knowledge base
KNOWLEDGE_BASE = {
    # Biology
    "photosynthesis": {
        "subject": "biology",
        "title": "Photosynthesis",
        "definition": "The biochemical process by which photoautotrophs (plants, algae) convert light energy into chemical energy stored in glucose.",
        "formula": "6CO2 + 6H2O + light energy -> C6H12O6 + 6O2",
        "key_facts": [
            "Occurs inside chloroplasts containing the green pigment chlorophyll.",
            "Light-dependent reactions occur in the thylakoid membranes.",
            "Calvin Cycle (light-independent reactions) occurs in the stroma.",
            "Releases oxygen gas into the atmosphere as a byproduct."
        ]
    },
    "mitochondria": {
        "subject": "biology",
        "title": "Mitochondria",
        "definition": "Double membrane-bound organelles known as the powerhouse of eukaryotic cells.",
        "formula": "C6H12O6 + 6O2 -> 6CO2 + 6H2O + 36-38 ATP",
        "key_facts": [
            "Generates adenosine triphosphate (ATP) through cellular respiration.",
            "Has its own circular DNA (mtDNA) and ribosomes.",
            "Inner membrane is folded into cristae to maximize surface area."
        ]
    },
    "dna": {
        "subject": "biology",
        "title": "DNA Structure & Replication",
        "definition": "Deoxyribonucleic acid is the hereditary molecule carrying genetic instructions for development and functioning.",
        "formula": "Double helix of nucleotide pairs (Adenine-Thymine, Guanine-Cytosine)",
        "key_facts": [
            "Composed of a phosphate group, deoxyribose sugar, and nitrogenous base.",
            "Adenine pairs with Thymine (2 hydrogen bonds); Guanine pairs with Cytosine (3 hydrogen bonds).",
            "Discovered by James Watson, Francis Crick, and Rosalind Franklin (1953)."
        ]
    },
    # Physics
    "newton's second law": {
        "subject": "physics",
        "title": "Newton's Second Law of Motion",
        "definition": "The rate of change of momentum of a body is directly proportional to the applied force and occurs in the direction in which the force acts.",
        "formula": "F = m * a (Force = mass x acceleration)",
        "key_facts": [
            "Force is measured in Newtons (N), mass in kilograms (kg), acceleration in m/s^2.",
            "If net force is zero, velocity remains constant (Newton's 1st law).",
            "Weight is gravitational force: W = m * g."
        ]
    },
    "gravity": {
        "subject": "physics",
        "title": "Gravitation & Free Fall",
        "definition": "The universal attractive force between any two objects with mass.",
        "formula": "F = G * (m1 * m2) / r^2; Near Earth surface: g = 9.8 m/s^2; Free fall distance: d = 0.5 * g * t^2",
        "key_facts": [
            "Gravitational constant G = 6.674 x 10^-11 N*(m/kg)^2.",
            "Acceleration due to gravity on Earth is approximately 9.8 m/s^2 (or 32.2 ft/s^2).",
            "In a vacuum, all objects fall at identical acceleration regardless of mass."
        ]
    },
    "ohm's law": {
        "subject": "physics",
        "title": "Ohm's Law (Electricity)",
        "definition": "The electric current through a conductor between two points is directly proportional to the voltage across the two points and inversely proportional to the resistance.",
        "formula": "V = I * R (Voltage = Current x Resistance)",
        "key_facts": [
            "V is measured in Volts (V), I in Amperes (A), and R in Ohms (Î©).",
            "Electrical power: P = V * I = I^2 * R = V^2 / R.",
            "Applies strictly to ohmic conductors at constant temperature."
        ]
    },
    # Chemistry
    "acids and bases": {
        "subject": "chemistry",
        "title": "Acids, Bases & pH Scale",
        "definition": "Substances characterized by their ability to donate protons (Arrhenius/BrÃ¸nsted-Lowry acid) or accept protons (base).",
        "formula": "pH = -log10[H+]; Neutral pH = 7.0; Acidic < 7.0; Basic > 7.0",
        "key_facts": [
            "Acids turn blue litmus paper red; bases turn red litmus paper blue.",
            "Strong acids: HCl, H2SO4, HNO3; Strong bases: NaOH, KOH.",
            "Neutralization reaction: Acid + Base -> Salt + Water."
        ]
    },
    # Math
    "pythagorean theorem": {
        "subject": "math",
        "title": "Pythagorean Theorem",
        "definition": "Fundamental relationship among the three sides of a right-angled Euclidean triangle.",
        "formula": "a^2 + b^2 = c^2 (where c is the hypotenuse)",
        "key_facts": [
            "Hypotenuse is always the longest side opposing the 90-degree right angle.",
            "Common Pythagorean triples: (3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25).",
            "Generalizes to the Law of Cosines for non-right triangles."
        ]
    },
    "quadratic formula": {
        "subject": "math",
        "title": "Quadratic Formula",
        "definition": "Formula providing the roots (solutions) to any quadratic equation of the form ax^2 + bx + c = 0.",
        "formula": "x = (-b Â± sqrt(b^2 - 4*a*c)) / (2*a)",
        "key_facts": [
            "Discriminant Î” = b^2 - 4*a*c determines nature of roots.",
            "If Î” > 0: two distinct real roots.",
            "If Î” = 0: exactly one real repeated root.",
            "If Î” < 0: two complex conjugate roots."
        ]
    }
}


class ToolResult:
    """Standardized tool output wrapper supporting error recovery."""
    def __init__(self, success: bool, data: Any, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def to_observation(self) -> str:
        if self.success:
            if isinstance(self.data, (dict, list)):
                return json.dumps(self.data, indent=2)
            return str(self.data)
        return f"ERROR [{self.error}]: {self.data}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }


# =========================================================================
# Tool 1: search_knowledge_base
# =========================================================================                                                                                     
 
def search_knowledge_base(query: str, subject: Optional[str] = None) -> ToolResult:
    """
    Improved educational knowledge search with keyword normalization,
    aliases, synonym matching, and subject filtering.
    """
    if not query or not query.strip():
        return ToolResult(
            success=False,
            data="Please provide a topic or question.",
            error="EmptyQueryError"
        )

    def normalize(text):
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split())

    clean_query = normalize(query)

    aliases = {
        "photosynthesis": [
            "how plants make food",
            "how plants produce food",
            "plant food production",
            "plants use sunlight"
        ],
        "mitochondria": [
            "powerhouse of the cell",
            "cell energy production",
            "atp production"
        ],
        "dna": [
            "genetic material",
            "hereditary material",
            "genetic information"
        ],
        "newton's second law": [
            "force mass acceleration",
            "law of acceleration",
            "f equals ma"
        ],
        "gravity": [
            "gravitational force",
            "free fall",
            "objects falling"
        ],
        "ohm's law": [
            "voltage current resistance",
            "electrical resistance"
        ],
        "acids and bases": [
            "ph scale",
            "acidic and alkaline",
            "neutralization"
        ],
        "pythagorean theorem": [
            "right triangle",
            "hypotenuse",
            "three sides of a right triangle"
        ],
        "quadratic formula": [
            "roots of quadratic equation",
            "solve quadratic equation",
            "discriminant"
        ]
    }

    stop_words = {
        "a", "an", "the", "and", "or", "is", "are",
        "what", "how", "do", "i", "to", "in", "of",
        "for", "with", "explain", "explanation",
        "analogy", "analogies", "please", "about",
        "definition", "define", "meaning", "concept",
        "simple", "words", "example", "examples"
    }

    query_words = set(clean_query.split()) - stop_words
    scored_results = []

    for key, item in KNOWLEDGE_BASE.items():

        if subject and subject.lower() not in ("all", "general", ""):
            if item["subject"] != subject.lower():
                continue

        searchable_text = normalize(
            key + " " +
            item["title"] + " " +
            item["definition"] + " " +
            item.get("formula", "") + " " +
            " ".join(item.get("key_facts", []))
        )

        searchable_words = set(searchable_text.split())

        score = len(query_words & searchable_words)

        # Direct word match against key or title
        norm_key = normalize(key)
        norm_title = normalize(item["title"])

        if clean_query in norm_key or norm_key in clean_query:
            score += 5

        if clean_query in norm_title or norm_title in clean_query:
            score += 5

        # Check if any non-stop query word matches the primary key or title words
        key_words = set(norm_key.split()) | set(norm_title.split())
        if query_words & key_words:
            score += 4

        if key in aliases:
            for alias in aliases[key]:
                alias_words = set(normalize(alias).split())
                if alias_words.issubset(set(clean_query.split())) or (query_words & alias_words):
                    score += 3
                    break

        if score >= 1:
            scored_results.append((score, item))

    scored_results.sort(key=lambda result: result[0], reverse=True)

    if scored_results:
        best_score = scored_results[0][0]

        matched_results = [
            {
                "concept": item["title"],
                "subject": item["subject"],
                "definition": item["definition"],
                "formula": item.get("formula", "N/A"),
                "key_facts": item.get("key_facts", [])
            }
            for score, item in scored_results
            if score == best_score
        ]

        return ToolResult(success=True, data=matched_results)

    available = ", ".join(
        f"'{key}'" for key in KNOWLEDGE_BASE.keys()
    )

    return ToolResult(
        success=False,
        data=(
            f"No relevant topic found for '{query}'. "
            f"Available topics: {available}"
        ),
        error="NotFoundError"
    )
#=========================================================================
# Tool 2: calculate_math_formula
# =========================================================================
def calculate_math_formula(expression: str) -> ToolResult:
    """
    Tool 2: Safe deterministic mathematical evaluator for arithmetic, formulas, and scientific calculations.
    Prevents LLM math hallucination.
    
    Supported functions: sqrt, sin, cos, tan, log, log10, abs, round, pow, pi, e.
    Powers use Python '**' operator (e.g. 5**2).
    
    Args:
        expression: Mathematical expression string (e.g. '(9.8 * 5**2) / 2', 'sqrt(144) + 25').
        
    Returns:
        ToolResult with computed numeric value or error diagnosis for self-correction.
    """
    if not expression or not expression.strip():
        return ToolResult(
            success=False,
            data="Math expression cannot be empty.",
            error="EmptyExpressionError"
        )

    clean_expr = expression.strip()

    # Self-Correction Diagnoser 1: Caret '^' used instead of '**'
    if "^" in clean_expr:
        suggested = clean_expr.replace("^", "**")
        return ToolResult(
            success=False,
            data=f"Invalid operator '^' detected in '{clean_expr}'. Use '**' for exponentiation. Suggested: '{suggested}'.",
            error="SyntaxError"
        )

    # Self-Correction Diagnoser 2: Implicit multiplication like '2(3)' or '5sqrt(4)' (allowing scientific notation like 3e8 or 1e-5)
    if re.search(r'\d+\s*\(', clean_expr) or re.search(r'\d+\s*(?!e[+-]?\d|E[+-]?\d)[a-df-zA-DF-Z]', clean_expr):
        return ToolResult(
            success=False,
            data=f"Implicit multiplication is not supported in '{clean_expr}'. Please use '*' explicitly (e.g. 2*(3) or 5*sqrt(4)).",
            error="SyntaxError"
        )

    # Safe math evaluation namespace
    safe_namespace = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "pow": pow,
        "max": max,
        "min": min
    }

    try:
        # Evaluate safely without builtins
        val = eval(clean_expr, {"__builtins__": None}, safe_namespace)
        
        # Round floating point noise if close to integer
        if isinstance(val, float):
            val = round(val, 6)
            if val.is_integer():
                val = int(val)
                
        return ToolResult(success=True, data=val)
        
    except ZeroDivisionError:
        return ToolResult(
            success=False,
            data=f"Mathematical error: Division by zero is undefined in '{clean_expr}'.",
            error="ZeroDivisionError"
        )
    except ValueError as ve:
        return ToolResult(
            success=False,
            data=f"Math domain error (e.g. square root of negative number) in '{clean_expr}': {str(ve)}",
            error="MathDomainError"
        )
    except SyntaxError as se:
        return ToolResult(
            success=False,
            data=f"Invalid syntax in math expression '{clean_expr}': {str(se)}",
            error="SyntaxError"
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=f"Evaluation failed for '{clean_expr}': {str(e)}",
            error="EvaluationError"
        )


# =========================================================================
# Tool 3: generate_quiz
# =========================================================================
QUIZ_DATABASE = {
    "photosynthesis": [
        {
            "id": 1,
            "question": "What primary pigment gives plant leaves their green color and absorbs sunlight for photosynthesis?",
            "options": ["A) Hemoglobin", "B) Chlorophyll", "C) Carotenoid", "D) Melanin"],
            "correct_answer": "B",
            "explanation": "Chlorophyll is the pigment located inside chloroplasts that traps light energy."
        },
        {
            "id": 2,
            "question": "Which gas is absorbed by plants from the atmosphere during photosynthesis?",
            "options": ["A) Oxygen", "B) Nitrogen", "C) Carbon Dioxide", "D) Methane"],
            "correct_answer": "C",
            "explanation": "Plants take in Carbon Dioxide (CO2) and release Oxygen (O2) into the atmosphere."
        },
        {
            "id": 3,
            "question": "What is the primary chemical energy sugar produced by photosynthesis?",
            "options": ["A) Glucose (C6H12O6)", "B) Sucrose", "C) Lactic Acid", "D) Fructose"],
            "correct_answer": "A",
            "explanation": "Photosynthesis synthesizes Glucose (C6H12O6) to fuel plant cellular processes."
        }
    ],
    "newton's second law": [
        {
            "id": 1,
            "question": "What is the mathematical formulation of Newton's Second Law of Motion?",
            "options": ["A) E = mc^2", "B) F = m * a", "C) V = I * R", "D) a^2 + b^2 = c^2"],
            "correct_answer": "B",
            "explanation": "Newton's Second Law defines net force as mass times acceleration (F = ma)."
        },
        {
            "id": 2,
            "question": "What is the SI unit of Force?",
            "options": ["A) Joule", "B) Watt", "C) Newton (N)", "D) Pascal"],
            "correct_answer": "C",
            "explanation": "The SI unit of force is the Newton (N), equivalent to 1 kg*m/s^2."
        }
    ],
    "pythagorean theorem": [
        {
            "id": 1,
            "question": "In a right-angled triangle with legs of length 3 and 4, what is the length of the hypotenuse?",
            "options": ["A) 5", "B) 7", "C) 6", "D) 12"],
            "correct_answer": "A",
            "explanation": "Using a^2 + b^2 = c^2: 3^2 + 4^2 = 9 + 16 = 25. Therefore c = sqrt(25) = 5."
        },
        {
            "id": 2,
            "question": "Which angle in a right triangle does the hypotenuse always oppose?",
            "options": ["A) 45 degrees", "B) 60 degrees", "C) 90 degrees", "D) 180 degrees"],
            "correct_answer": "C",
            "explanation": "The hypotenuse is the longest side and is always directly opposite the 90-degree right angle."
        }
    ],
    "gravity": [
        {
            "id": 1,
            "question": "What is the approximate acceleration due to gravity near Earth's surface?",
            "options": ["A) 3.14 m/s^2", "B) 9.8 m/s^2", "C) 15.0 m/s^2", "D) 98 m/s^2"],
            "correct_answer": "B",
            "explanation": "Acceleration due to gravity on Earth is standardized at approximately 9.8 m/s^2."
        },
        {
            "id": 2,
            "question": "In a complete vacuum with no air resistance, which object falls faster?",
            "options": ["A) A 10kg bowling ball", "B) A 1g feather", "C) Both fall at identical rates", "D) Neither falls"],
            "correct_answer": "C",
            "explanation": "Without air resistance, gravitational acceleration is identical for all objects regardless of mass."
        }
    ]
}


def generate_quiz(topic: str, num_questions: int = 3, difficulty: str = "medium") -> ToolResult:
    """
    Tool 3: Generates structured multiple-choice questions (MCQs) with answer keys and explanations.
    
    Args:
        topic: The academic topic for the quiz (e.g. 'Photosynthesis', 'Newton's second law', 'Pythagorean Theorem').
        num_questions: Number of questions (1 to 5).
        difficulty: 'easy', 'medium', or 'hard'.
        
    Returns:
        ToolResult with list of structured MCQs containing question, options, correct_answer, and explanation.
    """
    if not topic or not topic.strip():
        return ToolResult(success=False, data="Topic name cannot be empty.", error="EmptyTopicError")

    if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 5:
        return ToolResult(
            success=False,
            data="num_questions must be an integer between 1 and 5.",
            error="ValidationError"
        )

    clean_topic = topic.lower().strip()
    
    # Check pre-curated question bank
    for key, q_list in QUIZ_DATABASE.items():
        if key in clean_topic or clean_topic in key:
            selected = q_list[:num_questions]
            return ToolResult(success=True, data={
                "topic": topic,
                "difficulty": difficulty,
                "question_count": len(selected),
                "questions": selected
            })

    # Procedural educational quiz generator for any generic topic
    procedural_questions = [
        {
            "id": 1,
            "question": f"Which of the following best defines the primary principle of {topic}?",
            "options": [
                f"A) A foundational concept governing {topic}",
                "B) An unrelated phenomenon in astronomy",
                "C) A historical event from antiquity",
                "D) None of the above"
            ],
            "correct_answer": "A",
            "explanation": f"Option A reflects the core definition of {topic}."
        },
        {
            "id": 2,
            "question": f"What is a standard application or consequence of {topic}?",
            "options": [
                "A) It has no practical applications",
                f"B) It is used to model, analyze, and solve problems in {topic}",
                "C) It contradicts established scientific methods",
                "D) It only applies at absolute zero temperature"
            ],
            "correct_answer": "B",
            "explanation": f"{topic} provides theoretical and practical models for analysis."
        }
    ][:num_questions]

    return ToolResult(success=True, data={
        "topic": topic,
        "difficulty": difficulty,
        "question_count": len(procedural_questions),
        "questions": procedural_questions
    })


# =========================================================================
# Tool 4: save_study_notes
# =========================================================================
def save_study_notes(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    storage_dir: str = "storage/notes"
) -> ToolResult:
    """
    Tool 4: Persists structured study notes or formula sheets into user storage.
    
    SAFETY CLASSIFICATION: High-Impact / Sensitive action.
    Requires human-in-the-loop (HITL) confirmation before execution.
    
    Args:
        title: Note title (e.g. 'Kinematics_Falling_Distance').
        content: Markdown formatted content of the study note.
        tags: Categorization tags (e.g. ['physics', 'formulas']).
        storage_dir: Destination folder path (defaults to 'storage/notes').
        
    Returns:
        ToolResult with saved file path, size, and metadata.
    """
    if not title or not title.strip():
        return ToolResult(success=False, data="Note 'title' cannot be empty.", error="MissingTitleError")
        
    if not content or not content.strip():
        return ToolResult(success=False, data="Note 'content' cannot be empty.", error="MissingContentError")

    os.makedirs(storage_dir, exist_ok=True)
    
    # Sanitize title for filesystem safety
    safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", " ")).strip()
    safe_title = safe_title.replace(" ", "_") or "study_notes"
    
    file_path = os.path.join(storage_dir, f"{safe_title}.md")

    # Build clean markdown note with metadata header
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    clean_tags = tags or ["general"]
    
    header = (
        f"# {title}\n\n"
        f"**Date Created:** {timestamp}  \n"
        f"**Tags:** {', '.join(clean_tags)}  \n"
        f"**Source:** AI Study Buddy Agent  \n\n"
        f"---\n\n"
    )
    full_document = header + content.strip() + "\n"

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_document)
            
        return ToolResult(success=True, data={
            "saved_file": file_path,
            "title": title,
            "tags": clean_tags,
            "bytes_written": len(full_document.encode("utf-8")),
            "timestamp": timestamp
        })
    except Exception as e:
        return ToolResult(
            success=False,
            data=f"Failed to write note file '{file_path}': {str(e)}",
            error="IOError"
        )


# =========================================================================
# TOOL REGISTRY (Metadata for Agent & LLM Schema)
# =========================================================================
TOOL_REGISTRY = {
    "search_knowledge_base": {
        "func": search_knowledge_base,
        "description": "Searches curated educational materials, definitions, and facts for science, math, and general subjects.",
        "parameters": {
            "query": "string (search terms)",
            "subject": "string (optional: 'physics', 'chemistry', 'biology', 'math', 'general')"
        },
        "requires_confirmation": False
    },
    "calculate_math_formula": {
        "func": calculate_math_formula,
        "description": "Safely calculates mathematical expressions, formulas, and conversions without hallucinations.",
        "parameters": {
            "expression": "string (math expression, e.g. '(9.8 * 5**2) / 2')"
        },
        "requires_confirmation": False
    },
    "generate_quiz": {
        "func": generate_quiz,
        "description": "Generates MCQs only when the student explicitly asks for a quiz, test, practice questions, or MCQs. Do NOT call this tool for ordinary explanations, definitions, or homework answers unless quiz questions are requested.",
        "parameters": {
            "topic": "string (quiz topic)",
            "num_questions": "integer (1 to 5)",
            "difficulty": "string ('easy', 'medium', 'hard')"
        },
        "requires_confirmation": False
    },
    "save_study_notes": {
        "func": save_study_notes,
        "description": "Persists structured study notes or formula sheets into local storage. Requires human confirmation.",
        "parameters": {
            "title": "string (note title)",
            "content": "string (markdown body)",
            "tags": "list of strings (categories)"
        },
        "requires_confirmation": True
    }
}

