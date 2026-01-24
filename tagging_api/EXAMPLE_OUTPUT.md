# Example Test Output

This shows what you can expect from running the test suite.

## Console Output

```
🚀 Starting Test Suite
   Test cases: 8
   Prompt templates: detailed, quick, technical, general
   Total tests: 32
   Output directory: test_results/20260121_045900

📋 Test Case: Flask Tutorial
    ✅ detailed      - 8 tags
    ✅ quick         - 6 tags
    ✅ technical     - 9 tags
    ✅ general       - 7 tags

📋 Test Case: Database Troubleshooting
    ✅ detailed      - 7 tags
    ✅ quick         - 5 tags
    ✅ technical     - 8 tags
    ✅ general       - 6 tags

... (continues for all test cases)

✨ All tests completed!

💾 Raw results saved: test_results/20260121_045900/raw_results.json
📊 Markdown report saved: test_results/20260121_045900/report.md

============================================================
📊 TEST SUMMARY
============================================================
Total tests:      32
Successful:       32 (100.0%)
Failed:           0
Test cases:       8
Templates:        detailed, quick, technical, general
Output directory: test_results/20260121_045900
============================================================
```

## Report Sample (report.md excerpt)

```markdown
# Tagging API Test Results

**Generated:** 2026-01-21 04:59:00

**API Endpoint:** http://localhost:8002

## Summary

- **Total Tests:** 32
- **Successful:** 32 (100.0%)
- **Failed:** 0
- **Test Cases:** 8
- **Prompt Templates:** detailed, quick, technical, general

## Test Results by Case

### Flask Tutorial

**Title:** Getting Started with Flask

**Description:** Beginner tutorial on Flask web framework

**Fixture:** `flask_tutorial.md`

**Expected Tag Categories:** tutorial, beginner, flask, routing, templates

#### Prompt Template: `detailed`

**Performance:**
- Processing time: 2834 ms
- Tags generated: 8
- New tags: 5
- Existing tags matched: 3
- Content tokens: 485

**Generated Tags:**

| Tag | Confidence | New? | Category | Rationale |
|-----|------------|------|----------|-----------|
| python | 0.95 | 🔗 | technology | Content focuses on Python web framework... |
| flask | 0.92 | ✨ | technology | Main topic is Flask framework... |
| web-development | 0.88 | 🔗 | domain | Tutorial covers web application development... |
| tutorial | 0.90 | ✨ | type | Content structured as step-by-step tutorial... |
| beginner | 0.85 | ✨ | level | Starts with installation and basic concepts... |
| routing | 0.82 | ✨ | concept | Explains URL routing patterns... |
| templates | 0.78 | ✨ | concept | Covers Jinja2 templating... |
| backend | 0.87 | 🔗 | domain | Server-side web development... |

---

#### Prompt Template: `quick`

**Performance:**
- Processing time: 1456 ms
- Tags generated: 6
- New tags: 3
- Existing tags matched: 3
- Content tokens: 485

**Generated Tags:**

| Tag | Confidence | New? | Category | Rationale |
|-----|------------|------|----------|-----------|
| python | 0.93 | 🔗 | technology | Flask is a Python framework... |
| flask | 0.90 | ✨ | technology | Core topic of the tutorial... |
| web-development | 0.86 | 🔗 | domain | Web framework tutorial... |
| tutorial | 0.88 | ✨ | type | Tutorial format... |
| beginner-friendly | 0.84 | ✨ | level | Introductory content... |
| backend | 0.85 | 🔗 | domain | Backend web development... |

---

## Template Comparison

### Flask Tutorial

| Tag | detailed | quick | technical | general |
|-----|----------|-------|-----------|---------|
| backend | 0.87 | 0.85 | 0.89 | 0.86 |
| beginner | 0.85 | - | - | 0.83 |
| beginner-friendly | - | 0.84 | - | - |
| flask | 0.92 | 0.90 | 0.94 | 0.91 |
| python | 0.95 | 0.93 | 0.96 | 0.94 |
| routing | 0.82 | - | 0.84 | 0.80 |
| templates | 0.78 | - | 0.81 | - |
| tutorial | 0.90 | 0.88 | 0.87 | 0.89 |
| web-development | 0.88 | 0.86 | 0.90 | 0.87 |
| wsgi | - | - | 0.79 | - |
```

## Raw JSON Sample (raw_results.json excerpt)

```json
[
  {
    "success": true,
    "status_code": 200,
    "data": {
      "tags": [
        {
          "name": "python",
          "confidence": 0.95,
          "is_new": false,
          "rationale": "Content focuses on Python web framework Flask",
          "category": "technology",
          "matched_existing_tag": "python"
        },
        {
          "name": "flask",
          "confidence": 0.92,
          "is_new": true,
          "rationale": "Main topic is Flask web framework",
          "category": "technology",
          "matched_existing_tag": null
        }
      ],
      "model_name": "google/gemma-2-2b-it",
      "model_version": "1.0",
      "processing_time_ms": 2834.5,
      "stats": {
        "new_tags_suggested": 5,
        "existing_tags_matched": 3,
        "total_tags": 8,
        "content_tokens": 485
      }
    },
    "test_case": "Flask Tutorial",
    "prompt_template": "detailed",
    "fixture": "flask_tutorial.md",
    "title": "Getting Started with Flask",
    "description": "Beginner tutorial on Flask web framework",
    "expected_categories": ["tutorial", "beginner", "flask", "routing", "templates"],
    "timestamp": "2026-01-21T04:59:05.123456"
  }
]
```

## What to Look For

### Good Signs ✅
- Relevant tags that accurately describe content
- Reasonable confidence scores (0.7-0.95 for relevant tags)
- Appropriate balance of new vs. existing tag matching
- Consistent results across similar content
- Processing times under 5 seconds

### Warning Signs ⚠️
- Generic tags (e.g., "content", "information", "data")
- Very low confidence (<0.5) for obviously relevant tags
- Missing obvious tags
- Too many irrelevant tags
- Huge variance in tag count across templates for same content

### Action Items
- Compare template outputs to find best default
- Identify content types that need specialized prompts
- Adjust confidence thresholds
- Refine prompt templates based on patterns
- Add edge cases as new test fixtures
