# Phase 1: Core Clustering Infrastructure

**Timeline:** Week 1
**Goal:** Cluster page embeddings and store cluster metadata

## Overview

This phase establishes the foundational clustering infrastructure. We'll implement the HDBSCAN clustering algorithm, create database tables to store cluster metadata and assignments, and build the initial service layer for cluster management.

## Implementation Details

### 1. Dependencies

**Required packages:**
- scikit-learn (for KMeans fallback, silhouette analysis)
- hdbscan (primary clustering algorithm)
- scipy (for distance metrics)

**Installation:**
```bash
pip install scikit-learn hdbscan scipy
```

### 2. Clustering Algorithm

**Location:** `tagging_api/clustering.py`

**Function:** `cluster_page_embeddings(wiki_id, embeddings, params)`

**Algorithm:** HDBSCAN
- Handles variable cluster sizes
- Automatically identifies outliers
- No need to specify cluster count

**Parameters:**
- `min_cluster_size`: 3-5 pages
- `min_samples`: 2
- `metric`: cosine
- `cluster_selection_method`: eom (excess of mass)

**Key Features:**
- Returns cluster labels for each page
- Identifies outliers (label = -1)
- Calculates centroid embeddings
- Computes distance metrics

### 3. Database Schema

**Tables to create:**

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
ALTER TABLE page_tags ADD COLUMN IF NOT EXISTS cluster_id INTEGER REFERENCES page_tag_clusters(id) ON DELETE SET NULL;
ALTER TABLE page_tags ADD COLUMN IF NOT EXISTS base_confidence FLOAT;

CREATE INDEX idx_page_tags_source ON page_tags(source);
CREATE INDEX idx_page_tags_cluster ON page_tags(cluster_id);
```

### 4. Cluster Storage Service

**Location:** `app/services/clustering_service.py`

**Functions:**
- `save_cluster_metadata(wiki_id, cluster_data)` - Store cluster info
- `save_cluster_assignments(cluster_id, page_assignments)` - Store page-to-cluster mappings
- `calculate_centroid(embeddings)` - Compute cluster centroid
- `get_cluster_stats(cluster_id)` - Retrieve cluster statistics

## Validation Criteria

### Functional Tests
- Run clustering on test wiki with 50+ pages
- Verify clusters make semantic sense (manual review)
- Check outlier detection works correctly
- Measure clustering stability (run 3 times, compare assignments)

### Performance Tests
- Processing time < 5 seconds per 100 pages
- Memory usage stays within bounds

### Quality Metrics
- 70%+ of pages assigned to clusters (not outliers)
- Silhouette score > 0.3 (reasonable cluster separation)
- Clustering completes without errors

## Configuration

**Environment variables:**
```bash
CLUSTERING_ALGORITHM=hdbscan
MIN_CLUSTER_SIZE=3
MIN_SAMPLES=2
OUTLIER_DISTANCE_THRESHOLD=0.7
```

## Testing Strategy

### Unit Tests
1. Test clustering with synthetic embeddings (known clusters)
2. Test centroid calculation accuracy
3. Test outlier detection edge cases
4. Test empty wiki, single page, all identical pages

### Integration Tests
1. Test database migrations apply cleanly
2. Test full clustering + storage pipeline
3. Test with real wiki data (if available)

---

## Task Breakdown

### Feature 1: Dependencies & Setup
- [ ] Add scikit-learn, hdbscan, scipy to requirements.txt
- [ ] Install dependencies in development environment
- [ ] Verify HDBSCAN imports correctly
- [ ] Create clustering.py module structure

### Feature 2: Database Migrations
- [ ] Create migration file for page_tag_clusters table
- [ ] Create migration file for page_cluster_assignments table
- [ ] Create migration for page_tags modifications (source, cluster_id, base_confidence columns)
- [ ] Create all indexes
- [ ] Run migrations on development database
- [ ] Verify schema matches design
- [ ] Test CASCADE delete behavior

### Feature 3: Clustering Algorithm Implementation
- [ ] Create `cluster_page_embeddings()` function signature
- [ ] Implement HDBSCAN clustering with cosine metric
- [ ] Add parameter validation (min_cluster_size, min_samples)
- [ ] Implement outlier identification logic
- [ ] Calculate cluster centroids from member embeddings
- [ ] Calculate distance statistics (avg, max per cluster)
- [ ] Add error handling for edge cases
- [ ] Write unit tests for clustering function

### Feature 4: Cluster Storage Service
- [ ] Create app/services/clustering_service.py
- [ ] Implement `save_cluster_metadata()` function
- [ ] Implement `save_cluster_assignments()` function
- [ ] Implement `calculate_centroid()` helper function
- [ ] Implement `get_cluster_stats()` query function
- [ ] Add transaction handling for atomic saves
- [ ] Add error handling and rollback logic
- [ ] Write unit tests for storage functions

### Feature 5: Integration & End-to-End Testing
- [ ] Create test wiki with 50+ pages in test database
- [ ] Run clustering on test wiki
- [ ] Verify cluster assignments in database
- [ ] Check centroid embeddings are stored correctly
- [ ] Verify outlier flags are set appropriately
- [ ] Measure processing time (target: <5s per 100 pages)
- [ ] Calculate silhouette score (target: >0.3)
- [ ] Run clustering 3 times, measure stability
- [ ] Manual review: do clusters make semantic sense?

### Feature 6: Configuration & Documentation
- [ ] Add clustering environment variables to .env.example
- [ ] Document clustering algorithm choices (why HDBSCAN)
- [ ] Document database schema in code comments
- [ ] Add docstrings to all public functions
- [ ] Create usage examples in comments
- [ ] Update main README with Phase 1 completion notes