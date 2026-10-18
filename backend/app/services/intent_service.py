import re
from enum import Enum

class QueryIntent(str, Enum):
    QUESTION = "QUESTION"
    SUMMARY = "SUMMARY"
    UNKNOWN = "UNKNOWN"

class IntentClassifier:
    SUMMARY_PATTERNS = [
        r"^summarize(\s+this|\s+the\s+document|\s+everything|\s+all|\s+it)?$",
        r"^summarise(\s+this|\s+the\s+document|\s+everything|\s+all|\s+it)?$",
        r"^(give\s+me|provide|show)(\s+a|\s+the)?\s+(summary|overview|key\s+points|main\s+points|important\s+information)",
        r"^what\s+is\s+this\s+(document|file|contract|agreement|bill|statement)\s+about\??$",
        r"^explain\s+this\s+(document|file|contract|agreement|bill|statement)\??$",
        r"^give\s+me\s+an\s+overview\??$",
        r"^(can\s+you\s+)?summarize\s+(this|the)\s+(document|file|contract|agreement|bill)\??$",
        r"^(can\s+you\s+)?summarise\s+(this|the)\s+(document|file|contract|agreement|bill)\??$",
        r"^(brief|summary|key\s+takeaways|takeaways)\??$",
    ]

    @classmethod
    def classify(cls, query: str) -> QueryIntent:
        q_clean = query.strip().lower()
        # Remove trailing punctuation
        q_clean = re.sub(r"[?!.]+$", "", q_clean).strip()

        # Check summary patterns
        for pattern in cls.SUMMARY_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                return QueryIntent.SUMMARY

        # If it explicitly contains words like "summarize the document" or "give me key points"
        if ("summarize" in q_clean or "summarise" in q_clean) and ("document" in q_clean or "this" in q_clean or "all" in q_clean):
            return QueryIntent.SUMMARY

        if "key points" in q_clean or "overview of this document" in q_clean or "what is this document about" in q_clean:
            return QueryIntent.SUMMARY

        # General questions
        if any(q_clean.startswith(w) for w in ["what", "who", "when", "where", "how", "why", "which", "is", "are", "does", "do", "did", "can", "will"]):
            return QueryIntent.QUESTION

        if len(q_clean) > 0:
            return QueryIntent.QUESTION

        return QueryIntent.UNKNOWN
