import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BookOpen, Globe, User, Calendar, Search as SearchIcon, LogIn, UserPlus } from 'lucide-react';
import { wikisAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  const loadPublicWikis = async () => {
    setLoading(true);
    setError('');
    try {
      const params = { group_by: 'author' };
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      const response = await wikisAPI.listPublic(params);
      setAuthors(response.data.authors || []);
    } catch (err) {
      console.error('Failed to load public wikis:', err);
      setError('Failed to load public wikis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search
    const timer = setTimeout(() => {
      loadPublicWikis();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{ 
        borderBottom: '1px solid var(--border)',
        background: 'var(--card)',
        padding: '1rem 0',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2rem' }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <BookOpen size={32} style={{ color: 'var(--primary)' }} />
              <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
                Wiki Explorer
              </h1>
            </div>
            <div className="flex gap-2">
              {user ? (
                <button 
                  className="btn btn-primary"
                  onClick={() => navigate('/dashboard')}
                >
                  My Dashboard
                </button>
              ) : (
                <>
                  <Link to="/login" className="btn btn-secondary">
                    <LogIn size={18} />
                    Sign In
                  </Link>
                  <Link to="/register" className="btn btn-primary">
                    <UserPlus size={18} />
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{ 
        background: 'linear-gradient(135deg, var(--primary-light, #e0e7ff) 0%, var(--primary-lighter, #f5f7ff) 100%)',
        padding: '3rem 0',
        borderBottom: '1px solid var(--border)'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2rem', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '1rem' }}>
            Discover Public Wikis
          </h2>
          <p style={{ fontSize: '1.125rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            Explore knowledge bases created by our community
          </p>
          
          {/* Search Bar */}
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <div style={{ position: 'relative' }}>
              <SearchIcon 
                size={20} 
                style={{ 
                  position: 'absolute', 
                  left: '1rem', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)'
                }} 
              />
              <input
                type="text"
                className="form-input"
                placeholder="Search wikis by name or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '3rem', fontSize: '1rem' }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '3rem 2rem' }}>
        {error && (
          <div className="alert alert-error" style={{ marginBottom: '2rem' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div className="loading-container" style={{ padding: '4rem 0' }}>
            <div className="spinner" />
          </div>
        ) : authors.length === 0 ? (
          <div className="empty-state" style={{ padding: '4rem 0' }}>
            <Globe size={64} className="empty-state-icon" style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <h3 className="font-semibold mb-2" style={{ fontSize: '1.5rem' }}>
              {searchTerm ? 'No wikis found' : 'No public wikis yet'}
            </h3>
            <p className="text-secondary">
              {searchTerm 
                ? 'Try adjusting your search terms' 
                : 'Be the first to create and share a public wiki!'}
            </p>
          </div>
        ) : (
          <div>
            <p className="text-secondary mb-6" style={{ fontSize: '0.875rem' }}>
              Found {authors.length} {authors.length === 1 ? 'author' : 'authors'} with public wikis
            </p>

            {/* Authors & Their Wikis */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
              {authors.map((author) => (
                <div key={author.author.id} className="author-section">
                  {/* Author Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div style={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      background: 'var(--primary-light, #e0e7ff)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.25rem',
                      fontWeight: 600,
                      color: 'var(--primary)'
                    }}>
                      {author.author.avatar_url ? (
                        <img 
                          src={author.author.avatar_url} 
                          alt={author.author.display_name}
                          style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
                        />
                      ) : (
                        author.author.display_name.charAt(0).toUpperCase()
                      )}
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0 }}>
                        {author.author.display_name}
                      </h3>
                      <p className="text-secondary" style={{ fontSize: '0.875rem', margin: 0 }}>
                        {author.wikis.length} {author.wikis.length === 1 ? 'wiki' : 'wikis'}
                      </p>
                    </div>
                  </div>

                  {/* Author's Wikis */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
                    gap: '1rem',
                    marginLeft: '3.75rem'
                  }}>
                    {author.wikis.map((wiki) => (
                      <Link
                        key={wiki.id}
                        to={user ? `/wiki/${wiki.id}` : '/login'}
                        className="card wiki-card"
                        style={{ 
                          textDecoration: 'none', 
                          color: 'var(--text)',
                          transition: 'all 0.2s',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '';
                        }}
                      >
                        <div className="card-body">
                          <div className="flex items-start justify-between mb-2">
                            <h4 style={{ 
                              fontSize: '1.125rem', 
                              fontWeight: 600, 
                              margin: 0,
                              color: 'var(--primary)',
                              flex: 1
                            }}>
                              {wiki.name}
                            </h4>
                            <Globe size={18} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                          </div>
                          <p className="text-secondary" style={{ 
                            fontSize: '0.875rem',
                            margin: '0.5rem 0',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            minHeight: '2.5rem'
                          }}>
                            {wiki.description || 'No description available'}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-secondary" style={{ marginTop: '0.75rem' }}>
                            <Calendar size={14} />
                            <span>Updated {new Date(wiki.updated_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{ 
        borderTop: '1px solid var(--border)',
        padding: '2rem 0',
        marginTop: '4rem',
        textAlign: 'center',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2rem' }}>
          <p style={{ fontSize: '0.875rem', margin: 0 }}>
            Wiki Explorer - Share your knowledge with the world
          </p>
        </div>
      </footer>
    </div>
  );
}
