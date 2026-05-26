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


def test_sibling_headings_do_not_nest():
    # Use a small max_tokens so Setup and Usage sections end up in separate chunks.
    small_chunker = TextChunker(
        max_tokens=10,
        overlap_tokens=2,
        model_name='sentence-transformers/all-MiniLM-L6-v2'
    )
    content = "## Setup\n\nInstall deps.\n\n## Usage\n\nRun the server."
    chunks = small_chunker.chunk_page("Guide", content)
    usage_chunks = [c for c in chunks if 'Usage' in c.get('heading_path', '')]
    assert len(usage_chunks) > 0
    for chunk in usage_chunks:
        assert chunk['heading_path'] == 'Usage', f"Expected 'Usage', got '{chunk['heading_path']}'"
        assert '[Setup' not in chunk['chunk_text']
