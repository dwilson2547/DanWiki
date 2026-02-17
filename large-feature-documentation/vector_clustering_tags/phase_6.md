# Phase 6: Outlier Handling

**Timeline:** Week 3
**Goal:** Handle pages that don't fit well into any cluster

## Overview

HDBSCAN automatically identifies outliers - pages that don't belong to any cluster. We need a strategy to handle these pages so they don't remain untagged, while avoiding applying irrelevant tags.

## Outlier Detection

### Automatic Detection
- HDBSCAN marks outliers with cluster_label = -1
- Typically 10-30% of pages depending on wiki heterogeneity

### Additional Distance-Based Check
```python
def is_outlier(page, cluster, outlier_threshold=0.7):
    \"\"\"Check if page is too far from cluster centroid.\"\"\"
    distance = calculate_distance(page.embedding, cluster.centroid)
    max_distance = cluster.max_distance_to_centroid
    
    # Normalize distance to [0, 1]
    normalized_distance = distance / max_distance if max_distance > 0 else 0
    
    return normalized_distance > outlier_threshold
```

## Handling Strategies

### Strategy 1: Skip (Safest - Recommended for Initial Deployment)
- Leave outliers untagged by clustering
- Rely on manual tagging or individual LLM calls
- **Pros:** No incorrect tags, safest option
- **Cons:** Outliers remain untagged, incomplete coverage

### Strategy 2: Nearest Cluster with Low Confidence (Balanced - Recommended)
- Assign to nearest cluster centroid
- Apply heavy confidence penalty (multiply by 0.3-0.5)
- Mark as is_outlier=true in page_cluster_assignments
- **Pros:** Coverage without strong commitment, tags are suggestions
- **Cons:** May still produce somewhat irrelevant tags

### Strategy 3: Individual LLM Tagging (Thorough - Resource Intensive)
- Fall back to single-page tagging for outliers
- Use existing /analyze endpoint
- **Pros:** Highest quality for outliers, tailored tags
- **Cons:** Additional LLM calls (higher cost/time)

**Recommended approach:** Start with Strategy 1 (skip), then offer Strategy 2 as option, implement Strategy 3 only if needed.

## Implementation Details

### 1. Outlier Detection Function

**Location:** `tagging_api/clustering.py`

**Function:** `identify_outliers(cluster_assignments, distance_threshold=0.7)`

```python
def identify_outliers(cluster_assignments, distance_threshold=0.7):
    \"\"\"
    Identify pages that are outliers.
    
    Args:
        cluster_assignments: Dict mapping page_id to (cluster_label, distance)
        distance_threshold: Max normalized distance to consider inlier
    
    Returns:
        List of page_ids that are outliers
    \"\"\"
    outliers = []
    
    for page_id, (cluster_label, distance) in cluster_assignments.items():
        # HDBSCAN outliers
        if cluster_label == -1:
            outliers.append(page_id)
            continue
        
        # Distance-based outliers
        # (Check if assigned but very far from centroid)
        cluster = get_cluster_by_label(cluster_label)
        if is_outlier_by_distance(distance, cluster.max_distance, distance_threshold):
            outliers.append(page_id)
    
    return outliers
```

### 2. Nearest Cluster Assignment

**Location:** `tagging_api/clustering.py`

**Function:** `assign_outliers_to_nearest(outliers, clusters)`

```python
def assign_outliers_to_nearest(outliers, clusters):
    \"\"\"
    Assign outlier pages to nearest cluster centroid.
    
    Args:
        outliers: List of page objects with embeddings
        clusters: List of cluster objects with centroids
    
    Returns:
        Dict mapping page_id to (nearest_cluster_id, distance)
    \"\"\"
    assignments = {}
    
    for page in outliers:
        min_distance = float('inf')
        nearest_cluster = None
        
        for cluster in clusters:
            distance = cosine_distance(page.embedding, cluster.centroid)
            if distance < min_distance:
                min_distance = distance
                nearest_cluster = cluster
        
        assignments[page.id] = (nearest_cluster.id, min_distance)
    
    return assignments
```

### 3. Outlier Confidence Adjustment

```python
OUTLIER_CONFIDENCE_MULTIPLIER = 0.4

def calculate_outlier_confidence(base_confidence, distance_to_nearest):
    \"\"\"
    Apply heavy penalty for outlier assignments.
    
    Outliers get even lower confidence than edge cluster members.
    \"\"\"
    return base_confidence * OUTLIER_CONFIDENCE_MULTIPLIER * (1 - distance_to_nearest)
```

### 4. Outlier Handling in Pipeline

**Location:** `tagging_api/batch_processor.py`

```python
def handle_outliers(wiki_id, outliers, clusters, strategy='skip'):
    \"\"\"
    Handle outlier pages according to chosen strategy.
    \"\"\"
    if strategy == 'skip':
        # Mark as outliers, don't tag
        mark_pages_as_outliers(outliers)
        return {'outliers_skipped': len(outliers)}
    
    elif strategy == 'nearest':
        # Assign to nearest cluster with low confidence
        assignments = assign_outliers_to_nearest(outliers, clusters)
        for page_id, (cluster_id, distance) in assignments.items():
            cluster_tags = get_cluster_tags(cluster_id)
            for tag in cluster_tags:
                confidence = calculate_outlier_confidence(tag.confidence, distance)
                if confidence >= 0.3:  # Lower threshold for outliers
                    apply_tag(page_id, tag, confidence, source='cluster_outlier', cluster_id=cluster_id)
        return {'outliers_assigned': len(assignments)}
    
    elif strategy == 'individual':
        # Tag each outlier individually
        results = []
        for page in outliers:
            tags = call_individual_tagging_api(page)
            apply_tags(page.id, tags, source='individual_llm')
            results.append(page.id)
        return {'outliers_individually_tagged': len(results)}
```

### 5. Database Tracking

**Fields in page_cluster_assignments:**
- `is_outlier`: Boolean flag
- `distance_to_centroid`: Will be high for outliers
- `cluster_id`: NULL for skipped outliers, nearest cluster for assigned

**Query outliers:**
```sql
SELECT p.id, p.title, pca.distance_to_centroid
FROM pages p
JOIN page_cluster_assignments pca ON p.id = pca.page_id
WHERE pca.is_outlier = true
ORDER BY pca.distance_to_centroid DESC;
```

## Validation Criteria

### Functional Tests
- Identify outliers in test wiki
- Manually review outlier page content
- Verify outlier tags are reasonable (if any applied)
- Compare outlier tag quality vs. non-outliers

### Quality Metrics
- < 20% of pages marked as outliers (typical range: 10-30%)
- Outlier handling strategy executes without errors
- Outlier tags (if applied) have confidence < 0.5
- No crashes on wiki with all outliers or no outliers

### Edge Cases
- Wiki with 0 outliers
- Wiki with all outliers (highly heterogeneous)
- Outlier very far from all clusters
- Outlier equidistant from multiple clusters

## Configuration

**Environment variables:**
```bash
OUTLIER_DISTANCE_THRESHOLD=0.7
OUTLIER_CONFIDENCE_MULTIPLIER=0.4
OUTLIER_HANDLING_STRATEGY=skip  # skip, nearest, individual
OUTLIER_MIN_CONFIDENCE=0.3
```

## Testing Strategy

### Unit Tests
1. Test outlier identification (HDBSCAN + distance)
2. Test nearest cluster calculation
3. Test confidence adjustment for outliers
4. Test each handling strategy

### Integration Tests
1. Create test wiki with known outliers
2. Run full clustering pipeline
3. Verify outliers are identified correctly
4. Test each handling strategy end-to-end

### Quality Tests
1. Manually review outlier pages (semantic coherence?)
2. Compare outlier tags to cluster member tags
3. Check if outlier assignments make sense

---

## Task Breakdown

### Feature 1: Outlier Detection
- [ ] Create `identify_outliers()` function
- [ ] Implement HDBSCAN outlier detection (cluster_label == -1)
- [ ] Implement distance-based outlier detection
- [ ] Add configurable distance threshold
- [ ] Handle edge case: no outliers
- [ ] Handle edge case: all outliers
- [ ] Write unit tests for outlier detection
- [ ] Test with various distance thresholds

### Feature 2: Nearest Cluster Assignment
- [ ] Create `assign_outliers_to_nearest()` function
- [ ] Implement distance calculation to all centroids
- [ ] Find minimum distance cluster
- [ ] Handle edge case: equidistant clusters (use first)
- [ ] Optimize for many outliers (vectorized operations)
- [ ] Write unit tests for assignment logic
- [ ] Test with various cluster counts

### Feature 3: Outlier Confidence Adjustment
- [ ] Define OUTLIER_CONFIDENCE_MULTIPLIER constant
- [ ] Create `calculate_outlier_confidence()` function
- [ ] Implement heavy confidence penalty
- [ ] Ensure result always in [0.0, 1.0]
- [ ] Write unit tests for confidence calculation
- [ ] Test with various base confidences and distances

### Feature 4: Strategy 1 - Skip Implementation
- [ ] Implement skip strategy in `handle_outliers()`
- [ ] Mark pages as outliers in database (is_outlier=true)
- [ ] Don't create cluster assignments for skipped outliers
- [ ] Log outlier count and page IDs
- [ ] Return statistics
- [ ] Write tests for skip strategy

### Feature 5: Strategy 2 - Nearest Cluster Implementation
- [ ] Implement nearest strategy in `handle_outliers()`
- [ ] Call `assign_outliers_to_nearest()`
- [ ] Fetch tags for nearest cluster
- [ ] Calculate outlier confidence for each tag
- [ ] Apply threshold filtering (lower threshold)
- [ ] Insert tags with source='cluster_outlier'
- [ ] Set is_outlier=true in assignments
- [ ] Log assignment decisions
- [ ] Return statistics
- [ ] Write tests for nearest strategy

### Feature 6: Strategy 3 - Individual Tagging Implementation (Optional)
- [ ] Implement individual strategy in `handle_outliers()`
- [ ] Call existing /analyze endpoint for each outlier
- [ ] Apply returned tags with source='individual_llm'
- [ ] Handle LLM failures gracefully
- [ ] Track processing time (will be slow)
- [ ] Return statistics
- [ ] Write tests for individual strategy

### Feature 7: Pipeline Integration
- [ ] Add outlier handling to batch processor
- [ ] Make strategy configurable via options
- [ ] Call `handle_outliers()` after clustering
- [ ] Collect outlier statistics
- [ ] Include outlier stats in pipeline results
- [ ] Add error handling
- [ ] Write integration tests

### Feature 8: Database Tracking
- [ ] Verify is_outlier column exists in page_cluster_assignments
- [ ] Create query to list all outliers for wiki
- [ ] Create query to list outlier tags
- [ ] Add outlier count to cluster statistics
- [ ] Write database tests

### Feature 9: Validation & Quality Checks
- [ ] Create test wiki with diverse content (force outliers)
- [ ] Run clustering and identify outliers
- [ ] Manually review outlier pages (do they make sense?)
- [ ] Check outlier percentage (target: <20%)
- [ ] Test skip strategy
- [ ] Test nearest strategy
- [ ] Compare outlier tag quality to cluster member tags
- [ ] Measure processing time for each strategy

### Feature 10: Configuration & Monitoring
- [ ] Add outlier env vars to .env.example
- [ ] Make strategy runtime-configurable
- [ ] Add outlier metrics to pipeline results
- [ ] Add logging for outlier decisions
- [ ] Document each strategy's trade-offs
- [ ] Create admin guide for choosing strategy
- [ ] Update phase documentation with findings
