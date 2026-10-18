"""Repository data paths resolved from the package location."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEXICONS = REPO_ROOT / "lexicons"
GLOSSARY = REPO_ROOT / "glossary"

RENTAL_TOPICS = LEXICONS / "rental_topics.yaml"
JURISDICTION_TOPICS = LEXICONS / "jurisdiction_topics.yaml"
ESCALATION_TEMPLATES = LEXICONS / "escalation_templates.yaml"
RENTAL_TERMS = GLOSSARY / "rental_terms.yaml"
