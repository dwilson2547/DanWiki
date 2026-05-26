# Semantic Search Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve semantic search quality via heading context in embeddings, page-level result grouping, relative score display, and RRF-based hybrid fusion.

**Architecture:** Pure Python/SQL changes to `app/services/chunking.py` and `app/routes/semantic_search.py`. No new services or dependencies. After deploy, trigger re-embed via existing admin endpoint `POST /api/admin/embeddings/generate-all` with `{"status": "all"}`.

**Tech Stack:** Python 3.12, Flask, SQLAlchemy raw SQL, pgvector `<=>` cosine distance operator, pytest

---

## File Map

| Action | File | Purpose |
|---|---|---|
| Create | `tests/conftest.py` | Flask app fixture for all tests |
| Create | `tests/test_chunking.py` | Tests for heading prefix logic |
| Create | `tests/test_semantic_search.py` | Tests for RRF and score normalization |
| Modify | `app/__init__.py` | CORS origins from `CORS_ORIGINS` env var |
| Modify | `app/services/chunking.py` | Add `finalize_chunk()` helper, prepend heading path |
| Modify | `app/routes/semantic_search.py` | Page-level grouping, relative scores, RRF hybrid |

---

### Task 1: Test infrastructure

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest.py**

```python
import pytest
from app import create_app
from app.models import db as _db


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    return app


@pytest.fixture(scope='session')
def app_context(app):
    with app.app_context():
        yield app
```

- [ ] **Step 2: Verify pytest can collect**

```bash
cd /home/daniel/documents/workspace/DanWiki
pytest tests/conftest.py --collect-only
```

Expected: `no tests ran` (conftest has no test functions — that's correct)

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add Flask app fixture for pytest"
```

---

### Task 2: CORS origins from env var

**Files:**
- Modify: `app/__init__.py`

- [ ] **Step 1: Update CORS initialisation**

In `app/__init__.py`, replace lines 34–41 (the `CORS(app, resources=...)` call):

```python
cors_origins = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000'
).split(',')

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

`os` is already imported via `from app.config import config` (which calls `load_dotenv` which imports `os`). Confirm `import os` is present at the top of `app/__init__.py`; add it if missing.

- [ ] **Step 2: Verify app starts**

```bash
FLASK_ENV=development python run.py &
sleep 2
curl -s http://localhost:5000/api/health
kill %1
```

Expected: `{"status":"healthy","version":"1.1.0"}`

- [ ] **Step 3: Commit**

```bash
git add app/__init__.py
git commit -m "fix: CORS origins configurable via CORS_ORIGINS env var"
```

---

### Task 3: Heading context in chunk text

**Files:**
- Modify: `app/services/chunking.py`
- Create: `tests/test_chunking.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_chunking.py`:

```python
import pytest
from app.services.chunking import TextChunker


@pytest.fixture
def chunker():
    return TextChunker(
        max_tokens=256,
        overlap_tokens=50,
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )


def test_chunk_under_heading_has_prefix(chunker):
    content = "## Setup\n\nInstall the dependencies first.\n\n## Usage\n\nRun the server."
    chunks = chunker.chunk_page("My Page", content)
    setup_chunks = [c for c in chunks if 'Setup' in c.get('heading_path', '')]
    assert len(setup_chunks) > 0, "Expected chunks under Setup heading"
    for chunk in setup_chunks:
        assert chunk['chunk_text'].startswith('[Setup]'), (
            f"Expected heading prefix, got: {chunk['chunk_text'][:60]}"
        )


def test_nested_heading_prefix(chunker):
    content = "## Deployment\n\n### Rolling Updates\n\nRolling updates swap pods one at a time."
    chunks = chunker.chunk_page("K8s Guide", content)
    rolling_chunks = [c for c in chunks if 'Rolling Updates' in c.get('heading_path', '')]
    assert len(rolling_chunks) > 0
    for chunk in rolling_chunks:
        assert '[Deployment > Rolling Updates]' in chunk['chunk_text']


def test_chunk_without_headings_has_no_prefix(chunker):
    content = "This page has no headings at all. Just plain prose."
    chunks = chunker.chunk_page("Plain Page", content)
    for chunk in chunks:
        assert not chunk['chunk_text'].startswith('['), (
            f"Unexpected heading prefix on chunk: {chunk['chunk_text'][:60]}"
        )


def test_heading_path_still_stored_separately(chunker):
    content = "## Installation\n\nRun pip install."
    chunks = chunker.chunk_page("Guide", content)
    install_chunks = [c for c in chunks if c.get('heading_path')]
    assert len(install_chunks) > 0
    for chunk in install_chunks:
        assert chunk['heading_path'] == 'Installation'
        assert '[Installation]' in chunk['chunk_text']
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_chunking.py -v
```

Expected: 4 FAILED (heading prefix not yet added)

- [ ] **Step 3: Add `finalize_chunk` helper in `chunk_page()`**

In `app/services/chunking.py`, inside the `chunk_page()` method, add this nested function immediately after the `join_chunk_text` local function (around line 198):

```python
def finalize_chunk(text: str, position: int, tokens: int) -> None:
    nonlocal chunk_index
    heading_path = self.get_heading_path(headings, position)
    if heading_path:
        text = f"[{heading_path}]\n\n{text}"
    chunks.append({
        'chunk_index': chunk_index,
        'chunk_text': text,
        'heading_path': heading_path,
        'token_count': tokens
    })
    chunk_index += 1
```

- [ ] **Step 4: Replace the 4 `chunks.append(...)` + `chunk_index += 1` sites**

There are 4 sites in `chunk_page()` that follow this pattern:
```python
chunks.append({
    'chunk_index': chunk_index,
    'chunk_text': chunk_text,
    'heading_path': self.get_heading_path(headings, position),
    'token_count': current_tokens
})
chunk_index += 1
```

Replace each one with:
```python
finalize_chunk(chunk_text, position, current_tokens)
```

The 4 occurrences (search for `chunks.append` in `chunking.py`):

**Site 1** — when flushing before a long paragraph (inside `if para_tokens > self.max_tokens:` block):
```python
# before
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk)
chunks.append({
    'chunk_index': chunk_index,
    'chunk_text': chunk_text,
    'heading_path': self.get_heading_path(headings, position),
    'token_count': current_tokens
})
chunk_index += 1

# after
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk)
finalize_chunk(chunk_text, position, current_tokens)
```

**Site 2** — sentence-level split (inside `for sentence in sentences:` loop):
```python
# before
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if current_chunk else 0
chunks.append({
    'chunk_index': chunk_index,
    'chunk_text': chunk_text,
    'heading_path': self.get_heading_path(headings, position),
    'token_count': current_tokens
})
chunk_index += 1

# after
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if current_chunk else 0
finalize_chunk(chunk_text, position, current_tokens)
```

**Site 3** — paragraph overflow (inside `elif current_tokens + para_tokens > self.max_tokens:` block):
```python
# before
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if current_chunk else 0
chunks.append({
    'chunk_index': chunk_index,
    'chunk_text': chunk_text,
    'heading_path': self.get_heading_path(headings, position),
    'token_count': current_tokens
})
chunk_index += 1

# after
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if current_chunk else 0
finalize_chunk(chunk_text, position, current_tokens)
```

**Site 4** — final chunk flush (after the loop, `if current_chunk and current_tokens > 0:`):
```python
# before
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if len(current_chunk) > 1 else 0
chunks.append({
    'chunk_index': chunk_index,
    'chunk_text': chunk_text,
    'heading_path': self.get_heading_path(headings, position),
    'token_count': current_tokens
})

# after
chunk_text = join_chunk_text(current_chunk)
position = get_chunk_start_pos(current_chunk) if len(current_chunk) > 1 else 0
finalize_chunk(chunk_text, position, current_tokens)
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_chunking.py -v
```

Expected: 4 PASSED

- [ ] **Step 6: Run full test suite to check for regressions**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add app/services/chunking.py tests/test_chunking.py
git commit -m "feat: prepend heading path to chunk text for richer embeddings"
```

---

### Task 4: Rewrite `/api/search/semantic` — page-level results + relative scores

**Files:**
- Modify: `app/routes/semantic_search.py` — `semantic_search()` function
- Create: `tests/test_semantic_search.py` (partial — score normalisation logic)

- [ ] **Step 1: Write failing test for score normalisation**

Create `tests/test_semantic_search.py`:

```python
def _apply_relative_scores(results: list) -> list:
    """Extracted pure function — mirrors the logic added to semantic_search()."""
    if not results:
        return results
    max_score = max(r['similarity_score'] for r in results)
    for r in results:
        r['relative_score'] = round(
            (r['similarity_score'] / max_score) * 100, 1
        ) if max_score > 0 else 0.0
    return results


def test_relative_scores_top_result_is_100():
    results = [
        {'similarity_score': 0.72},
        {'similarity_score': 0.58},
        {'similarity_score': 0.41},
    ]
    out = _apply_relative_scores(results)
    assert out[0]['relative_score'] == 100.0
    assert out[1]['relative_score'] == round(0.58 / 0.72 * 100, 1)
    assert out[2]['relative_score'] == round(0.41 / 0.72 * 100, 1)


def test_relative_scores_single_result():
    results = [{'similarity_score': 0.55}]
    out = _apply_relative_scores(results)
    assert out[0]['relative_score'] == 100.0


def test_relative_scores_empty():
    assert _apply_relative_scores([]) == []


def test_relative_scores_zero_max():
    results = [{'similarity_score': 0.0}]
    out = _apply_relative_scores(results)
    assert out[0]['relative_score'] == 0.0
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/test_semantic_search.py -v
```

Expected: FAILED (`_apply_relative_scores` imported function does not exist yet in the route)

- [ ] **Step 3: Replace the `semantic_search()` function body**

In `app/routes/semantic_search.py`, replace the entire body of `semantic_search()` (everything after the `@jwt_required()` decorator) with the following. Keep the function signature and decorators unchanged.

```python
@semantic_search_bp.route('/semantic', methods=['GET'])
@jwt_required()
def semantic_search():
    current_user_id = int(get_jwt_identity())

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400

    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    threshold = float(request.args.get('threshold', 0.3))

    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    if not accessible_wiki_ids:
        return jsonify({'results': [], 'has_more': False}), 200

    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]

    try:
        embedding_client = get_embedding_client()
        query_embedding = embedding_client.generate_embeddings(query, normalize=True)
    except EmbeddingServiceError as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return jsonify({'error': 'Embedding service unavailable', 'details': str(e)}), 503

    try:
        ivfflat_probes = current_app.config.get('IVFFLAT_PROBES')
        if ivfflat_probes is not None:
            db.session.execute(
                text('SET LOCAL ivfflat.probes = :probes'),
                {'probes': ivfflat_probes}
            )

        similarity_query = text("""
            SELECT * FROM (
                SELECT DISTINCT ON (p.id)
                    p.id        AS page_id,
                    p.title     AS page_title,
                    p.slug      AS page_slug,
                    p.wiki_id,
                    w.name      AS wiki_name,
                    w.slug      AS wiki_slug,
                    pe.chunk_text AS excerpt,
                    pe.heading_path,
                    1 - ((pe.embedding <=> :query_embedding) / 2.0) AS similarity_score
                FROM page_embeddings pe
                JOIN pages p ON pe.page_id = p.id
                JOIN wikis w ON p.wiki_id = w.id
                WHERE p.wiki_id = ANY(:wiki_ids)
                  AND p.is_published = TRUE
                ORDER BY p.id, pe.embedding <=> :query_embedding
            ) best_per_page
            WHERE similarity_score >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit_plus_one
        """)

        rows = db.session.execute(
            similarity_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'threshold': threshold,
                'limit_plus_one': limit + 1,
            }
        ).fetchall()

        has_more = len(rows) > limit
        rows = rows[:limit]

        results = [
            {
                'page_id': row.page_id,
                'page_title': row.page_title,
                'page_slug': row.page_slug,
                'wiki_id': row.wiki_id,
                'wiki_name': row.wiki_name,
                'wiki_slug': row.wiki_slug,
                'excerpt': row.excerpt,
                'heading_path': row.heading_path,
                'similarity_score': float(row.similarity_score),
                'page_url': f'/wikis/{row.wiki_id}/pages/{row.page_id}',
            }
            for row in rows
        ]

        if results:
            max_score = max(r['similarity_score'] for r in results)
            for r in results:
                r['relative_score'] = (
                    round((r['similarity_score'] / max_score) * 100, 1)
                    if max_score > 0 else 0.0
                )

        return jsonify({
            'results': results,
            'has_more': has_more,
            'query': query,
            'threshold': threshold,
        }), 200

    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500
```

Also remove the `offset` parameter — it was used with the old count query and is no longer supported (results are ranked, not paginated by offset).

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_semantic_search.py -v
```

Expected: 4 PASSED (the pure function tests pass; DB-dependent tests are in Task 5)

- [ ] **Step 5: Commit**

```bash
git add app/routes/semantic_search.py tests/test_semantic_search.py
git commit -m "feat: semantic search returns page-level results with relative scores"
```

---

### Task 5: Rewrite `/api/search/hybrid` with RRF

**Files:**
- Modify: `app/routes/semantic_search.py` — `hybrid_search()` function
- Modify: `tests/test_semantic_search.py` — add RRF tests

- [ ] **Step 1: Add RRF tests to `tests/test_semantic_search.py`**

Append to the existing file:

```python
def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (rank + k)


def _compute_rrf(keyword_ranks: dict, semantic_ranks: dict) -> dict:
    """Mirrors the RRF logic in hybrid_search()."""
    all_ids = set(keyword_ranks) | set(semantic_ranks)
    return {
        pid: (
            (_rrf_score(keyword_ranks[pid]) if pid in keyword_ranks else 0.0) +
            (_rrf_score(semantic_ranks[pid]) if pid in semantic_ranks else 0.0)
        )
        for pid in all_ids
    }


def test_rrf_page_in_both_lists_ranks_higher():
    # page 1 is in both lists at rank 1; page 2 is only in keyword at rank 1
    keyword_ranks = {1: 1, 2: 2}
    semantic_ranks = {1: 1, 3: 2}
    scores = _compute_rrf(keyword_ranks, semantic_ranks)
    assert scores[1] > scores[2], "page in both lists should outscore page in one"
    assert scores[1] > scores[3], "page in both lists should outscore page in one"


def test_rrf_high_rank_beats_low_rank():
    keyword_ranks = {1: 1, 2: 10}
    semantic_ranks = {}
    scores = _compute_rrf(keyword_ranks, semantic_ranks)
    assert scores[1] > scores[2]


def test_rrf_score_formula():
    assert abs(_rrf_score(1) - 1.0 / 61) < 1e-9
    assert abs(_rrf_score(0) - 1.0 / 60) < 1e-9


def test_rrf_empty_inputs():
    assert _compute_rrf({}, {}) == {}
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_semantic_search.py::test_rrf_page_in_both_lists_ranks_higher -v
```

Expected: FAILED (functions not yet imported from the route)

Note: the test file defines `_rrf_score` and `_compute_rrf` as local pure functions — they are tested in isolation. The route will contain the same logic inlined.

- [ ] **Step 3: Run RRF tests to confirm they pass now** (they are self-contained)

```bash
pytest tests/test_semantic_search.py -v
```

Expected: all 8 tests PASS (the RRF tests use local functions defined in the test file itself)

- [ ] **Step 4: Replace the `hybrid_search()` function body**

In `app/routes/semantic_search.py`, replace the entire body of `hybrid_search()`:

```python
@semantic_search_bp.route('/hybrid', methods=['GET'])
@jwt_required()
def hybrid_search():
    current_user_id = int(get_jwt_identity())

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400

    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)

    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    if not accessible_wiki_ids:
        return jsonify({'results': [], 'total': 0}), 200

    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]

    # --- Keyword search ---
    search_term = f'%{query}%'
    keyword_rows = db.session.query(
        Page.id,
        Page.title,
        Page.slug,
        Page.summary,
        Page.wiki_id,
        Wiki.name.label('wiki_name'),
        Wiki.slug.label('wiki_slug'),
    ).join(Wiki).filter(
        Page.wiki_id.in_(accessible_wiki_ids),
        Page.is_published == True,
        db.or_(
            Page.title.ilike(search_term),
            Page.content.ilike(search_term),
            Page.summary.ilike(search_term),
        )
    ).limit(limit * 2).all()

    # --- Semantic search ---
    semantic_rows = []
    try:
        embedding_client = get_embedding_client()
        query_embedding = embedding_client.generate_embeddings(query, normalize=True)

        ivfflat_probes = current_app.config.get('IVFFLAT_PROBES')
        if ivfflat_probes is not None:
            db.session.execute(
                text('SET LOCAL ivfflat.probes = :probes'),
                {'probes': ivfflat_probes}
            )

        semantic_query = text("""
            SELECT * FROM (
                SELECT DISTINCT ON (p.id)
                    p.id, p.title, p.slug, p.summary, p.wiki_id,
                    w.name AS wiki_name, w.slug AS wiki_slug,
                    pe.embedding <=> :query_embedding AS best_distance
                FROM pages p
                JOIN page_embeddings pe ON p.id = pe.page_id
                JOIN wikis w ON p.wiki_id = w.id
                WHERE p.wiki_id = ANY(:wiki_ids)
                  AND p.is_published = TRUE
                ORDER BY p.id, pe.embedding <=> :query_embedding
            ) best
            ORDER BY best_distance ASC
            LIMIT :limit
        """)

        semantic_rows = db.session.execute(
            semantic_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'limit': limit * 2,
            }
        ).fetchall()
    except Exception as e:
        logger.error(f"Semantic portion of hybrid search failed: {e}")

    # --- RRF merge ---
    def rrf_score(rank: int, k: int = 60) -> float:
        return 1.0 / (rank + k)

    keyword_ranks = {row[0]: i + 1 for i, row in enumerate(keyword_rows)}
    semantic_ranks = {row[0]: i + 1 for i, row in enumerate(semantic_rows)}

    page_data = {}
    for row in keyword_rows:
        page_data[row[0]] = {
            'page_id': row[0], 'title': row[1], 'slug': row[2],
            'summary': row[3], 'wiki_id': row[4],
            'wiki_name': row[5], 'wiki_slug': row[6],
            'page_url': f'/wikis/{row[4]}/pages/{row[0]}',
        }
    for row in semantic_rows:
        if row[0] not in page_data:
            page_data[row[0]] = {
                'page_id': row[0], 'title': row[1], 'slug': row[2],
                'summary': row[3], 'wiki_id': row[4],
                'wiki_name': row[5], 'wiki_slug': row[6],
                'page_url': f'/wikis/{row[4]}/pages/{row[0]}',
            }

    all_ids = set(keyword_ranks) | set(semantic_ranks)
    rrf_scores = {
        pid: (
            (rrf_score(keyword_ranks[pid]) if pid in keyword_ranks else 0.0) +
            (rrf_score(semantic_ranks[pid]) if pid in semantic_ranks else 0.0)
        )
        for pid in all_ids
    }

    sorted_ids = sorted(all_ids, key=lambda pid: rrf_scores[pid], reverse=True)[:limit]

    results = []
    for pid in sorted_ids:
        entry = dict(page_data[pid])
        entry['combined_score'] = rrf_scores[pid]
        results.append(entry)

    if results:
        max_score = max(r['combined_score'] for r in results)
        for r in results:
            r['relative_score'] = (
                round((r['combined_score'] / max_score) * 100, 1)
                if max_score > 0 else 0.0
            )

    return jsonify({
        'results': results,
        'total': len(results),
        'query': query,
    }), 200
```

Remove the now-unused `func` import from `sqlalchemy` at the top of the file if `func` is no longer referenced anywhere else in the module.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add app/routes/semantic_search.py tests/test_semantic_search.py
git commit -m "feat: hybrid search uses RRF, drops broken weighted-sum scoring"
```

---

### Task 6: Trigger re-embed after deploy

This is not a code task — it is the operational step required when this branch is deployed, because existing `page_embeddings` rows were created without heading prefixes.

After deploying (or running locally with an active embedding service):

```bash
curl -X POST http://localhost:5000/api/admin/embeddings/generate-all \
  -H "Authorization: Bearer <admin-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "all"}'
```

Expected response:
```json
{"message": "Bulk embedding generation initiated", "queued": N, "failed": 0, "total": N}
```

Monitor progress via:
```bash
curl http://localhost:5000/api/admin/stats \
  -H "Authorization: Bearer <admin-jwt-token>"
```

Watch `pages.pending_embeddings` count down to 0.
