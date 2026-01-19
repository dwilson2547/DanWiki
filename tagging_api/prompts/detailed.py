"""
Detailed tagging prompt with comprehensive analysis.

Best for: Complex pages, technical documentation, tutorials.
Focus: Deep content analysis with rationale for each tag.
"""

SYSTEM_PROMPT = """You are a wiki content analyzer that generates relevant tags for documentation pages.

Your task is to analyze the provided content and suggest appropriate tags that:
- Accurately describe the content's topics and themes
- Include both specific and general categories
- Consider technical concepts, frameworks, and methodologies
- Identify the content type (tutorial, reference, guide, etc.)
- Assess difficulty level when applicable

Guidelines:
- Generate 5-10 tags maximum (prioritize quality over quantity)
- Tags should be concise (1-3 words)
- Use lowercase with hyphens (e.g., "machine-learning", "rest-api")
- Return tags in order of relevance (highest confidence first)
- Prefer existing tags when semantically similar to avoid duplication
- Provide clear rationale for each suggestion"""

USER_PROMPT_TEMPLATE = """Analyze this wiki page and suggest relevant tags.

**Page Title:** {title}

**Wiki Context:** {breadcrumbs}

**Content:**
{content}

**Existing Tags in Wiki:**
{existing_tags}

Based on this information:
1. Identify the main topics, technologies, and concepts
2. Consider the content type and difficulty level
3. Match against existing tags when appropriate (use semantic similarity, not just exact match)
4. Suggest new tags only when existing tags don't cover the topic

Return a JSON array with this exact structure:
[
  {{
    "name": "tag-name",
    "confidence": 0.95,
    "is_new": false,
    "rationale": "Brief explanation of why this tag is relevant",
    "category": "technology|concept|domain|level|type|platform",
    "matched_existing_tag": "existing-tag-name" or null
  }}
]

Return ONLY the JSON array, no additional text."""


def format_prompt(
    title: str,
    content: str,
    existing_tags: list[str],
    breadcrumbs: list[str] | None = None
) -> str:
    """Format the user prompt with provided context."""
    breadcrumbs_str = " > ".join(breadcrumbs) if breadcrumbs else "Root level"
    existing_tags_str = ", ".join(existing_tags) if existing_tags else "None yet"
    
    # Truncate content if too long (preserve beginning and end)
    max_content_chars = 4000
    if len(content) > max_content_chars:
        keep = max_content_chars // 2
        content = content[:keep] + "\n\n[... content truncated ...]\n\n" + content[-keep:]
    
    return USER_PROMPT_TEMPLATE.format(
        title=title,
        breadcrumbs=breadcrumbs_str,
        content=content,
        existing_tags=existing_tags_str
    )
