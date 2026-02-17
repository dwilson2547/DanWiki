# Phase 8: Monitoring and Optimization

**Timeline:** Week 4
**Goal:** Add observability and tune performance

## Overview

This final phase focuses on production readiness: comprehensive monitoring, performance optimization, and quality assurance. Good observability is critical for debugging issues and measuring success.

## Metrics to Track

### Performance Metrics

```python
PERFORMANCE_METRICS = {
    'clustering_duration_seconds': float,
    'tag_generation_duration_seconds': float,
    'propagation_duration_seconds': float,
    'total_pipeline_duration_seconds': float,
    'avg_llm_latency_ms': float,
    'pages_per_second': float
}
```

### Quality Metrics

```python
QUALITY_METRICS = {
    'cluster_count': int,
    'avg_cluster_size': float,
    'min_cluster_size': int,
    'max_cluster_size': int,
    'outlier_count': int,
    'outlier_percentage': float,
    'silhouette_score': float,          # Cluster quality
    'avg_cluster_confidence': float,    # Tag confidence
    'tags_per_cluster': float
}
```

### Coverage Metrics

```python
COVERAGE_METRICS = {
    'pages_processed': int,
    'pages_tagged': int,
    'pages_untagged': int,
    'total_tags_applied': int,
    'avg_tags_per_page': float,
    'min_tags_per_page': int,
    'max_tags_per_page': int,
    'coverage_percentage': float  # % of pages with at least 1 tag
}
```

### Error Metrics

```python
ERROR_METRICS = {
    'llm_failures': int,
    'llm_timeouts': int,
    'parsing_errors': int,
    'propagation_conflicts': int,
    'database_errors': int,
    'total_errors': int
}
```

## Implementation Details

### 1. Metrics Collection

**Location:** `tagging_api/metrics.py`

**Metrics class:**
```python
class ClusteringMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.stage_times = {}
        self.counters = defaultdict(int)
        self.gauges = {}
    
    def start_stage(self, stage_name):
        self.stage_times[stage_name] = {'start': time.time()}
    
    def end_stage(self, stage_name):
        if stage_name in self.stage_times:
            duration = time.time() - self.stage_times[stage_name]['start']
            self.stage_times[stage_name]['duration'] = duration
    
    def increment(self, counter_name, value=1):
        self.counters[counter_name] += value
    
    def set_gauge(self, gauge_name, value):
        self.gauges[gauge_name] = value
    
    def to_dict(self):
        return {
            'total_duration': time.time() - self.start_time,
            'stage_durations': {k: v['duration'] for k, v in self.stage_times.items()},
            'counters': dict(self.counters),
            'gauges': self.gauges
        }
```

### 2. Metrics Storage

**Redis for real-time metrics:**
```python
def store_metrics(wiki_id, job_id, metrics):
    \"\"\"Store metrics in Redis with TTL.\"\"\"
    key = f\"clustering_metrics:{wiki_id}:{job_id}\"
    redis_client.setex(
        key,
        ttl=86400,  # 24 hours
        value=json.dumps(metrics.to_dict())
    )
```

**Database for historical metrics:**
```sql
CREATE TABLE clustering_metrics (
    id SERIAL PRIMARY KEY,
    wiki_id INTEGER NOT NULL REFERENCES wikis(id),
    job_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Performance
    total_duration_seconds FLOAT,
    clustering_duration_seconds FLOAT,
    tag_generation_duration_seconds FLOAT,
    propagation_duration_seconds FLOAT,
    
    -- Quality
    cluster_count INTEGER,
    avg_cluster_size FLOAT,
    outlier_count INTEGER,
    silhouette_score FLOAT,
    
    -- Coverage
    pages_processed INTEGER,
    pages_tagged INTEGER,
    total_tags_applied INTEGER,
    avg_tags_per_page FLOAT,
    
    -- Errors
    llm_failures INTEGER,
    parsing_errors INTEGER,
    total_errors INTEGER,
    
    metrics_json JSONB  -- Full metrics dump
);

CREATE INDEX idx_clustering_metrics_wiki ON clustering_metrics(wiki_id);
CREATE INDEX idx_clustering_metrics_created ON clustering_metrics(created_at DESC);
```

### 3. Metrics Endpoint

**Location:** `app/routes/tagging.py`

**Route:** `GET /api/tags/cluster-metrics/{wiki_id}`

**Response:**
```json
{
  \"wiki_id\": 1,
  \"latest_clustering\": {
    \"job_id\": \"cluster_wiki_1_abc123\",
    \"created_at\": \"2026-01-24T10:00:00Z\",
    \"performance\": {
      \"total_duration_seconds\": 245.3,
      \"clustering_duration_seconds\": 12.5,
      \"tag_generation_duration_seconds\": 180.2,
      \"propagation_duration_seconds\": 52.6
    },
    \"quality\": {
      \"cluster_count\": 25,
      \"avg_cluster_size\": 20.4,
      \"outlier_percentage\": 12.3,
      \"silhouette_score\": 0.42
    },
    \"coverage\": {
      \"pages_processed\": 500,
      \"pages_tagged\": 485,
      \"avg_tags_per_page\": 5.2
    },
    \"errors\": {
      \"llm_failures\": 2,
      \"parsing_errors\": 0,
      \"total_errors\": 2
    }
  },
  \"historical_trend\": {
    \"avg_duration_seconds\": 230.5,
    \"avg_cluster_count\": 23.8,
    \"avg_quality_score\": 0.39
  }
}
```

### 4. Logging Strategy

**Structured logging with JSON:**
```python
import structlog

logger = structlog.get_logger()

# Log key events
logger.info(
    \"clustering_started\",
    wiki_id=wiki_id,
    page_count=page_count,
    options=options
)

logger.info(
    \"cluster_created\",
    wiki_id=wiki_id,
    cluster_id=cluster.id,
    page_count=len(cluster.pages),
    representative_pages=cluster.representative_page_ids
)

logger.warning(
    \"llm_timeout\",
    cluster_id=cluster.id,
    attempt=retry_count,
    timeout_seconds=30
)

logger.error(
    \"propagation_failed\",
    cluster_id=cluster.id,
    error=str(e),
    traceback=traceback.format_exc()
)
```

**Log levels:**
- DEBUG: Detailed algorithm steps
- INFO: Major pipeline events
- WARNING: Recoverable errors, retries
- ERROR: Failures that skip work
- CRITICAL: Fatal errors that abort pipeline

### 5. Performance Optimization

**Optimization opportunities:**

1. **Database Batching**
   - Use bulk inserts instead of row-by-row
   - Use COPY for large datasets
   - Batch updates in transactions

2. **Query Optimization**
   - Add indexes on frequently queried columns
   - Use joins instead of N+1 queries
   - Materialize expensive computations

3. **Caching**
   - Cache cluster centroids in memory
   - Cache existing wiki tags
   - Cache embedding similarity results

4. **Parallelization** (if safe)
   - Generate tags for multiple clusters in parallel (GPU memory permitting)
   - Propagate tags in parallel batches

**Example optimization:**
```python
# Before: N+1 queries
for page_id in page_ids:
    page = db.query(Page).get(page_id)
    apply_tags(page)

# After: Bulk query
pages = db.query(Page).filter(Page.id.in_(page_ids)).all()
bulk_apply_tags(pages)
```

### 6. Quality Checks

**Automatic quality alerts:**
```python
def check_quality_thresholds(metrics):
    alerts = []
    
    if metrics['silhouette_score'] < 0.2:
        alerts.append({
            'severity': 'warning',
            'message': 'Low cluster quality (silhouette < 0.2)',
            'action': 'Consider increasing min_cluster_size or check data quality'
        })
    
    if metrics['outlier_percentage'] > 30:
        alerts.append({
            'severity': 'warning',
            'message': 'High outlier percentage (>30%)',
            'action': 'Wiki content may be too heterogeneous for clustering'
        })
    
    if metrics['avg_tags_per_page'] < 2:
        alerts.append({
            'severity': 'info',
            'message': 'Low average tags per page (<2)',
            'action': 'Consider lowering confidence thresholds'
        })
    
    return alerts
```

### 7. Admin Dashboard (Optional)

**Metrics to display:**
- Recent clustering jobs (status, duration, quality)
- Cluster distribution (histogram of cluster sizes)
- Tag coverage (% of pages tagged)
- Quality trends over time (silhouette score)
- Error rates
- Performance trends

## Validation Criteria

### Functional Tests
- Run full pipeline with metrics collection
- Verify all metrics are captured correctly
- Review logs for completeness
- Test performance optimizations (before/after timing)

### Quality Metrics
- All metrics captured and stored
- Logs provide sufficient debugging information
- Performance improvements: 20-30% faster vs. baseline
- No metrics collection overhead > 5% of total time

### Edge Cases
- Very large wiki (test memory usage)
- Very small wiki (test with 5 pages)
- Wiki with frequent errors (test error tracking)

## Configuration

**Environment variables:**
```bash
# Metrics
ENABLE_METRICS=true
METRICS_TTL_SECONDS=86400
STORE_METRICS_IN_DB=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/tagging/clustering.log

# Performance
ENABLE_QUERY_CACHING=true
BATCH_INSERT_SIZE=1000
MAX_PARALLEL_LLM_CALLS=3
```

## Testing Strategy

### Unit Tests
1. Test metrics collection (start/end stages)
2. Test metrics calculations
3. Test quality threshold checks
4. Test logging output

### Integration Tests
1. Full pipeline with metrics
2. Metrics storage and retrieval
3. Historical metrics queries
4. Alert generation

### Performance Tests
1. Benchmark before optimization
2. Apply optimizations
3. Benchmark after optimization
4. Measure improvement percentage

---

## Task Breakdown

### Feature 1: Metrics Collection Framework
- [ ] Create tagging_api/metrics.py module
- [ ] Implement ClusteringMetrics class
- [ ] Add start_stage() and end_stage() methods
- [ ] Add counter and gauge methods
- [ ] Integrate metrics into batch processor
- [ ] Collect metrics at each pipeline stage
- [ ] Write unit tests for metrics class

### Feature 2: Metrics Storage
- [ ] Design clustering_metrics database table
- [ ] Create migration for metrics table
- [ ] Implement Redis storage for real-time metrics
- [ ] Implement database storage for historical metrics
- [ ] Add metrics TTL in Redis
- [ ] Create indexes on metrics table
- [ ] Write tests for storage

### Feature 3: Metrics Endpoint
- [ ] Create GET /api/tags/cluster-metrics/{wiki_id} route
- [ ] Fetch latest metrics from database
- [ ] Calculate historical trends
- [ ] Format response
- [ ] Add authentication
- [ ] Write integration tests

### Feature 4: Structured Logging
- [ ] Add structlog to requirements.txt
- [ ] Configure structured logging
- [ ] Replace print statements with logger calls
- [ ] Log all major pipeline events (start, end, errors)
- [ ] Log cluster creation details
- [ ] Log LLM calls and responses
- [ ] Log tag propagation decisions
- [ ] Add request ID for tracing
- [ ] Write to log file
- [ ] Test log output format

### Feature 5: Performance Optimization - Database
- [ ] Profile database queries (identify slow queries)
- [ ] Add missing indexes
- [ ] Convert N+1 queries to bulk queries
- [ ] Use bulk inserts for tags (executemany or COPY)
- [ ] Wrap operations in transactions
- [ ] Measure query performance before/after
- [ ] Write tests for optimized queries

### Feature 6: Performance Optimization - Caching
- [ ] Implement centroid embedding cache (in-memory)
- [ ] Cache existing wiki tags
- [ ] Cache cluster metadata during propagation
- [ ] Add cache invalidation logic
- [ ] Measure cache hit rates
- [ ] Write tests for caching

### Feature 7: Performance Optimization - Parallelization
- [ ] Identify parallel-safe operations
- [ ] Implement parallel tag generation (if GPU allows)
- [ ] Implement parallel tag propagation (batch processing)
- [ ] Add thread pool or async execution
- [ ] Handle errors in parallel operations
- [ ] Measure speedup
- [ ] Write tests for parallel execution

### Feature 8: Quality Checks & Alerts
- [ ] Implement `check_quality_thresholds()` function
- [ ] Define quality thresholds (silhouette, outliers, tags/page)
- [ ] Generate alerts for threshold violations
- [ ] Log quality alerts
- [ ] Store alerts in metrics
- [ ] Send notifications (optional)
- [ ] Write tests for quality checks

### Feature 9: Performance Benchmarking
- [ ] Create benchmark suite
- [ ] Benchmark baseline (before optimization)
- [ ] Apply each optimization
- [ ] Benchmark after each optimization
- [ ] Measure improvement percentages
- [ ] Document optimization impact
- [ ] Create performance report

### Feature 10: Admin Dashboard (Optional)
- [ ] Design dashboard UI
- [ ] Create API endpoints for dashboard data
- [ ] Display recent clustering jobs
- [ ] Show cluster size distribution (chart)
- [ ] Show quality trends (chart)
- [ ] Show error rates
- [ ] Add real-time job status
- [ ] Write frontend tests

### Feature 11: End-to-End Validation
- [ ] Run full pipeline with all monitoring
- [ ] Verify all metrics collected
- [ ] Check log completeness
- [ ] Verify quality alerts trigger correctly
- [ ] Measure total performance improvement
- [ ] Test with various wiki sizes (10, 100, 1000 pages)
- [ ] Identify any remaining bottlenecks

### Feature 12: Documentation & Configuration
- [ ] Add monitoring env vars to .env.example
- [ ] Document all tracked metrics
- [ ] Document logging format
- [ ] Document quality thresholds
- [ ] Create monitoring guide for admins
- [ ] Document optimization decisions
- [ ] Create troubleshooting guide
- [ ] Update phase documentation with findings

### Feature 13: Production Readiness
- [ ] Review all error handling
- [ ] Add graceful shutdown handling
- [ ] Test recovery from failures
- [ ] Set up log rotation
- [ ] Configure monitoring alerts (PagerDuty, etc.)
- [ ] Create runbook for common issues
- [ ] Perform load testing
- [ ] Get approval for production deployment
