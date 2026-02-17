# Phase 5: Full Wiki Batch Processing

**Timeline:** Week 3
**Goal:** Orchestrate full wiki tagging via clustering pipeline

## Overview

This phase brings everything together into a complete end-to-end pipeline. Users can trigger clustering and tagging for an entire wiki with a single API call. The system handles all steps automatically and reports progress.

## Pipeline Architecture

### Pipeline Steps

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

### Error Handling Strategy

**Graceful degradation:**
- If clustering fails: abort, return error
- If single cluster tag generation fails: skip cluster, log error, continue
- If propagation fails for cluster: log error, continue with next
- If outlier handling fails: log error, mark outliers as untagged

**Partial success:**
- Return statistics on what succeeded and what failed
- Allow retry of failed portions
- Don't roll back successful clusters on partial failure

## Implementation Details

### 1. Pipeline Orchestrator

**Location:** `tagging_api/batch_processor.py`

**Function:** `process_wiki_clustering(wiki_id, options)`

**Process:**
```python
def process_wiki_clustering(wiki_id, options):
    results = {
        'wiki_id': wiki_id,
        'status': 'in_progress',
        'progress': {},
        'errors': []
    }
    
    try:
        # Step 1: Fetch pages with embeddings
        pages = fetch_wiki_pages_with_embeddings(wiki_id)
        results['progress']['pages_fetched'] = len(pages)
        
        # Step 2: Cluster
        clusters = cluster_page_embeddings(pages, options)
        results['progress']['clusters_created'] = len(clusters)
        
        # Step 3: Process each cluster
        for cluster in clusters:
            try:
                representatives = select_representative_pages(cluster)
                tags = generate_cluster_tags(representatives)
                propagate_cluster_tags(cluster, tags)
                results['progress']['clusters_processed'] += 1
            except Exception as e:
                results['errors'].append({
                    'cluster_id': cluster.id,
                    'error': str(e)
                })
        
        # Step 4: Handle outliers
        if options.get('handle_outliers') != 'skip':
            handle_outliers(wiki_id, options)
        
        results['status'] = 'completed'
        return results
        
    except Exception as e:
        results['status'] = 'failed'
        results['error'] = str(e)
        return results
```

### 2. Redis Queue Integration

**Location:** `tagging_api/worker.py`

**Job:** `cluster_tag_wiki`

**Queue Setup:**
```python
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url(os.getenv('REDIS_URL'))
queue = Queue('tagging', connection=redis_conn)

def cluster_tag_wiki(wiki_id, options):
    \"\"\"RQ worker job for wiki clustering and tagging.\"\"\"
    return process_wiki_clustering(wiki_id, options)
```

**Job Metadata:**
- Store in Redis with TTL (24 hours)
- Include progress updates
- Store final results

### 3. Batch API Endpoint

**Location:** `tagging_api/app.py`

**Route:** `POST /analyze/wiki/cluster`

**Request:**
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

**Response:**
```json
{
  "job_id": "cluster_wiki_1_abc123",
  "status": "queued",
  "estimated_duration_seconds": 300,
  "queue_position": 2
}
```

### 4. Status Endpoint

**Route:** `GET /analyze/wiki/cluster/{job_id}`

**Response:**
```json
{
  "job_id": "cluster_wiki_1_abc123",
  "status": "processing|completed|failed",
  "progress": {
    "pages_fetched": 500,
    "clusters_created": 25,
    "clusters_processed": 15,
    "tags_generated": 180,
    "tags_applied": 1200,
    "outliers_handled": 30
  },
  "errors": [
    {
      "cluster_id": 12,
      "error": "LLM timeout"
    }
  ],
  "created_at": "2026-01-24T10:00:00Z",
  "started_at": "2026-01-24T10:01:00Z",
  "completed_at": "2026-01-24T10:06:00Z"
}
```

### 5. Wiki App Integration

**Location:** `app/routes/tagging.py`

**Route:** `POST /api/tags/cluster-tag-wiki`

**Process:**
1. Validate user has permission (admin or wiki owner)
2. Call tagging microservice `/analyze/wiki/cluster`
3. Store job_id in wiki app database
4. Return job_id to frontend
5. Frontend polls status endpoint

**Optional webhook callback:**
- Tagging service calls back to wiki app on completion
- Wiki app updates job status in database
- Triggers notification to user

## Validation Criteria

### Functional Tests
- Process small test wiki (20-50 pages) end-to-end
- Verify all steps complete without errors
- Check database consistency (no orphaned records)
- Measure total processing time

### Quality Metrics
- End-to-end pipeline completes successfully
- Processing time: < 10 minutes per 1000 pages
- No data corruption or inconsistencies
- Graceful handling of LLM failures (retry or skip)

### Edge Cases
- Wiki with no pages
- Wiki with all identical pages (single cluster)
- Wiki with all unique pages (all outliers)
- Very large wiki (5000+ pages)

## Configuration

**Environment variables:**
```bash
# Pipeline
MAX_WIKI_PAGES=10000
PIPELINE_TIMEOUT_SECONDS=3600
ENABLE_PROGRESS_TRACKING=true

# Retry
MAX_CLUSTER_RETRIES=3
RETRY_DELAY_SECONDS=5

# Queue
RQ_QUEUE_NAME=tagging
JOB_TTL_SECONDS=86400
RESULT_TTL_SECONDS=604800
```

## Testing Strategy

### Unit Tests
1. Test pipeline orchestrator with mocked steps
2. Test error handling at each step
3. Test progress tracking
4. Test job metadata storage/retrieval

### Integration Tests
1. End-to-end test with small wiki (20 pages)
2. Test with medium wiki (100 pages)
3. Test with wiki containing outliers
4. Test partial failure scenarios
5. Test job queue and status endpoints

### Load Tests
1. Test with large wiki (1000 pages)
2. Test multiple concurrent wiki jobs
3. Measure memory usage
4. Measure GPU utilization

---

## Task Breakdown

### Feature 1: Pipeline Orchestrator
- [ ] Create tagging_api/batch_processor.py module
- [ ] Implement `process_wiki_clustering()` function
- [ ] Add step 1: Fetch pages with embeddings
- [ ] Add step 2: Run clustering
- [ ] Add step 3: Process each cluster (select + generate + propagate)
- [ ] Add step 4: Handle outliers
- [ ] Add progress tracking throughout pipeline
- [ ] Implement error collection (don't abort on single failure)
- [ ] Add logging for each major step
- [ ] Write unit tests with mocked dependencies

### Feature 2: Error Handling & Recovery
- [ ] Implement graceful degradation strategy
- [ ] Add retry logic for transient failures
- [ ] Separate fatal vs. recoverable errors
- [ ] Log all errors with context
- [ ] Return partial success results
- [ ] Add ability to resume from failure point
- [ ] Write tests for various failure scenarios

### Feature 3: Redis Queue Integration
- [ ] Add rq to requirements.txt
- [ ] Create tagging_api/worker.py module
- [ ] Implement `cluster_tag_wiki()` RQ job
- [ ] Set up Redis connection
- [ ] Configure job timeouts and TTLs
- [ ] Add job metadata storage
- [ ] Implement progress updates in Redis
- [ ] Test job enqueue/dequeue
- [ ] Test worker execution

### Feature 4: Batch Endpoint (Tagging Service)
- [ ] Create POST /analyze/wiki/cluster route
- [ ] Implement request validation
- [ ] Add authentication check
- [ ] Enqueue job in RQ
- [ ] Generate unique job_id
- [ ] Store job metadata
- [ ] Return job_id and status
- [ ] Add error handling
- [ ] Write integration tests

### Feature 5: Status Endpoint
- [ ] Create GET /analyze/wiki/cluster/{job_id} route
- [ ] Fetch job status from RQ
- [ ] Fetch progress from Redis
- [ ] Format response
- [ ] Handle job not found
- [ ] Add authentication check
- [ ] Write integration tests

### Feature 6: Wiki App Integration
- [ ] Create POST /api/tags/cluster-tag-wiki route in wiki app
- [ ] Add permission check (admin or owner)
- [ ] Call tagging service API
- [ ] Store job_id in wiki database
- [ ] Create job status table (optional)
- [ ] Return job_id to frontend
- [ ] Add error handling
- [ ] Write integration tests

### Feature 7: Frontend Polling (Optional)
- [ ] Create frontend component to trigger clustering
- [ ] Implement status polling (5-second interval)
- [ ] Display progress bar
- [ ] Show completion status
- [ ] Handle errors gracefully
- [ ] Add cancel button (if needed)

### Feature 8: Webhook Callback (Optional)
- [ ] Add callback_url parameter to batch endpoint
- [ ] Implement callback on job completion
- [ ] Include job results in callback payload
- [ ] Add callback authentication
- [ ] Handle callback failures (retry)
- [ ] Write tests for callback

### Feature 9: End-to-End Validation
- [ ] Create test wiki with 50 pages
- [ ] Trigger full pipeline via API
- [ ] Monitor progress through status endpoint
- [ ] Verify all clusters created in database
- [ ] Verify tags applied to all pages
- [ ] Check for orphaned records
- [ ] Measure total processing time
- [ ] Test with various wiki sizes (20, 100, 500 pages)

### Feature 10: Performance Optimization
- [ ] Profile pipeline to identify bottlenecks
- [ ] Optimize database queries (bulk operations)
- [ ] Add caching where appropriate
- [ ] Parallelize independent operations (if safe)
- [ ] Measure before/after performance
- [ ] Document optimization decisions

### Feature 11: Configuration & Documentation
- [ ] Add pipeline env vars to .env.example
- [ ] Document job lifecycle
- [ ] Document error handling strategy
- [ ] Add API documentation (Swagger)
- [ ] Create usage guide for wiki admins
- [ ] Document troubleshooting steps
- [ ] Update phase documentation with findings
