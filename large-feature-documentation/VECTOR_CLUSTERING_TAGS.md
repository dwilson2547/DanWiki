# Vector Clustering-Based Tag Generation

## Success Probability Assessment

**Overall Success Likelihood: 75-85%**

**High Confidence Areas:**
- Clustering page embeddings (90% - proven technology, embeddings already exist)
- Generating tags for clusters (85% - LLM prompt engineering is well-understood)
- Tag propagation logic (95% - straightforward database operations)

**Medium Confidence Areas:**
- Optimal cluster count determination (70% - requires experimentation)
- Confidence score calibration (65% - subjective, needs validation)
- Handling edge cases and outliers (70% - unpredictable content patterns)

**Risk Factors:**
- Wiki content heterogeneity (highly technical vs. general documentation)
- Embedding quality for domain-specific content
- Cluster stability across wiki updates
- LLM consistency across different cluster compositions

**Mitigation Strategy:**
Start with hybrid approach that falls back to individual page tagging when clustering confidence is low. This ensures no worse than current performance while allowing gradual optimization.

## Architecture Overview

### Data Flow

```
1. Wiki Pages → 2. Page Embeddings → 3. Clustering → 4. Cluster Analysis
     (existing)     (existing)         (new)         (new)
                                          ↓
5. Tag Generation ← 6. Representative Pages Selection
   (LLM call)          (new)
       ↓
7. Tag Propagation → 8. Confidence Weighting → 9. Database Storage
   (new)                (new)                     (existing)
```

### Components

**New Services:**
- Clustering Service (in tagging microservice)
- Cluster Management (database tables)
- Batch orchestration endpoint

**Modified Services:**
- Tag generation prompt templates
- Batch processing worker
- Tag confidence scoring

**Database Changes:**
- page_tag_clusters table
- cluster_metadata table
- tag source tracking in page_tags

## Database Schema

```sql
-- Cluster metadata
CREATE TABLE page_tag_clusters (
    id SERIAL PRIMARY KEY,
    wiki_id INTEGER NOT NULL REFERENCES wikis(id) ON DELETE CASCADE,
    cluster_label INTEGER NOT NULL,
    centroid_embedding vector(384),
    page_count INTEGER NOT NULL,
    avg_distance_to_centroid FLOAT,
    representative_page_ids INTEGER[],
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(wiki_id, cluster_label)
);

CREATE INDEX idx_page_tag_clusters_wiki ON page_tag_clusters(wiki_id);

-- Track which pages belong to which clusters
CREATE TABLE page_cluster_assignments (
    id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    cluster_id INTEGER NOT NULL REFERENCES page_tag_clusters(id) ON DELETE CASCADE,
    distance_to_centroid FLOAT NOT NULL,
    is_outlier BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(page_id, cluster_id)
);

CREATE INDEX idx_page_cluster_page ON page_cluster_assignments(page_id);
CREATE INDEX idx_page_cluster_cluster ON page_cluster_assignments(cluster_id);

-- Modify page_tags to track tag source
ALTER TABLE page_tags ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';
-- Values: 'manual', 'cluster', 'individual_llm', 'hybrid'

ALTER TABLE page_tags ADD COLUMN IF NOT EXISTS cluster_id INTEGER REFERENCES page_tag_clusters(id) ON DELETE SET NULL;
ALTER TABLE page_tags ADD COLUMN IF NOT EXISTS base_confidence FLOAT;
-- base_confidence: original LLM confidence before distance weighting

CREATE INDEX idx_page_tags_source ON page_tags(source);
CREATE INDEX idx_page_tags_cluster ON page_tags(cluster_id);
```

## Implementation Phases

### Phase 1: Core Clustering Infrastructure (Week 1)

**Goal:** Cluster page embeddings and store cluster metadata

**Tasks:**

1. Add clustering dependencies
   - scikit-learn (for KMeans, silhouette analysis)
   - hdbscan (better for variable density clusters)
   - scipy (for distance metrics)

2. Implement clustering algorithm
   - Location: `tagging_api/clustering.py`
   - Function: `cluster_page_embeddings(wiki_id, embeddings, params)`
   - Algorithm: HDBSCAN (handles variable cluster sizes, identifies outliers)
   - Parameters:
     - min_cluster_size: 3-5 pages
     - min_samples: 2
     - metric: cosine
     - cluster_selection_method: eom (excess of mass)

3. Create database migrations
   - Add tables: page_tag_clusters, page_cluster_assignments
   - Modify page_tags table
   - Create indexes

4. Implement cluster storage
   - Location: `app/services/clustering_service.py`
   - Save cluster metadata to database
   - Store centroid embeddings
   - Track page-to-cluster assignments

**Validation:**
- Run clustering on test wiki with 50+ pages
- Verify clusters make semantic sense
- Check outlier detection works correctly
- Measure clustering stability (run 3 times, compare assignments)

**Success Criteria:**
- Clustering completes without errors
- 70%+ of pages assigned to clusters (not outliers)
- Silhouette score > 0.3 (reasonable cluster separation)
- Processing time < 5 seconds per 100 pages

### Phase 2: Representative Page Selection (Week 1-2)

**Goal:** Select best pages to represent each cluster for LLM analysis

**Strategy Options:**

1. **Centroid-Closest (Recommended - Most Reliable)**
   - Select k=3 pages closest to cluster centroid
   - Pros: Most representative of cluster theme
   - Cons: May miss edge cases
   - Implementation: Sort by distance_to_centroid ASC, LIMIT 3

2. **Diverse Sampling**
   - Select pages spread across cluster (k-means++ style)
   - Pros: Better coverage of cluster variation
   - Cons: May dilute cluster theme
   - Implementation: Iteratively select pages maximizing min distance to already selected

3. **Hybrid: Centroid + Edges**
   - 2 closest to centroid + 1 farthest (within threshold)
   - Pros: Balance between theme and coverage
   - Cons: More complex, may confuse LLM
   - Implementation: Combined selection logic

**Recommended:** Start with Option 1 (Centroid-Closest), measure precision/recall, then experiment with Option 3 if results are too narrow.

**Tasks:**

1. Implement selection algorithm
   - Location: `tagging_api/clustering.py`
   - Function: `select_representative_pages(cluster_pages, method='centroid_closest', k=3)`

2. Add page content aggregation
   - Location: `tagging_api/clustering.py`
   - Function: `aggregate_cluster_content(pages, max_tokens=3000)`
   - Strategy: Combine title + summary of all 3 pages, truncate if needed
   - Include page titles as context clues

3. Store representative page IDs
   - Update page_tag_clusters.representative_page_ids

**Validation:**
- Manual review of representative pages for 5-10 clusters
- Verify content aggregation stays within token limits
- Check that representative pages are semantically coherent

**Success Criteria:**
- Representative pages clearly reflect cluster theme (human eval)
- Aggregated content < 3000 tokens for all clusters
- Selection runs in < 1 second per cluster

### Phase 3: Cluster-Based Tag Generation (Week 2)

**Goal:** Generate tags for clusters using LLM analysis of representative pages

**Prompt Engineering:**

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

**Tasks:**

1. Create cluster-specific prompt template
   - Location: `tagging_api/prompts.py`
   - Add CLUSTER_TAGGING_PROMPT constant

2. Implement cluster tag generation
   - Location: `tagging_api/tag_generator.py`
   - Function: `generate_cluster_tags(cluster_content, existing_tags, model)`
   - Use lower temperature (0.2) for more consistent tags
   - Parse and validate JSON response

3. Add cluster tag caching
   - Store generated tags in page_tag_clusters table
   - JSON column: cluster_tags with full tag objects
   - Cache invalidation: when cluster is re-computed

4. Create endpoint
   - Location: `tagging_api/app.py`
   - Route: `POST /analyze/cluster`
   - Input: cluster_id or (wiki_id + cluster_label)
   - Output: Generated tags with confidences

**Validation:**
- Generate tags for 10 diverse clusters
- Human evaluation: do tags apply to all cluster members?
- Compare cluster tags vs. individual page tags (sample 20 pages)
- Measure precision: % of cluster tags that are relevant to each member page

**Success Criteria:**
- 80%+ of cluster tags are relevant to all member pages (human eval)
- Tag generation completes in < 5 seconds per cluster
- JSON parsing succeeds 95%+ of the time

### Phase 4: Tag Propagation with Confidence Weighting (Week 2-3)

**Goal:** Apply cluster tags to all member pages with distance-based confidence adjustment

**Confidence Calculation:**

```python
def calculate_propagated_confidence(base_confidence, distance_to_centroid, max_cluster_distance):
    """
    Adjust LLM confidence based on page's position in cluster.
    
    Pages close to centroid get full confidence.
    Pages at cluster edge get reduced confidence.
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

**Threshold Logic:**

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

**Tasks:**

1. Implement confidence calculation
   - Location: `app/services/clustering_service.py`
   - Function: `calculate_propagated_confidence(...)`
   - Add unit tests for edge cases

2. Implement tag propagation
   - Location: `app/services/clustering_service.py`
   - Function: `propagate_cluster_tags(cluster_id, auto_apply_threshold=0.7)`
   - Batch insert to page_tags table
   - Set source='cluster', cluster_id, base_confidence

3. Add conflict resolution
   - If page already has tag from manual/individual source: skip
   - If page has cluster tag from different cluster: keep higher confidence
   - Track tag provenance for debugging

4. Create bulk propagation endpoint
   - Location: `app/routes/tagging.py`
   - Route: `POST /api/tags/propagate-clusters`
   - Input: wiki_id, options (thresholds, mode)
   - Output: Statistics (tags_applied, pages_updated, conflicts)

**Validation:**
- Propagate tags for test cluster, manually verify 20 pages
- Check confidence scores decrease appropriately with distance
- Verify no duplicate tags on same page
- Test conflict resolution logic

**Success Criteria:**
- Tags propagated to all cluster members
- Confidence scores monotonically decrease with distance
- No duplicate tags created
- Propagation completes in < 2 seconds per 100 pages

### Phase 5: Full Wiki Batch Processing (Week 3)

**Goal:** Orchestrate full wiki tagging via clustering pipeline

**Pipeline Steps:**

```
1. Fetch all published pages with embeddings for wiki
2. Cluster embeddings (HDBSCAN)
3. Identify outliers
4. For each cluster:
   a. Select representative pages
   b. Generate cluster tags (LLM)
   c. Propagate to cluster members
5. For outliers (optional):
   a. Fall back to individual page tagging
   b. Or assign to nearest cluster with low confidence
6. Store cluster metadata
7. Return results
```

**Tasks:**

1. Implement full pipeline orchestrator
   - Location: `tagging_api/batch_processor.py`
   - Function: `process_wiki_clustering(wiki_id, options)`
   - Include progress tracking
   - Handle partial failures gracefully

2. Add RQ job for async processing
   - Location: `tagging_api/worker.py`
   - Job: `cluster_tag_wiki`
   - Store results in Redis
   - Callback to wiki app on completion

3. Create batch endpoint
   - Location: `tagging_api/app.py`
   - Route: `POST /analyze/wiki/cluster`
   - Input:
     ```json
     {
       "wiki_id": 1,
       "options": {
         "min_cluster_size": 3,
         "outlier_threshold": 0.5,
         "auto_apply_threshold": 0.7,
         "handle_outliers": "individual|nearest|skip",
         "regenerate_clusters": true
       }
     }
     ```
   - Output: job_id for status tracking

4. Add status endpoint
   - Route: `GET /analyze/wiki/cluster/{job_id}`
   - Return progress, results, errors

5. Create wiki app integration endpoint
   - Location: `app/routes/tagging.py`
   - Route: `POST /api/tags/cluster-tag-wiki`
   - Calls tagging microservice
   - Stores results in database
   - Returns summary to frontend

**Validation:**
- Process small test wiki (20-50 pages) end-to-end
- Verify all steps complete without errors
- Check database consistency (no orphaned records)
- Measure total processing time

**Success Criteria:**
- End-to-end pipeline completes successfully
- Processing time: < 10 minutes per 1000 pages
- No data corruption or inconsistencies
- Graceful handling of LLM failures (retry or skip)

### Phase 6: Outlier Handling (Week 3)

**Goal:** Handle pages that don't fit well into any cluster

**Outlier Detection:**
- HDBSCAN automatically marks outliers (cluster_label = -1)
- Additional check: distance > threshold even for assigned cluster

**Handling Strategies:**

1. **Skip (Safest)**
   - Leave outliers untagged by clustering
   - Rely on manual tagging or individual LLM calls
   - Pros: No incorrect tags
   - Cons: Outliers remain untagged

2. **Nearest Cluster with Low Confidence (Recommended)**
   - Assign to nearest cluster centroid
   - Apply heavy confidence penalty (multiply by 0.3-0.5)
   - Mark as is_outlier=true
   - Pros: Coverage without strong commitment
   - Cons: May still produce irrelevant tags

3. **Individual LLM Tagging (Thorough)**
   - Fall back to single-page tagging for outliers
   - Use existing /analyze endpoint
   - Pros: Highest quality for outliers
   - Cons: Additional LLM calls (higher cost)

**Tasks:**

1. Implement outlier detection
   - Location: `tagging_api/clustering.py`
   - Function: `identify_outliers(cluster_assignments, distance_threshold=0.7)`

2. Implement nearest cluster assignment
   - Location: `tagging_api/clustering.py`
   - Function: `assign_outliers_to_nearest(outliers, clusters)`
   - Calculate distance to all cluster centroids
   - Assign to nearest with outlier flag

3. Add outlier handling to pipeline
   - Configurable strategy via options
   - Default: nearest cluster with 0.4x confidence multiplier

4. Track outlier statistics
   - Count outliers per wiki
   - Store outlier handling method in page_cluster_assignments

**Validation:**
- Identify outliers in test wiki
- Manually review outlier page content
- Verify outlier tags are reasonable (if any applied)
- Compare outlier tag quality vs. non-outliers

**Success Criteria:**
- < 20% of pages marked as outliers
- Outlier handling strategy executes without errors
- Outlier tags (if applied) have confidence < 0.5

### Phase 7: Re-clustering Strategy (Week 4)

**Goal:** Determine when and how to update clusters as wiki content changes

**Triggers for Re-clustering:**

1. **Manual Trigger** (Safest)
   - Admin initiates re-clustering via UI
   - Full control, no surprises
   - Recommended for initial deployment

2. **Threshold-Based** (Balanced)
   - Re-cluster when X% of pages added/modified
   - Thresholds: 10% for small wikis (<100 pages), 20% for large
   - Automatic but predictable

3. **Scheduled** (Autonomous)
   - Weekly/monthly cron job
   - Good for actively maintained wikis
   - May waste resources on static wikis

**Re-clustering Process:**

```
1. Check if re-clustering needed (trigger condition met)
2. Archive old clusters (soft delete, keep for history)
3. Run new clustering on all current pages
4. Compare new vs. old cluster assignments
5. Update cluster metadata
6. Re-propagate tags with new confidences
7. Notify admin of significant changes
```

**Tasks:**

1. Implement re-clustering check
   - Location: `app/services/clustering_service.py`
   - Function: `should_recluster(wiki_id, strategy='threshold')`
   - Track wiki modification count since last clustering

2. Implement cluster archival
   - Soft delete: add archived_at timestamp
   - Keep old assignments for audit trail

3. Add cluster comparison
   - Location: `app/services/clustering_service.py`
   - Function: `compare_clusterings(old_clusters, new_clusters)`
   - Metrics: % of pages that changed clusters, new cluster count

4. Create re-clustering endpoint
   - Location: `app/routes/tagging.py`
   - Route: `POST /api/tags/recluster-wiki/{wiki_id}`
   - Requires admin permissions

5. Add automatic trigger (optional)
   - Background job checks all wikis periodically
   - Queues re-clustering for qualifying wikis

**Validation:**
- Trigger re-clustering on test wiki after adding 10 pages
- Verify old clusters are archived
- Check that tags are updated appropriately
- Measure cluster stability (how many pages changed clusters)

**Success Criteria:**
- Re-clustering completes successfully
- Old data is preserved (not deleted)
- Tag updates are applied correctly
- Cluster stability > 70% (most pages stay in same cluster)

### Phase 8: Monitoring and Optimization (Week 4)

**Goal:** Add observability and tune performance

**Metrics to Track:**

```python
CLUSTERING_METRICS = {
    # Performance
    'clustering_duration_seconds': float,
    'tag_generation_duration_seconds': float,
    'propagation_duration_seconds': float,
    'total_pipeline_duration_seconds': float,
    
    # Quality
    'cluster_count': int,
    'avg_cluster_size': float,
    'outlier_count': int,
    'outlier_percentage': float,
    'silhouette_score': float,
    'avg_cluster_confidence': float,
    
    # Coverage
    'pages_processed': int,
    'pages_tagged': int,
    'total_tags_applied': int,
    'avg_tags_per_page': float,
    
    # Errors
    'llm_failures': int,
    'parsing_errors': int,
    'propagation_conflicts': int
}
```

**Tasks:**

1. Add metrics collection
   - Location: `tagging_api/batch_processor.py`
   - Collect metrics at each pipeline stage
   - Store in Redis with job results

2. Create metrics endpoint
   - Route: `GET /api/tags/cluster-metrics/{wiki_id}`
   - Return latest clustering metrics
   - Include historical comparison

3. Add logging
   - Log key decision points (cluster assignment, outlier handling)
   - Log performance bottlenecks
   - Use structured logging (JSON)

4. Implement performance optimization
   - Batch database operations (bulk inserts)
   - Parallel LLM calls for clusters (if GPU memory allows)
   - Cache cluster embeddings in memory

5. Add quality checks
   - Automatic silhouette score calculation
   - Alert if quality metrics drop below thresholds
   - Manual review queue for low-confidence clusters

**Validation:**
- Run full pipeline with metrics collection
- Verify all metrics are captured correctly
- Review logs for completeness
- Test performance optimizations (before/after timing)

**Success Criteria:**
- All metrics captured and stored
- Logs provide sufficient debugging information
- Performance improvements: 20-30% faster vs. baseline
- No metrics collection overhead > 5% of total time

## Configuration

**Environment Variables:**

```bash
# Clustering
CLUSTERING_ALGORITHM=hdbscan  # hdbscan, kmeans
MIN_CLUSTER_SIZE=3
MIN_SAMPLES=2
OUTLIER_DISTANCE_THRESHOLD=0.7
REPRESENTATIVE_PAGE_COUNT=3

# Tag Propagation
AUTO_APPLY_THRESHOLD=0.7
SUGGEST_THRESHOLD=0.4
OUTLIER_CONFIDENCE_MULTIPLIER=0.4

# LLM for Clustering
CLUSTER_TAGGING_TEMPERATURE=0.2
CLUSTER_TAGGING_MAX_TOKENS=500
CLUSTER_CONTEXT_MAX_TOKENS=3000

# Re-clustering
RECLUSTER_THRESHOLD_PERCENT=15
RECLUSTER_SCHEDULE=weekly  # weekly, monthly, manual

# Performance
BATCH_SIZE_CLUSTERS=10  # Process N clusters in parallel
ENABLE_CLUSTER_CACHING=true
```

## Testing Strategy

### Unit Tests

1. **Clustering Algorithm**
   - Test with known embeddings (synthetic data)
   - Verify cluster assignments are consistent
   - Test outlier detection edge cases
   - Test empty wiki, single page, all identical pages

2. **Representative Page Selection**
   - Test centroid-closest selection
   - Test with clusters of varying sizes
   - Verify k is respected

3. **Confidence Calculation**
   - Test distance-based weighting
   - Test edge cases (distance=0, distance=max)
   - Verify monotonic decrease with distance

4. **Tag Propagation**
   - Test conflict resolution
   - Test duplicate prevention
   - Test threshold filtering

### Integration Tests

1. **Full Pipeline**
   - Test end-to-end with small wiki (20 pages)
   - Verify database state after completion
   - Test with no existing tags
   - Test with pre-existing manual tags

2. **Re-clustering**
   - Add pages, trigger re-cluster
   - Verify old clusters are archived
   - Test cluster stability metrics

3. **Outlier Handling**
   - Force outliers (add very different page)
   - Test each handling strategy
   - Verify outlier flags are set

### Load Tests

1. **Large Wiki Performance**
   - Test with 500, 1000, 2000 page wikis
   - Measure linear scaling
   - Identify bottlenecks

2. **Concurrent Processing**
   - Queue multiple wiki clustering jobs
   - Verify workers don't interfere
   - Test GPU memory management

### Quality Validation

1. **Manual Tag Review**
   - Sample 50 pages across 10 clusters
   - Evaluate tag relevance (binary: relevant/not relevant)
   - Calculate precision per cluster

2. **Comparison Study**
   - Tag 100 pages via clustering
   - Tag same 100 pages individually
   - Compare: precision, recall, consistency

3. **User Acceptance**
   - Have 2-3 wiki owners review cluster tags
   - Measure acceptance rate
   - Collect feedback on tag quality

## Rollout Plan

### Week 1: Development + Initial Testing
- Implement Phases 1-2
- Unit tests
- Test on synthetic data

### Week 2: Core Features
- Implement Phases 3-4
- Integration tests
- Test on small real wiki (20-50 pages)

### Week 3: Pipeline + Optimization
- Implement Phases 5-6
- Load tests
- Test on medium wiki (100-200 pages)

### Week 4: Polish + Monitoring
- Implement Phases 7-8
- Quality validation
- Documentation

### Week 5: Beta Deployment
- Deploy to staging environment
- Test with 2-3 beta wikis
- Collect metrics and feedback

### Week 6: Production Release
- Production deployment
- Enable for all wikis (admin-initiated)
- Monitor performance and quality

## Fallback Plan

**If clustering approach fails quality thresholds:**

1. **Hybrid Mode (Recommended Fallback)**
   - Use clustering only for wikis with > 100 pages
   - Use individual tagging for smaller wikis
   - Let admin choose per wiki

2. **Revert to Individual**
   - Keep clustering infrastructure
   - Disable auto-propagation
   - Use clusters for analytics only (tag suggestions in UI)

3. **Assisted Manual Tagging**
   - Show cluster tags as suggestions
   - Require human approval before applying
   - Track approval rate to improve prompts

## Success Metrics

**Quantitative:**
- Processing time: 10-15x faster than individual tagging
- Tag precision: > 75% (human eval on sample)
- Tag coverage: > 90% of pages get at least 3 tags
- Cluster stability: > 70% of pages stay in same cluster after re-clustering
- System uptime: > 99% during pipeline execution

**Qualitative:**
- User feedback: Positive reception from wiki owners
- Tag usefulness: Users actually browse by cluster-generated tags
- Maintenance: Few manual corrections needed

## Risk Mitigation

**Risk: Poor cluster quality due to heterogeneous wiki content**
- Mitigation: Increase min_cluster_size, tune outlier threshold
- Fallback: Use individual tagging for heterogeneous wikis

**Risk: LLM generates irrelevant tags for clusters**
- Mitigation: Lower auto_apply_threshold, require manual review
- Fallback: Show as suggestions only, not auto-apply

**Risk: Cluster instability across updates**
- Mitigation: Use hierarchical clustering, increase cluster size
- Fallback: Only re-cluster when explicitly triggered

**Risk: Database performance issues with large wikis**
- Mitigation: Batch operations, indexes on foreign keys
- Fallback: Process clusters in smaller batches

**Risk: GPU OOM during parallel cluster processing**
- Mitigation: Process one cluster at a time, monitor memory
- Fallback: Reduce context size, use smaller model

## Open Questions

1. **Cluster Count Determination**
   - How to automatically choose optimal number of clusters?
   - HDBSCAN finds it automatically, but may need tuning
   - Consider hierarchical clustering for more control

2. **Cross-Cluster Tags**
   - Should some tags apply across multiple clusters (e.g., "beginner")?
   - Consider global tag generation pass after clustering

3. **User Feedback Loop**
   - How to incorporate user corrections into future clustering?
   - Store user edits (removed/added tags) and use for prompt refinement

4. **Incremental Updates**
   - Can we update single cluster when pages within it change?
   - Or always require full re-clustering?

5. **Multi-Language Support**
   - Do embeddings cluster well across languages?
   - May need language-specific clustering

## Next Steps

1. Review and approve plan
2. Create database migrations (Phase 1)
3. Set up development branch
4. Begin Phase 1 implementation
5. Schedule weekly progress reviews
