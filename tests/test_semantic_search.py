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
