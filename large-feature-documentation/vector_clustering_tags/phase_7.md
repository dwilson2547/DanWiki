# Phase 7: Re-clustering Strategy

**Timeline:** Week 4
**Goal:** Determine when and how to update clusters as wiki content changes

## Overview

As wikis evolve (pages added, modified, deleted), clusters can become stale. We need a strategy to detect when re-clustering is needed and how to update clusters without disrupting existing tags.

## Re-clustering Triggers

### Trigger 1: Manual (Safest - Recommended for Initial Deployment)
- Admin initiates re-clustering via UI button
- Full control, no surprises
- Admin can review impact before applying
- **Use for:** Initial deployment, major wiki changes

### Trigger 2: Threshold-Based (Balanced - Recommended for Production)
- Automatically re-cluster when X% of pages added/modified
- **Thresholds:**
  - Small wikis (<100 pages): 10% change
  - Medium wikis (100-500 pages): 15% change
  - Large wikis (>500 pages): 20% change
- **Pros:** Automatic but predictable
- **Cons:** Requires tracking modification count

### Trigger 3: Scheduled (Autonomous)
- Weekly/monthly cron job
- Good for actively maintained wikis
- **Pros:** Set and forget
- **Cons:** May waste resources on static wikis, unpredictable timing

**Recommended approach:** Start with manual (Trigger 1), then enable threshold-based (Trigger 2) after validation.

## Re-clustering Process

### Workflow

```
1. Check if re-clustering needed (trigger condition met)
2. Archive old clusters (soft delete, keep for history)
3. Fetch current pages with embeddings
4. Run new clustering on all current pages
5. Compare new vs. old cluster assignments
6. Calculate cluster stability metrics
7. Store new cluster metadata
8. Re-propagate tags with new confidences
9. Archive old tags with source='cluster' (optional)
10. Notify admin of significant changes
```

### Cluster Stability Metrics

```python
def calculate_cluster_stability(old_assignments, new_assignments):
    \"\"\"
    Measure how much clustering changed.
    
    Returns:
        - stability_score: % of pages that stayed in same cluster (0.0-1.0)
        - pages_changed_cluster: count
        - new_clusters: count
        - removed_clusters: count
    \"\"\"
    common_pages = set(old_assignments.keys()) & set(new_assignments.keys())
    
    unchanged = 0
    for page_id in common_pages:
        # Compare cluster membership
        old_cluster = old_assignments[page_id]
        new_cluster = new_assignments[page_id]
        
        # Check if same pages are still clustered together
        old_neighbors = get_cluster_members(old_cluster)
        new_neighbors = get_cluster_members(new_cluster)
        
        overlap = len(old_neighbors & new_neighbors) / len(old_neighbors | new_neighbors)
        if overlap > 0.5:  # Majority overlap
            unchanged += 1
    
    stability_score = unchanged / len(common_pages) if common_pages else 0
    
    return {
        'stability_score': stability_score,
        'pages_changed_cluster': len(common_pages) - unchanged,
        'old_cluster_count': len(set(old_assignments.values())),
        'new_cluster_count': len(set(new_assignments.values()))
    }
```

## Implementation Details

### 1. Modification Tracking

**Add to pages table:**
```sql
ALTER TABLE pages ADD COLUMN IF NOT EXISTS last_clustered_at TIMESTAMP;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS modified_after_clustering BOOLEAN DEFAULT false;
```

**Update on page modification:**
```python
def mark_page_modified(page_id):
    # Set modified_after_clustering flag
    db.execute(
        \"UPDATE pages SET modified_after_clustering = true WHERE id = :page_id\",
        {'page_id': page_id}
    )
```

### 2. Re-clustering Check Function

**Location:** `app/services/clustering_service.py`

**Function:** `should_recluster(wiki_id, strategy='threshold')`

```python
def should_recluster(wiki_id, strategy='threshold'):
    \"\"\"
    Check if wiki needs re-clustering.
    
    Args:
        wiki_id: Wiki to check
        strategy: 'manual', 'threshold', or 'scheduled'
    
    Returns:
        (should_recluster: bool, reason: str)
    \"\"\"
    if strategy == 'manual':
        return False, \"Manual trigger only\"
    
    if strategy == 'threshold':
        total_pages = count_wiki_pages(wiki_id)
        modified_pages = count_modified_pages(wiki_id)
        
        threshold = get_threshold_for_size(total_pages)
        change_percent = (modified_pages / total_pages) * 100
        
        if change_percent >= threshold:
            return True, f\"{change_percent:.1f}% of pages modified (threshold: {threshold}%)\"\n        return False, f\"Only {change_percent:.1f}% modified (threshold: {threshold}%)\"\n    \n    if strategy == 'scheduled':
        last_clustered = get_last_clustering_date(wiki_id)
        schedule_interval = get_schedule_interval()  # from config\n        \n        if datetime.now() - last_clustered > schedule_interval:
            return True, f\"Last clustered {last_clustered}, schedule: {schedule_interval}\"\n        return False, \"Not yet time for scheduled re-clustering\"\n```

### 3. Cluster Archival

**Add to page_tag_clusters table:**
```sql
ALTER TABLE page_tag_clusters ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;
ALTER TABLE page_tag_clusters ADD COLUMN IF NOT EXISTS replaced_by_cluster_id INTEGER REFERENCES page_tag_clusters(id);

CREATE INDEX idx_page_tag_clusters_archived ON page_tag_clusters(archived_at);
```

**Archival function:**
```python
def archive_clusters(wiki_id):
    \"\"\"Soft delete old clusters before re-clustering.\"\"\"
    db.execute(
        \"\"\"
        UPDATE page_tag_clusters 
        SET archived_at = NOW() 
        WHERE wiki_id = :wiki_id 
          AND archived_at IS NULL
        \"\"\",
        {'wiki_id': wiki_id}
    )
```

### 4. Cluster Comparison Function

**Location:** `app/services/clustering_service.py`

**Function:** `compare_clusterings(wiki_id, old_cluster_date)`

```python
def compare_clusterings(wiki_id, old_cluster_date):
    \"\"\"
    Compare old and new clustering to measure stability.
    \"\"\"
    # Fetch old assignments
    old_assignments = get_cluster_assignments(wiki_id, archived=True, date=old_cluster_date)
    
    # Fetch new assignments
    new_assignments = get_cluster_assignments(wiki_id, archived=False)
    
    # Calculate metrics
    metrics = calculate_cluster_stability(old_assignments, new_assignments)
    
    # Find major changes
    major_changes = identify_major_changes(old_assignments, new_assignments)
    
    return {
        'metrics': metrics,
        'major_changes': major_changes
    }
```

### 5. Tag Re-propagation

**Options:**

**Option A: Keep old tags, add new tags**
- Old cluster tags remain (marked with archived cluster_id)
- New cluster tags added alongside
- User sees both, can manually clean up

**Option B: Replace old cluster tags**
- Delete all tags with source='cluster' and archived cluster_id
- Apply new cluster tags
- Cleaner, but loses history

**Option C: Keep high-confidence old tags, add new tags**
- Keep old cluster tags with confidence > 0.8
- Add new cluster tags
- Mark conflicts

**Recommended:** Option B for simplicity, Option C for safety.

### 6. Re-clustering Endpoint

**Location:** `app/routes/tagging.py`

**Route:** `POST /api/tags/recluster-wiki/{wiki_id}`

**Request:**
```json
{
  "strategy": "threshold|scheduled|force",
  "options": {
    "replace_old_tags": true,
    "notify_admin": true
  }
}
```

**Response:**
```json
{
  "wiki_id": 1,
  "status": "completed",
  "old_cluster_count": 20,
  "new_cluster_count": 22,
  "stability_score": 0.78,
  "pages_changed_cluster": 45,
  "tags_updated": 230,
  "processing_time_ms": 45000
}
```

### 7. Admin Notification

**Send notification when:**
- Re-clustering completes
- Stability score < 0.5 (major restructuring)
- Significant increase/decrease in cluster count (>30%)

**Notification content:**
- Wiki name
- Cluster count change
- Stability score
- Pages affected
- Link to review changes

## Validation Criteria

### Functional Tests
- Trigger re-clustering on test wiki after adding 10 pages
- Verify old clusters are archived
- Check that tags are updated appropriately
- Measure cluster stability (how many pages changed clusters)

### Quality Metrics
- Re-clustering completes successfully
- Old data is preserved (not deleted)
- Tag updates are applied correctly
- Cluster stability > 70% (most pages stay in same cluster)

### Edge Cases
- Re-clustering immediately after clustering (no changes)
- Re-clustering after deleting many pages
- Re-clustering with only new pages added (no overlap)

## Configuration

**Environment variables:**
```bash
RECLUSTER_THRESHOLD_SMALL_WIKI=10
RECLUSTER_THRESHOLD_MEDIUM_WIKI=15
RECLUSTER_THRESHOLD_LARGE_WIKI=20
RECLUSTER_SCHEDULE=weekly  # weekly, monthly, never
MIN_STABILITY_SCORE=0.7
REPLACE_OLD_CLUSTER_TAGS=true
```

## Testing Strategy

### Unit Tests
1. Test modification tracking
2. Test threshold calculations
3. Test cluster stability calculation
4. Test cluster archival logic

### Integration Tests
1. Full re-clustering workflow
2. Compare old vs. new clusters
3. Verify tag updates
4. Test with various change percentages

### Quality Tests
1. Measure stability on real wikis
2. Validate cluster quality after re-clustering
3. Check tag relevance after re-propagation

---

## Task Breakdown

### Feature 1: Modification Tracking
- [ ] Add last_clustered_at column to pages table
- [ ] Add modified_after_clustering column to pages table
- [ ] Create migration for new columns
- [ ] Implement page modification trigger
- [ ] Update page edit handlers to set modified flag
- [ ] Create query to count modified pages
- [ ] Write tests for tracking

### Feature 2: Re-clustering Check Logic
- [ ] Create `should_recluster()` function
- [ ] Implement manual strategy (always return false)
- [ ] Implement threshold strategy
- [ ] Calculate threshold based on wiki size
- [ ] Count modified pages since last clustering
- [ ] Implement scheduled strategy (compare dates)
- [ ] Add logging for check decisions
- [ ] Write unit tests for each strategy

### Feature 3: Cluster Archival
- [ ] Add archived_at column to page_tag_clusters
- [ ] Add replaced_by_cluster_id column
- [ ] Create index on archived_at
- [ ] Create migration for columns
- [ ] Implement `archive_clusters()` function
- [ ] Implement soft delete (set archived_at)
- [ ] Update queries to filter archived clusters
- [ ] Write tests for archival

### Feature 4: Cluster Comparison
- [ ] Create `calculate_cluster_stability()` function
- [ ] Fetch old cluster assignments
- [ ] Fetch new cluster assignments
- [ ] Compare page-to-cluster mappings
- [ ] Calculate stability score
- [ ] Identify pages that changed clusters
- [ ] Count cluster count changes
- [ ] Write unit tests for stability calculation

### Feature 5: Tag Re-propagation Strategy
- [ ] Decide on tag handling approach (A, B, or C)
- [ ] Implement chosen strategy
- [ ] Delete old cluster tags (if Option B)
- [ ] Apply new cluster tags
- [ ] Handle conflicts (if Option C)
- [ ] Track tag changes (added, removed, updated)
- [ ] Write tests for re-propagation

### Feature 6: Re-clustering Endpoint
- [ ] Create POST /api/tags/recluster-wiki/{wiki_id} route
- [ ] Add authentication/authorization (admin only)
- [ ] Implement request validation
- [ ] Call re-clustering check (if strategy != 'force')
- [ ] Archive old clusters
- [ ] Run new clustering
- [ ] Compare clusterings
- [ ] Re-propagate tags
- [ ] Format response with statistics
- [ ] Add error handling
- [ ] Write integration tests

### Feature 7: Admin Notification
- [ ] Determine notification triggers
- [ ] Implement notification function
- [ ] Format notification content
- [ ] Send via email/webhook/in-app notification
- [ ] Include stability metrics
- [ ] Add link to review changes
- [ ] Make notification optional (config)
- [ ] Write tests for notifications

### Feature 8: Automatic Trigger Background Job (Optional)
- [ ] Create background job to check all wikis
- [ ] Run periodically (daily)
- [ ] Call `should_recluster()` for each wiki
- [ ] Queue re-clustering jobs for qualifying wikis
- [ ] Add job scheduling (cron or RQ scheduler)
- [ ] Add logging
- [ ] Make job optional (config)
- [ ] Write tests

### Feature 9: Validation & Quality Checks
- [ ] Create test wiki
- [ ] Run initial clustering
- [ ] Add/modify 15% of pages
- [ ] Trigger re-clustering
- [ ] Verify old clusters archived
- [ ] Check stability score (target: >0.7)
- [ ] Manually review changed clusters
- [ ] Verify tags updated correctly
- [ ] Measure processing time
- [ ] Test with various modification percentages

### Feature 10: UI Integration (Optional)
- [ ] Add \"Re-cluster Wiki\" button in admin UI
- [ ] Show last clustering date
- [ ] Show modification percentage
- [ ] Display re-clustering results
- [ ] Show stability metrics
- [ ] Allow reviewing changes before applying
- [ ] Write frontend tests

### Feature 11: Configuration & Documentation
- [ ] Add re-clustering env vars to .env.example
- [ ] Document each trigger strategy
- [ ] Document tag re-propagation options
- [ ] Create admin guide for re-clustering
- [ ] Document stability metrics
- [ ] Add troubleshooting guide
- [ ] Update phase documentation with findings
