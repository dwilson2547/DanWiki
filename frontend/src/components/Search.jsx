import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, X } from 'lucide-react';
import { searchAPI } from '../services/api';

export default function Search({ wikiId = null, placeholder = 'Search pages...' }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const searchPages = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const response = wikiId
          ? await searchAPI.searchWikiPages(wikiId, query)
          : await searchAPI.searchPages(query);
        setResults(response.data.pages);
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(searchPages, 300);
    return () => clearTimeout(debounce);
  }, [query, wikiId]);

  const handleSelect = (page) => {
    navigate(`/wiki/${page.wiki_id}/page/${page.id}`);
    setQuery('');
    setIsOpen(false);
  };

  return (
    <div className="search-container" ref={containerRef}>
      <SearchIcon size={16} className="search-icon" />
      <input
        type="text"
        className="search-input"
        placeholder={placeholder}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
      />
      {query && (
        <button
          className="btn btn-ghost btn-icon btn-sm"
          style={{ position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)' }}
          onClick={() => {
            setQuery('');
            setResults([]);
          }}
        >
          <X size={14} />
        </button>
      )}
      
      {isOpen && query.length >= 2 && (
        <div className="search-results">
          {loading && (
            <div className="p-4 text-center">
              <div className="spinner" style={{ margin: '0 auto' }} />
            </div>
          )}
          
          {!loading && results.length === 0 && (
            <div className="p-4 text-center text-secondary text-sm">
              No results found
            </div>
          )}
          
          {!loading && results.map(page => (
            <div
              key={page.id}
              className="search-result-item"
              onClick={() => handleSelect(page)}
            >
              <div className="font-medium">{page.title}</div>
              {page.wiki && (
                <div className="text-xs text-secondary mt-1">
                  in {page.wiki.name}
                </div>
              )}
              {page.context && (
                <div className="text-sm text-secondary mt-1" style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical'
                }}>
                  {page.context}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
