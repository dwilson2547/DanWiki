"""
Code-focused tagging prompt for technical documentation.

Best for: API docs, code examples, programming tutorials.
Focus: Programming languages, frameworks, patterns, technical concepts.
"""

SYSTEM_PROMPT = """You are a technical documentation analyzer specializing in code and programming content.

Your expertise includes:
- Programming languages and frameworks
- Software architecture and design patterns
- Development tools and methodologies
- Technical concepts and algorithms

Generate tags that help developers find and categorize technical content.

Guidelines:
- Identify programming languages used
- Recognize frameworks, libraries, and tools
- Detect design patterns and architectures
- Tag API types (REST, GraphQL, gRPC, etc.)
- Note development practices (testing, CI/CD, etc.)
- Use standard technical terminology
- Prefer existing tags to maintain consistency"""

USER_PROMPT_TEMPLATE = """Analyze this technical documentation page:

**Title:** {title}
**Location:** {breadcrumbs}

**Content:**
{content}

**Existing Technical Tags:**
{existing_tags}

Focus your analysis on:
1. Programming languages mentioned or used in examples
2. Frameworks, libraries, and tools discussed
3. Software patterns and architectures
4. API types and protocols
5. Development practices and methodologies

Return a JSON array with technical tags:
[
  {{
    "name": "tag-name",
    "confidence": 0.92,
    "is_new": false,
    "rationale": "Specific reason based on code/technical content",
    "category": "language|framework|pattern|tool|concept|practice",
    "matched_existing_tag": "existing-tag" or null
  }}
]

Return ONLY the JSON array. Ensure the JSON is valid."""


def format_prompt(
    title: str,
    content: str,
    existing_tags: list[str],
    breadcrumbs: list[str] | None = None
) -> str:
    """Format the user prompt with provided context."""
    breadcrumbs_str = " > ".join(breadcrumbs) if breadcrumbs else "Root"
    existing_tags_str = ", ".join(existing_tags) if existing_tags else "No existing tags"
    
    # Extract code blocks for emphasis
    max_content_chars = 4000
    if len(content) > max_content_chars:
        # Try to preserve code blocks if possible
        keep = max_content_chars // 2
        content = content[:keep] + "\n[... content truncated ...]\n" + content[-keep:]
    
    return USER_PROMPT_TEMPLATE.format(
        title=title,
        breadcrumbs=breadcrumbs_str,
        content=content,
        existing_tags=existing_tags_str
    )
