# Phase 3: Cluster-Based Tag Generation

**Timeline:** Week 2
**Goal:** Generate tags for clusters using LLM analysis of representative pages

## Overview

This phase implements the core value proposition: using an LLM to analyze representative pages and generate tags that apply to entire clusters. Quality of prompt engineering directly determines tag quality.

## Prompt Engineering

### Cluster Tagging Prompt

```python
CLUSTER_TAGGING_PROMPT = """You are analyzing a cluster of similar wiki pages. Based on the representative pages below, generate tags that apply to ALL pages in this cluster.

Cluster Info:
- Cluster ID: {cluster_id}
- Pages in cluster: {page_count}
- Representative pages: {representative_count}

Representative Pages:
{page_contents}

Existing Wiki Tags: {existing_tags}

Generate 5-8 tags that capture the common themes across these pages. Focus on:
1. Shared technologies/frameworks
2. Common concepts/topics
3. Content type (tutorial, reference, guide)
4. Difficulty level if consistent

Requirements:
- Tags must apply to ALL pages in cluster, not just one
- Prefer existing wiki tags when semantically similar
- Use lowercase, hyphenated format
- Return as JSON array

Expected format:
[
  {
    "name": "tag-name",
    "confidence": 0.85,
    "rationale": "Brief explanation",
    "category": "technology|concept|type|level"
  }
]
"""
```

### Prompt Design Principles

1. **Clear constraint:** Tags must apply to ALL pages
2. **Context provided:** Cluster size, representative count
3. **Existing tag awareness:** Prevent synonym proliferation
4. **Structured output:** JSON for reliable parsing
5. **Rationale requirement:** Forces model to explain reasoning

## Implementation Details

### 1. Prompt Template Module

**Location:** `tagging_api/prompts.py`

**Constants:**
- `CLUSTER_TAGGING_PROMPT` - Main template
- `EXISTING_TAGS_FORMAT` - How to format existing tags list
- `PAGE_CONTENT_FORMAT` - How to format representative pages

### 2. Tag Generation Function

**Location:** `tagging_api/tag_generator.py`

**Function:** `generate_cluster_tags(cluster_content, existing_tags, model)`

**Parameters:**
- Temperature: 0.2 (lower for consistency)
- Max tokens: 500 (enough for 8 tags with rationales)
- Top-p: 0.9

**Process:**
1. Format prompt with cluster data
2. Call LLM
3. Parse JSON response
4. Validate tag structure
5. Filter by confidence threshold
6. Return tag list

### 3. Response Parsing

**Validation checks:**
- Valid JSON structure
- All required fields present (name, confidence, rationale, category)
- Confidence in valid range (0.0-1.0)
- Tag name format (lowercase, hyphenated)
- Category is valid enum value

**Error handling:**
- Retry on parse failure (up to 3 times)
- Log unparseable responses
- Return empty list on total failure
- Track parsing success rate

### 4. Cluster Tag Caching

**Storage:** Add JSON column to `page_tag_clusters` table

```sql
ALTER TABLE page_tag_clusters ADD COLUMN cluster_tags JSONB;
CREATE INDEX idx_page_tag_clusters_tags ON page_tag_clusters USING GIN(cluster_tags);
```

**Cache invalidation:** When cluster is re-computed

### 5. API Endpoint

**Route:** `POST /analyze/cluster`

**Request:**
```json
{
  "cluster_id": 123,
  "wiki_id": 1,
  "cluster_label": 5,
  "options": {
    "temperature": 0.2,
    "max_tags": 8
  }
}
```

**Response:**
```json
{
  "cluster_id": 123,
  "tags": [
    {
      "name": "python",
      "confidence": 0.92,
      "rationale": "All pages discuss Python programming",
      "category": "technology",
      "is_existing": true
    }
  ],
  "model_name": "gemma-2-9b-it",
  "processing_time_ms": 1234
}
```

## Validation Criteria

### Functional Tests
- Generate tags for 10 diverse clusters
- JSON parsing succeeds 95%+ of the time
- Tag generation completes in < 5 seconds per cluster

### Quality Metrics
- 80%+ of cluster tags are relevant to all member pages (human eval)
- Human evaluation on sample of 50 pages across 10 clusters
- Compare cluster tags vs. individual page tags (20 page sample)
- Measure precision: % of cluster tags relevant to each member

### Edge Cases
- Cluster with very similar pages (expect high confidence)
- Cluster with diverse pages (expect more general tags)
- Technical vs. general content
- Small vs. large clusters

## Configuration

**Environment variables:**
```bash
CLUSTER_TAGGING_TEMPERATURE=0.2
CLUSTER_TAGGING_MAX_TOKENS=500
CLUSTER_MAX_TAGS=8
CLUSTER_MIN_TAG_CONFIDENCE=0.5
```

## Testing Strategy

### Unit Tests
1. Test prompt formatting with various inputs
2. Test JSON parsing (valid and invalid responses)
3. Test tag validation logic
4. Test confidence filtering

### Integration Tests
1. End-to-end tag generation for test cluster
2. Verify tags stored in database
3. Test with various model responses
4. Test retry logic on parse failures

### Quality Tests
1. Generate tags for 10 test clusters
2. Manual evaluation of tag relevance
3. Check tag applicability to all cluster members
4. Compare to individual page tagging baseline

---

## Task Breakdown

### Feature 1: Prompt Engineering
- [ ] Create tagging_api/prompts.py module
- [ ] Define CLUSTER_TAGGING_PROMPT constant
- [ ] Create prompt formatting function
- [ ] Add existing tags formatting helper
- [ ] Add page content formatting helper
- [ ] Test prompt with various cluster sizes
- [ ] Iterate on prompt wording (test with real LLM)
- [ ] Document prompt design decisions

### Feature 2: Tag Generation Core
- [ ] Create tagging_api/tag_generator.py module
- [ ] Implement `generate_cluster_tags()` function
- [ ] Integrate with existing LLM client
- [ ] Set appropriate generation parameters (temp, max_tokens)
- [ ] Add timeout handling (30s max)
- [ ] Add retry logic (3 attempts)
- [ ] Log all LLM calls and responses
- [ ] Write unit tests for tag generation

### Feature 3: JSON Response Parsing
- [ ] Create `parse_tag_response()` function
- [ ] Implement JSON validation
- [ ] Validate required fields (name, confidence, rationale, category)
- [ ] Validate confidence range (0.0-1.0)
- [ ] Validate tag name format (lowercase, hyphenated)
- [ ] Validate category enum values
- [ ] Add error handling for malformed JSON
- [ ] Log parsing failures with full response
- [ ] Write unit tests for parser (valid/invalid cases)
- [ ] Track parsing success rate metric

### Feature 4: Tag Caching
- [ ] Add cluster_tags JSONB column to page_tag_clusters
- [ ] Create GIN index on cluster_tags
- [ ] Implement cache storage after generation
- [ ] Implement cache retrieval function
- [ ] Add cache invalidation on re-clustering
- [ ] Write tests for cache operations

### Feature 5: API Endpoint
- [ ] Create POST /analyze/cluster route
- [ ] Implement request validation
- [ ] Add authentication check
- [ ] Fetch cluster data from database
- [ ] Fetch representative pages content
- [ ] Fetch existing wiki tags
- [ ] Call tag generation function
- [ ] Store results in cache
- [ ] Format response
- [ ] Add error handling
- [ ] Write integration tests for endpoint

### Feature 6: Quality Validation
- [ ] Generate tags for 10 diverse test clusters
- [ ] Manually evaluate tag relevance (human review)
- [ ] Check tags apply to all cluster members
- [ ] Measure JSON parsing success rate (target: 95%+)
- [ ] Measure processing time per cluster (target: <5s)
- [ ] Compare cluster tags vs individual page tags (20 page sample)
- [ ] Calculate precision metric
- [ ] Document quality findings
- [ ] Identify areas for prompt improvement

### Feature 7: Configuration & Monitoring
- [ ] Add cluster tagging env vars to .env.example
- [ ] Document prompt template parameters
- [ ] Add metrics collection (processing time, parse success)
- [ ] Add logging for all generation attempts
- [ ] Create debug endpoint to view cached cluster tags
- [ ] Document LLM parameter choices
- [ ] Update phase documentation with results