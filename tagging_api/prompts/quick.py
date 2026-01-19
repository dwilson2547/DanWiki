"""
Quick tagging prompt for fast inference.

Best for: Short pages, simple content, batch processing.
Focus: Speed over detailed analysis, fewer instructions.
"""

SYSTEM_PROMPT = """You are a wiki tagging assistant. Generate 3-7 relevant tags for documentation pages.

Rules:
- Tags are lowercase with hyphens (e.g., "web-dev")
- Prefer existing tags to avoid duplicates
- Return JSON only"""

USER_PROMPT_TEMPLATE = """Title: {title}
Path: {breadcrumbs}

Content:
{content}

Existing tags: {existing_tags}

Generate tags as JSON array:
[{{"name": "tag", "confidence": 0.9, "is_new": true, "rationale": "why", "category": "type", "matched_existing_tag": null}}]"""


def format_prompt(
    title: str,
    content: str,
    existing_tags: list[str],
    breadcrumbs: list[str] | None = None
) -> str:
    """Format the user prompt with provided context."""
    breadcrumbs_str = " > ".join(breadcrumbs) if breadcrumbs else "Root"
    existing_tags_str = ", ".join(existing_tags[:20]) if existing_tags else "None"
    
    # More aggressive truncation for quick mode
    max_content_chars = 2000
    if len(content) > max_content_chars:
        content = content[:max_content_chars] + "\n[...]"
    
    return USER_PROMPT_TEMPLATE.format(
        title=title,
        breadcrumbs=breadcrumbs_str,
        content=content,
        existing_tags=existing_tags_str
    )
