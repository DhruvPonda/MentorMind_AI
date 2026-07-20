import os
from typing import Tuple

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ─── Topic Taxonomy ──────────────────────────────────────────────

TOPIC_TAXONOMY = {
    "recursion": [
        "recursion", "recursive", "factorial", "base case",
        "call stack", "stack overflow",
    ],
    "sorting algorithms": [
        "sort", "sorting", "bubble sort", "merge sort",
        "quick sort", "insertion sort", "selection sort",
    ],
    "data structures": [
        "array", "linked list", "stack", "queue",
        "tree", "graph", "hash table", "heap",
    ],
    "object-oriented programming": [
        "class", "object", "inheritance", "polymorphism",
        "encapsulation", "abstraction", "oop",
    ],
    "probability": [
        "probability", "chance", "event", "random",
        "likelihood", "bayes", "conditional probability",
    ],
    "statistics": [
        "mean", "median", "mode", "standard deviation",
        "variance", "distribution", "hypothesis",
    ],
    "calculus": [
        "derivative", "integral", "differentiation",
        "integration", "limit", "calculus",
    ],
    "linear algebra": [
        "matrix", "vector", "eigenvalue", "determinant",
        "linear transformation", "linear algebra",
    ],
    "newton's laws": [
        "newton", "force", "mass", "acceleration",
        "inertia", "action reaction", "f=ma",
    ],
    "thermodynamics": [
        "heat", "temperature", "entropy",
        "thermodynamics", "thermal", "energy transfer",
    ],
    "electromagnetism": [
        "electric", "magnetic", "electromagnetic",
        "voltage", "current", "resistance", "ohm",
    ],
    "optics": [
        "light", "reflection", "refraction",
        "lens", "mirror", "optics", "wavelength",
    ],
    "chemistry basics": [
        "atom", "molecule", "element", "compound",
        "chemical reaction", "periodic table",
    ],
    "organic chemistry": [
        "organic", "carbon", "hydrocarbon",
        "functional group", "isomer",
    ],
    "biology basics": [
        "cell", "dna", "rna", "protein",
        "gene", "chromosome", "mitosis", "meiosis",
    ],
    "ecology": [
        "ecosystem", "food chain", "biodiversity",
        "habitat", "species", "ecology",
    ],
    "photosynthesis": [
        "photosynthesis", "chlorophyll", "chloroplast",
        "light reaction", "calvin cycle",
    ],
    "evolution": [
        "evolution", "natural selection", "adaptation",
        "darwin", "mutation", "speciation",
    ],
    "python programming": [
        "python", "pip", "def", "import",
        "list comprehension", "dictionary", "tuple",
    ],
    "web development": [
        "html", "css", "javascript", "react",
        "api", "http", "web", "frontend", "backend",
    ],
    "machine learning": [
        "machine learning", "neural network", "deep learning",
        "training", "model", "classification", "regression",
    ],
    "databases": [
        "sql", "database", "query", "table",
        "join", "index", "nosql", "relational",
    ],
    "algorithms": [
        "algorithm", "time complexity", "space complexity",
        "big o", "dynamic programming", "greedy",
    ],
    "general": [],  # Fallback topic
}

CONFIDENCE_THRESHOLD = 0.3


def _keyword_match(text: str) -> Tuple[str, float]:
    """Match text against the topic taxonomy using keyword frequency."""
    text_lower = text.lower()
    scores = {}

    for topic, keywords in TOPIC_TAXONOMY.items():
        if topic == "general" or not keywords:
            continue
        match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if match_count > 0:
            scores[topic] = match_count / len(keywords)

    if not scores:
        return "general", 0.0

    best_topic = max(scores, key=scores.get)
    return best_topic, scores[best_topic]


def _llm_classify(question: str, answer: str) -> str:
    """Fallback: use LLM to classify the topic when keyword confidence is low."""
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        topics_list = ", ".join(
            t for t in TOPIC_TAXONOMY.keys() if t != "general"
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a topic classifier. Given a student question "
                        f"and tutor answer, classify the topic into exactly ONE "
                        f"of these categories: {topics_list}, general. "
                        f"Respond with ONLY the topic name, nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nAnswer: {answer}",
                },
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_tokens=20,
        )

        detected = response.choices[0].message.content.strip().lower()

        # Exact match
        if detected in TOPIC_TAXONOMY:
            return detected
        # Fuzzy match
        for topic in TOPIC_TAXONOMY:
            if topic in detected or detected in topic:
                return topic
        return "general"
    except Exception:
        return "general"


def detect_topic(question: str, answer: str) -> str:
    """
    Hybrid topic detection:
    1. Try keyword matching first (fast, free).
    2. Fall back to LLM classification when confidence is below threshold.
    """
    combined_text = f"{question} {answer}"
    topic, confidence = _keyword_match(combined_text)

    if confidence >= CONFIDENCE_THRESHOLD:
        return topic

    # Low confidence → ask the LLM
    return _llm_classify(question, answer)
