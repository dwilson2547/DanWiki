import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search as SearchIcon, X, Zap, BookOpen, Hash } from 'lucide-react';
import { searchAPI } from '../services/api';

/**
 * SemanticSearch Component
 * 
 * A reusable AI-powered semantic search component with multiple modes:
 * - Semantic: Pure vector similarity search
 * - Hybrid: Combines keyword and semantic search
 * - Keyword: Traditional text search
 */
export default function SemanticSearch({ 
  wikiId = null, 
  placeholder = 'Search with AI...', 
  defaultMode = 'semantic',
  showModeToggle = true,
  onResultClick = null,
  className = ''
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState(defaultMode); // 'semantic', 'hybrid', 'keyword'
  const [semanticWeight, setSemanticWeight] = useState(0.7);
  const [threshold, setThreshold] = useState(0.5);
  const [showSettings, setShowSettings] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const performSearch = async () => {
      if (query.length < 2) {
        setResults([]);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        let response;
        
        switch (searchMode) {
          case 'semantic':
            response = await searchAPI.semanticSearch(query, wikiId, 20, 0, threshold);
            // Transform semantic results to match UI format
            setResults(response.data.results.map(r => ({
              ...r,
              similarity_score: r.similarity_score,
              chunk_preview: r.chunk_text,
              heading: r.heading_path
            })));
            break;
            
          case 'hybrid':
            response = await searchAPI.hybridSearch(query, wikiId, 20, semanticWeight);
            setResults(response.data.results);
            break;
            
          case 'keyword':
            response = await searchAPI.searchPages(query, wikiId);
            setResults(response.data.pages || []);
            break;
            
          default:
            throw new Error('Invalid search mode');
        }
      } catch (err) {
        console.error('Search failed:', err);
        setError(err.response?.data?.error || 'Search failed. Please try again.');
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(performSearch, 400);
    return () => clearTimeout(debounce);
  }, [query, searchMode, wikiId, semanticWeight, threshold]);

  const handleResultClick = (result) => {
    if (onResultClick) {
      onResultClick(result);
    } else {
      const wikiIdToUse = result.wiki_id || wikiId;
      navigate(`/wiki/${wikiIdToUse}/page/${result.page_id}`);
    }
    setQuery('');
    setResults([]);
  };

  const getModeIcon = (mode) => {
    switch (mode) {
      case 'semantic': return <Sparkles size={14} />;
      case 'hybrid': return <Zap size={14} />;
      case 'keyword': return <SearchIcon size={14} />;
      default: return null;
    }
  };

  const getModeLabel = (mode) => {
    switch (mode) {
      case 'semantic': return 'AI Search';
      case 'hybrid': return 'Hybrid';
      case 'keyword': return 'Keyword';
      default: return mode;
    }
  };

  return (
    <div className={`semantic-search-container ${className}`}>
      <div className="search-header">
        <div className="search-input-wrapper">
          <Sparkles size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button
              className="btn btn-ghost btn-icon btn-sm search-query-clear"
              onClick={() => {
                setQuery('');
                setResults([]);
                setError(null);
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {showModeToggle && (
          <div className="search-mode-toggle">
            {['semantic', 'hybrid', 'keyword'].map(mode => (
              <button
                key={mode}
                className={`btn btn-sm ${searchMode === mode ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setSearchMode(mode)}
                title={getModeLabel(mode)}
              >
                {getModeIcon(mode)}
                <span className="ml-1">{getModeLabel(mode)}</span>
              </button>
            ))}
            <button
              className="btn btn-ghost btn-icon btn-sm"
              onClick={() => setShowSettings(!showSettings)}
              title="Search settings"
            >
              ⚙️
            </button>
          </div>
        )}
      </div>

      {/* Advanced Settings */}
      {showSettings && (
        <div className="search-settings card p-3 mt-2">
          <h4 className="text-sm font-semibold mb-2">Search Settings</h4>
          
          {searchMode === 'semantic' && (
            <div className="setting-group">
              <label className="text-xs text-secondary">
                Similarity Threshold: {threshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0.3"
                max="0.9"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-secondary mt-1">
                Higher = more strict matching
              </p>
            </div>
          )}
          
          {searchMode === 'hybrid' && (
            <div className="setting-group">
              <label className="text-xs text-secondary">
                AI Weight: {(semanticWeight * 100).toFixed(0)}% / Keyword: {((1 - semanticWeight) * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={semanticWeight}
                onChange={(e) => setSemanticWeight(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-secondary mt-1">
                Balance between AI and keyword matching
              </p>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="alert alert-error mt-2">
          {error}
        </div>
      )}

      {/* Results */}
      {query.length >= 2 && (
        <div className="search-results mt-2">
          {loading && (
            <div className="p-4 text-center">
              <div className="spinner" style={{ margin: '0 auto' }} />
              <p className="text-sm text-secondary mt-2">
                {searchMode === 'semantic' ? 'Analyzing with AI...' : 'Searching...'}
              </p>
            </div>
          )}

          {!loading && results.length === 0 && !error && (
            <div className="p-4 text-center">
              <SearchIcon size={32} className="mx-auto mb-2 text-secondary opacity-50" />
              <p className="text-sm text-secondary">No results found</p>
              <p className="text-xs text-secondary mt-1">Try adjusting your search or settings</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="results-list">
              {results.map((result, index) => (
                <div
                  key={`${result.page_id || result.id}-${index}`}
                  className="search-result-item"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="result-header">
                    <div className="flex items-center gap-2">
                      <BookOpen size={16} className="text-primary" />
                      <h4 className="result-title">{result.page_title || result.title}</h4>
                    </div>
                    {(result.similarity_score || result.combined_score) && (
                      <div className="result-score">
                        <div 
                          className="score-bar" 
                          style={{ 
                            width: `${(result.similarity_score || result.combined_score || 0) * 100}%`,
                            background: `hsl(${(result.similarity_score || result.combined_score) * 120}, 70%, 50%)`
                          }}
                        />
                        <span className="score-text">
                          {((result.similarity_score || result.combined_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>

                  {result.heading_path && (
                    <div className="result-breadcrumb">
                      <Hash size={12} />
                      <span>{result.heading_path}</span>
                    </div>
                  )}

                  <p className="result-content">
                    {result.chunk_text || result.summary || result.content?.substring(0, 200) || 'No preview available'}
                  </p>

                  <div className="result-meta">
                    <span className="wiki-name">{result.wiki_name}</span>
                    {searchMode === 'hybrid' && result.semantic_score > 0 && (
                      <span className="badge badge-sm">
                        <Sparkles size={10} className="mr-1" />
                        AI Match
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
