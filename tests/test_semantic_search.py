"""
Pure function tests for semantic search result processing.

These tests are self-contained and do not require a running database
or any imports from the route module.
"""


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
