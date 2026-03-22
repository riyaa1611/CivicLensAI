"""LLM-based policy classifier: generates impact tags."""
import logging
import json
from typing import List
import httpx

from ..config.settings import settings

logger = logging.getLogger(__name__)

VALID_TAGS = [
    "citizens", "startups", "students", "taxpayers",
    "healthcare", "privacy", "technology", "business",
    "education", "finance",
]

CLASSIFY_PROMPT = """You are a civic policy classifier. Analyze the following policy/document and select the most relevant impact tags.

Available tags: {tags}

Policy title: {title}
Content: {content}

Return ONLY a JSON array of the most relevant tags (2-5 tags). Example: ["citizens", "taxpayers", "finance"]
Return only the JSON array, no other text."""


async def classify_policy(content: str, title: str = "") -> List[str]:
    """
    Classify a policy document and return relevant impact tags.
    Falls back to basic keyword matching if LLM fails.
    """
    max_chars = 3000
    truncated = content[:max_chars] if len(content) > max_chars else content

    prompt = CLASSIFY_PROMPT.format(
        tags=", ".join(VALID_TAGS),
        title=title,
        content=truncated,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://civiclens.app",
                    "X-Title": "CivicLens",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a policy classifier. Return only valid JSON arrays.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            llm_content = data["choices"][0]["message"].get("content")
            if llm_content is None:
                raise ValueError("LLM returned null content")
            raw = llm_content.strip()

            # Strip markdown if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            tags = json.loads(raw)
            # Filter to only valid tags
            return [t for t in tags if t in VALID_TAGS]

    except Exception as e:
        logger.warning(f"LLM classification failed for '{title}': {e}")
        return _keyword_classify(content + " " + title)


def _keyword_classify(text: str) -> List[str]:
    """Fallback keyword-based classification."""
    text_lower = text.lower()
    tags = []
    keyword_map = {
        "citizens": ["citizen", "public", "people", "individual", "person"],
        "startups": ["startup", "entrepreneur", "msme", "sme", "small business", "incubat"],
        "students": ["student", "education", "school", "college", "university", "scholarship"],
        "taxpayers": ["tax", "gst", "income tax", "filing", "itr", "revenue"],
        "healthcare": ["health", "medical", "hospital", "medicine", "patient", "pharma"],
        "privacy": ["privacy", "data protection", "personal data", "surveillance", "consent"],
        "technology": ["technology", "digital", "software", "ai", "cyber", "internet", "tech"],
        "business": ["business", "commerce", "trade", "industry", "corporate", "company"],
        "education": ["education", "learning", "curriculum", "teacher", "school", "academic"],
        "finance": ["finance", "bank", "loan", "credit", "insurance", "investment", "rbi"],
    }
    for tag, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags[:5] if tags else ["citizens"]
