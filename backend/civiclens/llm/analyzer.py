"""LLM-based policy analyzer: generates summaries and key clauses."""
import logging
from typing import List
import httpx

from ..config.settings import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a civic intelligence assistant. Analyze the following government policy or legal document.

Provide:
1. A concise 3-point summary explaining the key provisions (write as plain bullet points)
2. Up to 5 key clauses or important sections

Policy/Document:
{content}

Respond in this exact JSON format:
{{
  "summary": ["Point 1", "Point 2", "Point 3"],
  "key_clauses": ["Clause 1", "Clause 2", "Clause 3"]
}}

Return only valid JSON, no markdown code blocks."""


async def analyze_policy(content: str, title: str = "") -> dict:
    """
    Generate summary and key clauses for a policy document using LLM.

    Returns:
        dict with keys: summary (str), key_clauses (list[str])
    """
    # Truncate very long content to avoid token limits
    max_chars = 8000
    truncated = content[:max_chars] if len(content) > max_chars else content

    prompt = SUMMARY_PROMPT.format(content=truncated)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
                            "content": "You are CivicLens, an AI civic intelligence assistant. Always respond with valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            llm_content = data["choices"][0]["message"].get("content")
            if llm_content is None:
                raise ValueError("LLM returned null content")
            raw = llm_content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            import json
            parsed = json.loads(raw)
            summary_points = parsed.get("summary", [])
            key_clauses = parsed.get("key_clauses", [])

            summary = "\n".join(
                f"• {pt}" for pt in summary_points
            ) if isinstance(summary_points, list) else str(summary_points)

            return {
                "summary": summary,
                "key_clauses": key_clauses if isinstance(key_clauses, list) else [],
            }

    except Exception as e:
        logger.warning(f"LLM analysis failed for '{title}': {e}")
        return {
            "summary": "Summary not available.",
            "key_clauses": [],
        }
