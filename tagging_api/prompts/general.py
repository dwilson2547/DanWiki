"""
General-purpose tagging prompt with balanced approach.

Best for: Mixed content, general wikis, when unsure of content type.
Focus: Balanced analysis covering multiple dimensions.
"""

SYSTEM_PROMPT = """You are a versatile wiki content analyzer that generates relevant tags for documentation.

Your task is to provide balanced tagging that covers:
- Main topics and subject matter
- Content type (tutorial, guide, reference, troubleshooting, etc.)
- Technical vs. conceptual content
- Target audience level (beginner, intermediate, advanced)
- Related domains and applications

Generate tags that help users discover, organize, and filter content effectively."""

USER_PROMPT_TEMPLATE = """Analyze this wiki page and suggest appropriate tags.

**Title:** {title}
**Context:** {breadcrumbs}

**Content:**
{content}

**Existing Tags:**
{existing_tags}

Provide tags covering these dimensions:
- **Topic**: What is this page about?
- **Type**: Tutorial, guide, reference, how-to, troubleshooting, etc.
- **Domain**: Application area or field
- **Level**: Beginner, intermediate, advanced (if applicable)
- **Technology**: Specific tools, frameworks, or technologies (if applicable)

Prefer existing tags when semantically similar. Suggest new tags when needed to accurately describe the content.

Return JSON array:
[
  {{
    "name": "tag-name",
    "confidence": 0.88,
    "is_new": true,
    "rationale": "Why this tag fits",
    "category": "topic|type|domain|level|technology",
    "matched_existing_tag": null
  }}
]

Return ONLY the JSON array, no other text."""


def format_prompt(
    title: str,
    content: str,
    existing_tags: list[str],
    breadcrumbs: list[str] | None = None
) -> str:
    """Format the user prompt with provided context."""
    breadcrumbs_str = " > ".join(breadcrumbs) if breadcrumbs else "Top level"
    existing_tags_str = ", ".join(existing_tags) if existing_tags else "None"
    
    max_content_chars = 3500
    if len(content) > max_content_chars:
        keep = max_content_chars // 2
        content = content[:keep] + "\n\n[... middle section omitted ...]\n\n" + content[-keep:]
    
    return USER_PROMPT_TEMPLATE.format(
        title=title,
        breadcrumbs=breadcrumbs_str,
        content=content,
        existing_tags=existing_tags_str
    )
