# Phase 4: Tag Propagation with Confidence Weighting

**Timeline:** Week 2-3
**Goal:** Apply cluster tags to all member pages with distance-based confidence adjustment

## Overview

This phase propagates the cluster-level tags to individual pages, adjusting confidence scores based on how close each page is to the cluster centroid. Pages near the center get full confidence; pages at the edges get reduced confidence.

## Confidence Calculation

### Distance-Based Weighting

```python
def calculate_propagated_confidence(base_confidence, distance_to_centroid, max_cluster_distance):
    """
    Adjust LLM confidence based on page's position in cluster.
    
    Pages close to centroid get full confidence.
    Pages at cluster edge get reduced confidence.
    
    Args:
        base_confidence: Original LLM confidence (0.0-1.0)
        distance_to_centroid: Page's distance to cluster center
        max_cluster_distance: Maximum distance in cluster
    
    Returns:
        Adjusted confidence (0.0-1.0)
    """
    # Linear decay based on distance
    distance_factor = 1.0 - (distance_to_centroid / max_cluster_distance)
    
    # Apply distance penalty (sqrt for gentler decay)
    distance_weight = math.sqrt(max(0.0, distance_factor))
    
    # Final confidence
    return base_confidence * distance_weight

# Examples:
# - Page at centroid (distance=0): confidence = 0.90 * 1.0 = 0.90
# - Page at 50% distance: confidence = 0.90 * 0.707 = 0.64
# - Page at edge (distance=max): confidence = 0.90 * 0.0 = 0.0
```

### Threshold Logic

```python
PROPAGATION_THRESHOLDS = {
    'auto_apply': 0.7,      # Automatically apply tag
    'suggest': 0.4,          # Show as suggestion
    'ignore': 0.4            # Don't propagate
}

def should_propagate_tag(final_confidence):
    if final_confidence >= PROPAGATION_THRESHOLDS['auto_apply']:
        return 'apply'
    elif final_confidence >= PROPAGATION_THRESHOLDS['suggest']:
        return 'suggest'
    else:
        return 'ignore'
```

## Implementation Details

### 1. Confidence Calculation Module

**Location:** `app/services/clustering_service.py`

**Function:** `calculate_propagated_confidence(base_confidence, distance_to_centroid, max_cluster_distance)`

**Features:**
- Smooth decay (sqrt for gentler curve)
- Handles edge cases (distance=0, distance=max)
- Always returns value in [0.0, 1.0]

### 2. Tag Propagation Function

**Location:** `app/services/clustering_service.py`

**Function:** `propagate_cluster_tags(cluster_id, auto_apply_threshold=0.7)`

**Process:**
1. Fetch cluster tags from cache
2. Fetch all pages in cluster with distances
3. For each page:
   - For each cluster tag:
     - Calculate propagated confidence
     - Check against thresholds
     - If above threshold, prepare tag record
4. Batch insert to page_tags table
5. Return statistics

**Fields to set:**
- `source`: 'cluster'
- `cluster_id`: reference to cluster
- `base_confidence`: original LLM confidence
- `confidence`: propagated confidence (for sorting/filtering)

### 3. Conflict Resolution

**Rules:**
1. **Manual/Individual takes precedence:** Skip if page already has tag from 'manual' or 'individual_llm' source
2. **Higher confidence wins:** If page has cluster tag from different cluster, keep higher confidence
3. **Track provenance:** Always store cluster_id for debugging

**Implementation:**
```sql
-- Check for conflicts before insert
SELECT pt.id, pt.source, pt.confidence 
FROM page_tags pt
JOIN tags t ON pt.tag_id = t.id
WHERE pt.page_id = :page_id 
  AND t.name = :tag_name;

-- Only insert if:
-- 1. No existing tag, OR
-- 2. Existing tag is 'cluster' source AND new confidence > existing confidence
```

### 4. Bulk Propagation Endpoint

**Location:** `app/routes/tagging.py`

**Route:** `POST /api/tags/propagate-clusters`

**Request:**
```json
{
  "wiki_id": 1,
  "options": {
    "auto_apply_threshold": 0.7,
    "suggest_threshold": 0.4,
    "mode": "auto|suggest|dry_run"
  }
}
```

**Response:**
```json
{
  "wiki_id": 1,
  "clusters_processed": 15,
  "statistics": {
    "tags_applied": 234,
    "tags_suggested": 89,
    "tags_skipped": 45,
    "pages_updated": 120,
    "conflicts_resolved": 12
  },
  "processing_time_ms": 2345
}
```

## Validation Criteria

### Functional Tests
- Propagate tags for test cluster, manually verify 20 pages
- Check confidence scores decrease appropriately with distance
- Verify no duplicate tags on same page
- Test conflict resolution logic

### Quality Metrics
- Tags propagated to all cluster members
- Confidence scores monotonically decrease with distance
- No duplicate tags created
- Propagation completes in < 2 seconds per 100 pages

### Edge Cases
- Page already has same tag manually
- Page belongs to multiple clusters (shouldn't happen, but handle)
- Very high distance pages (near outlier threshold)
- Confidence calculation produces 0.0

## Configuration

**Environment variables:**
```bash
AUTO_APPLY_THRESHOLD=0.7
SUGGEST_THRESHOLD=0.4
OUTLIER_CONFIDENCE_MULTIPLIER=0.4
PROPAGATION_BATCH_SIZE=100
```

## Testing Strategy

### Unit Tests
1. Test confidence calculation with various distances
2. Test threshold logic (auto_apply, suggest, ignore)
3. Test conflict resolution rules
4. Test edge cases (distance=0, distance=max)

### Integration Tests
1. Full propagation for test cluster
2. Verify database state after propagation
3. Test with pre-existing manual tags
4. Test with pre-existing cluster tags

### Performance Tests
1. Measure propagation time for 100, 500, 1000 pages
2. Test batch insert performance
3. Identify bottlenecks

---

## Task Breakdown

### Feature 1: Confidence Calculation
- [ ] Create confidence calculation function
- [ ] Implement distance-based weighting (sqrt decay)
- [ ] Add input validation (ranges, null checks)
- [ ] Handle edge cases (distance=0, distance=max, invalid inputs)
- [ ] Write unit tests for various distance values
- [ ] Test monotonic decrease property
- [ ] Document calculation rationale
- [ ] Create visualization of decay curve (optional)

### Feature 2: Threshold Logic
- [ ] Define PROPAGATION_THRESHOLDS constants
- [ ] Create `should_propagate_tag()` function
- [ ] Implement threshold comparison logic
- [ ] Make thresholds configurable via env vars
- [ ] Write unit tests for threshold decisions
- [ ] Document threshold rationale

### Feature 3: Tag Propagation Core
- [ ] Create `propagate_cluster_tags()` function
- [ ] Fetch cluster tags from database
- [ ] Fetch cluster pages with distances
- [ ] Calculate max_cluster_distance
- [ ] Loop through pages and tags
- [ ] Calculate propagated confidence for each pair
- [ ] Apply threshold filtering
- [ ] Prepare tag records for insertion
- [ ] Write unit tests for propagation logic

### Feature 4: Conflict Resolution
- [ ] Implement conflict detection query
- [ ] Add rule: skip manual/individual_llm tags
- [ ] Add rule: keep higher confidence for cluster tags
- [ ] Track conflict statistics
- [ ] Add logging for conflict resolution decisions
- [ ] Write unit tests for conflict scenarios
- [ ] Test with various existing tag sources

### Feature 5: Batch Database Operations
- [ ] Implement batch insert for page_tags
- [ ] Use transactions for atomicity
- [ ] Add rollback on error
- [ ] Optimize insert performance (COPY or multi-value INSERT)
- [ ] Add progress tracking for large batches
- [ ] Write integration tests for batch operations
- [ ] Measure performance (target: <2s per 100 pages)

### Feature 6: Bulk Propagation Endpoint
- [ ] Create POST /api/tags/propagate-clusters route
- [ ] Implement request validation
- [ ] Add authentication/authorization
- [ ] Fetch all clusters for wiki
- [ ] Loop through clusters and propagate
- [ ] Collect statistics
- [ ] Format response
- [ ] Add error handling
- [ ] Write integration tests for endpoint

### Feature 7: Validation & Quality Checks
- [ ] Propagate tags for test cluster (50+ pages)
- [ ] Manually verify 20 random pages
- [ ] Check confidence decreases with distance (plot graph)
- [ ] Verify no duplicate tags on any page
- [ ] Test conflict resolution (create manual tags first)
- [ ] Measure propagation time
- [ ] Validate database integrity (foreign keys, constraints)
- [ ] Test dry_run mode (no actual writes)

### Feature 8: Configuration & Monitoring
- [ ] Add propagation env vars to .env.example
- [ ] Make thresholds runtime-configurable
- [ ] Add metrics collection (tags applied, conflicts, time)
- [ ] Add logging for propagation decisions
- [ ] Create debug endpoint to view propagation preview
- [ ] Document configuration options
- [ ] Update phase documentation with findings
