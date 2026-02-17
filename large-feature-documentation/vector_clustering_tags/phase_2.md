# Phase 2: Representative Page Selection

**Timeline:** Week 1-2
**Goal:** Select best pages to represent each cluster for LLM analysis

## Overview

This phase focuses on selecting the most representative pages from each cluster to feed to the LLM. The selection strategy significantly impacts tag quality - we need pages that best capture the cluster's theme without introducing noise.

## Strategy Options

### Option 1: Centroid-Closest (Recommended)
- Select k=3 pages closest to cluster centroid
- **Pros:** Most representative of cluster theme, simple, fast
- **Cons:** May miss edge cases, less diversity
- **Implementation:** Sort by distance_to_centroid ASC, LIMIT 3

### Option 2: Diverse Sampling
- Select pages spread across cluster (k-means++ style)
- **Pros:** Better coverage of cluster variation
- **Cons:** May dilute cluster theme, confuse LLM
- **Implementation:** Iteratively select pages maximizing min distance to already selected

### Option 3: Hybrid (Centroid + Edges)
- 2 closest to centroid + 1 farthest (within threshold)
- **Pros:** Balance between theme and coverage
- **Cons:** More complex, may confuse LLM
- **Implementation:** Combined selection logic

**Decision:** Start with Option 1, measure results, experiment with Option 3 if needed.

## Implementation Details

### 1. Page Selection Algorithm

**Location:** `tagging_api/clustering.py`

**Function:** `select_representative_pages(cluster_pages, method='centroid_closest', k=3)`

**Logic:**
```python
def select_representative_pages(cluster_pages, method='centroid_closest', k=3):
    """
    Select k representative pages from cluster.
    
    Args:
        cluster_pages: List of (page_id, distance_to_centroid) tuples
        method: Selection strategy
        k: Number of pages to select
    
    Returns:
        List of page_ids
    """
    if method == 'centroid_closest':
        # Sort by distance, take k closest
        sorted_pages = sorted(cluster_pages, key=lambda x: x[1])
        return [page_id for page_id, _ in sorted_pages[:k]]
    # Add other methods as needed
```

### 2. Content Aggregation

**Location:** `tagging_api/clustering.py`

**Function:** `aggregate_cluster_content(pages, max_tokens=3000)`

**Strategy:**
- Combine title + summary for each representative page
- If full content needed, truncate proportionally
- Include page titles as strong context signals
- Stay within token limits

**Format:**
```
Page 1: {title}
{summary or truncated content}

Page 2: {title}
{summary or truncated content}

Page 3: {title}
{summary or truncated content}
```

### 3. Representative Page Storage

**Update page_tag_clusters table:**
- Store selected page IDs in `representative_page_ids` array column
- Allows retrieval without re-computation
- Useful for debugging and auditing

## Validation Criteria

### Functional Tests
- Manual review of representative pages for 5-10 clusters
- Verify content aggregation stays within token limits
- Check that representative pages are semantically coherent

### Quality Metrics
- Representative pages clearly reflect cluster theme (human evaluation)
- Aggregated content < 3000 tokens for all clusters
- Selection runs in < 1 second per cluster

### Edge Cases
- Clusters with fewer than k pages (use all)
- Single-page clusters
- Clusters with very long content (truncation)

## Configuration

**Environment variables:**
```bash
REPRESENTATIVE_PAGE_COUNT=3
CLUSTER_CONTEXT_MAX_TOKENS=3000
REPRESENTATIVE_SELECTION_METHOD=centroid_closest
```

## Testing Strategy

### Unit Tests
1. Test selection with various cluster sizes (2, 5, 10, 100 pages)
2. Test with k > cluster size
3. Test content aggregation token counting
4. Test truncation logic

### Integration Tests
1. Select representatives from real clusters
2. Verify stored page IDs match selection
3. Test full content retrieval and aggregation

---

## Task Breakdown

### Feature 1: Page Selection Algorithm
- [ ] Create `select_representative_pages()` function signature
- [ ] Implement centroid-closest selection method
- [ ] Add parameter validation (k, method)
- [ ] Handle edge case: k > cluster size (use all pages)
- [ ] Handle edge case: empty cluster
- [ ] Add logging for selection decisions
- [ ] Write unit tests for selection logic
- [ ] Test with clusters of varying sizes (2, 5, 10, 50, 100 pages)

### Feature 2: Content Aggregation
- [ ] Create `aggregate_cluster_content()` function
- [ ] Implement token counting (use tiktoken or similar)
- [ ] Fetch page titles and summaries from database
- [ ] Format aggregated content (template)
- [ ] Implement proportional truncation if over limit
- [ ] Prioritize title + summary over full content
- [ ] Add logging for token counts
- [ ] Write unit tests for aggregation logic
- [ ] Test truncation behavior with long content

### Feature 3: Database Integration
- [ ] Add query to fetch pages by cluster_id with distances
- [ ] Update page_tag_clusters after selection (representative_page_ids)
- [ ] Create helper function to retrieve representative pages
- [ ] Add caching for representative page content
- [ ] Write integration tests with test database

### Feature 4: Alternative Selection Methods (Optional)
- [ ] Implement diverse sampling method
- [ ] Implement hybrid (centroid + edges) method
- [ ] Add method parameter to configuration
- [ ] Write comparison tests (centroid vs. diverse vs. hybrid)
- [ ] Document trade-offs in code comments

### Feature 5: Validation & Quality Checks
- [ ] Select representatives for 10 test clusters
- [ ] Manual review: do pages represent cluster well?
- [ ] Verify all aggregated content < 3000 tokens
- [ ] Check semantic coherence (do pages relate to each other?)
- [ ] Measure selection performance (target: <1s per cluster)
- [ ] Test with edge cases (small clusters, large clusters)

### Feature 6: Configuration & Documentation
- [ ] Add representative selection env vars to .env.example
- [ ] Document selection strategy rationale
- [ ] Add docstrings with examples
- [ ] Document token counting approach
- [ ] Create usage examples
- [ ] Update phase documentation with findings