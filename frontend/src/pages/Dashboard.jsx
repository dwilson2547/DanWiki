import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Book, Lock, Globe, MoreVertical, Trash2, Settings, Home, Sparkles, Upload, FileArchive } from 'lucide-react';
import { wikisAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';
import Search from '../components/Search';
import UserMenu from '../components/UserMenu';

export default function Dashboard() {
  const [wikis, setWikis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWiki, setNewWiki] = useState({ name: '', description: '', is_public: false });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(null);
  
  // Bulk import state
  const [importMode, setImportMode] = useState(false); // false = manual, true = import from archive
  const [archiveFile, setArchiveFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [importResult, setImportResult] = useState(null);
  
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadWikis();
  }, []);

  const loadWikis = async () => {
    try {
      const response = await wikisAPI.list();
      setWikis(response.data.wikis);
    } catch (err) {
      console.error('Failed to load wikis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWiki = async (e) => {
    e.preventDefault();
    setError('');
    setCreating(true);
    setImportResult(null);

    try {
      if (importMode && archiveFile) {
        // Import from archive
        const formData = new FormData();
        formData.append('archive', archiveFile);
        formData.append('name', newWiki.name);
        if (newWiki.description) formData.append('description', newWiki.description);
        formData.append('is_public', newWiki.is_public.toString());
        
        const response = await wikisAPI.importArchive(formData, (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        });
        
        setImportResult(response.data.import_result);
        setWikis([...wikis, response.data.wiki]);
        
        // Show result modal for a moment before navigating
        setTimeout(() => {
          setShowCreateModal(false);
          resetForm();
          navigate(`/wiki/${response.data.wiki.id}`);
        }, 2000);
      } else {
        // Create empty wiki
        const response = await wikisAPI.create(newWiki);
        setWikis([...wikis, response.data.wiki]);
        setShowCreateModal(false);
        resetForm();
        navigate(`/wiki/${response.data.wiki.id}`);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create wiki');
      setImportResult(err.response?.data?.details || null);
    } finally {
      setCreating(false);
      setUploadProgress(0);
    }
  };
  
  const resetForm = () => {
    setNewWiki({ name: '', description: '', is_public: false });
    setImportMode(false);
    setArchiveFile(null);
    setUploadProgress(0);
    setImportResult(null);
    setError('');
  };
  
  const handleArchiveFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const validExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
      const fileName = file.name.toLowerCase();
      const isValid = validExtensions.some(ext => fileName.endsWith(ext));
      
      if (!isValid) {
        setError('Invalid file type. Please upload a .zip or .tar.gz file');
        setArchiveFile(null);
        return;
      }
      
      // Validate file size (500MB max)
      const maxSize = 500 * 1024 * 1024;
      if (file.size > maxSize) {
        setError(`File too large. Maximum size is 500MB (${(file.size / (1024 * 1024)).toFixed(1)}MB)`);
        setArchiveFile(null);
        return;
      }
      
      setArchiveFile(file);
      setError('');
    }
  };

  const handleDeleteWiki = async (wikiId) => {
    if (!confirm('Are you sure you want to delete this wiki? All pages will be deleted.')) {
      return;
    }

    try {
      await wikisAPI.delete(wikiId);
      setWikis(wikis.filter(w => w.id !== wikiId));
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete wiki');
    }
    setDropdownOpen(null);
  };

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
              <Book size={32} style={{ color: 'var(--primary)' }} />
              <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
                My Wikis
              </h1>
            </div>
            <div className="flex gap-2 items-center">
              <Link to="/search" className="btn btn-ghost">
                <Sparkles size={18} />
                AI Search
              </Link>
              <Link to="/" className="btn btn-ghost">
                <Home size={18} />
                Explore Public Wikis
              </Link>
              <button 
                className="btn btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={18} />
                New Wiki
              </button>
              <UserMenu />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
        <div className="mb-4">
          <p className="text-secondary text-sm mb-4">
            Welcome back, {user?.display_name || user?.username}
          </p>
          <div style={{ maxWidth: 400 }}>
            <Search placeholder="Search across all wikis..." />
          </div>
        </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
        </div>
      ) : wikis.length === 0 ? (
        <div className="empty-state">
          <Book size={48} className="empty-state-icon" style={{ margin: '0 auto' }} />
          <h3 className="font-semibold mb-2">No wikis yet</h3>
          <p className="text-secondary mb-4">Create your first wiki to get started</p>
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={18} />
            Create Wiki
          </button>
        </div>
      ) : (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
          gap: '1rem' 
        }}>
          {wikis.map(wiki => (
            <div key={wiki.id} className="wiki-card">
              <div className="flex justify-between items-start mb-2">
                <Link 
                  to={`/wiki/${wiki.id}`}
                  className="wiki-card-title"
                  style={{ color: 'var(--text)', textDecoration: 'none' }}
                >
                  {wiki.name}
                </Link>
                <div className="dropdown">
                  <button 
                    className="btn btn-ghost btn-icon btn-sm"
                    onClick={() => setDropdownOpen(dropdownOpen === wiki.id ? null : wiki.id)}
                  >
                    <MoreVertical size={16} />
                  </button>
                  {dropdownOpen === wiki.id && (
                    <div className="dropdown-menu">
                      <Link 
                        to={`/wiki/${wiki.id}/settings`}
                        className="dropdown-item flex items-center gap-2"
                        onClick={() => setDropdownOpen(null)}
                      >
                        <Settings size={14} />
                        Settings
                      </Link>
                      <button 
                        className="dropdown-item dropdown-item-danger flex items-center gap-2"
                        onClick={() => handleDeleteWiki(wiki.id)}
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <p className="wiki-card-description">
                {wiki.description || 'No description'}
              </p>
              <div className="flex items-center gap-2 text-xs text-secondary">
                {wiki.is_public ? (
                  <>
                    <Globe size={14} />
                    <span>Public</span>
                  </>
                ) : (
                  <>
                    <Lock size={14} />
                    <span>Private</span>
                  </>
                )}
                <span>•</span>
                <span>Created {new Date(wiki.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      </main>

      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          resetForm();
        }}
        title="Create New Wiki"
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowCreateModal(false);
                resetForm();
              }}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleCreateWiki}
              disabled={creating || !newWiki.name.trim() || (importMode && !archiveFile)}
            >
              {creating ? (uploadProgress > 0 ? `Uploading... ${uploadProgress}%` : 'Creating...') : (importMode ? 'Import Wiki' : 'Create Wiki')}
            </button>
          </>
        }
      >
        {error && <div className="alert alert-error">{error}</div>}
        
        {importResult && (
          <div className={`alert ${importResult.failure_count > 0 ? 'alert-warning' : 'alert-success'}`}>
            <strong>Import completed!</strong>
            <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
              <li>{importResult.success_count} pages imported successfully</li>
              {importResult.attachments_created?.length > 0 && (
                <li>{importResult.attachments_created.length} attachments imported</li>
              )}
              {importResult.failure_count > 0 && (
                <li>{importResult.failure_count} items failed</li>
              )}
            </ul>
            {importResult.errors?.length > 0 && (
              <details style={{ marginTop: '0.5rem' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--error)' }}>View errors</summary>
                <ul style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
                  {importResult.errors.map((err, idx) => (
                    <li key={idx}>{err.item}: {err.error}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
        
        <form onSubmit={handleCreateWiki}>
          {/* Import mode toggle */}
          <div className="form-group" style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1rem' }}>
            <label className="form-label">Creation Method</label>
            <div className="flex gap-2">
              <button
                type="button"
                className={`btn ${!importMode ? 'btn-primary' : 'btn-secondary'} flex-1`}
                onClick={() => setImportMode(false)}
              >
                <Plus size={16} />
                Create Empty
              </button>
              <button
                type="button"
                className={`btn ${importMode ? 'btn-primary' : 'btn-secondary'} flex-1`}
                onClick={() => setImportMode(true)}
              >
                <FileArchive size={16} />
                Import Archive
              </button>
            </div>
          </div>
          
          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              type="text"
              className="form-input"
              value={newWiki.name}
              onChange={(e) => setNewWiki({ ...newWiki, name: e.target.value })}
              placeholder="My Knowledge Base"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description (optional)</label>
            <textarea
              className="form-input"
              value={newWiki.description}
              onChange={(e) => setNewWiki({ ...newWiki, description: e.target.value })}
              placeholder="What is this wiki about?"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={newWiki.is_public}
                onChange={(e) => setNewWiki({ ...newWiki, is_public: e.target.checked })}
              />
              <span className="text-sm">Make this wiki public</span>
            </label>
            <p className="text-xs text-secondary mt-1">
              Public wikis can be viewed by anyone with the link
            </p>
          </div>
          
          {/* Archive upload section */}
          {importMode && (
            <div className="form-group" style={{ 
              border: '2px dashed var(--border)', 
              borderRadius: '0.5rem', 
              padding: '1rem',
              background: 'var(--bg)'
            }}>
              <label className="form-label flex items-center gap-2">
                <Upload size={16} />
                Archive File (.zip, .tar.gz)
              </label>
              <input
                type="file"
                accept=".zip,.tar,.tar.gz,.tgz"
                onChange={handleArchiveFileChange}
                className="form-input"
                style={{ padding: '0.5rem' }}
              />
              {archiveFile && (
                <p className="text-sm text-secondary mt-2">
                  Selected: {archiveFile.name} ({(archiveFile.size / (1024 * 1024)).toFixed(2)} MB)
                </p>
              )}
              <p className="text-xs text-secondary mt-2">
                The archive will be extracted and pages will be created based on the directory structure.
                Markdown files (.md) become pages, directories map to hierarchy, and other files become attachments.
              </p>
              {uploadProgress > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ 
                    background: 'var(--border)', 
                    height: '8px', 
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{ 
                      background: 'var(--primary)', 
                      height: '100%', 
                      width: `${uploadProgress}%`,
                      transition: 'width 0.3s'
                    }} />
                  </div>
                  <p className="text-xs text-center mt-1">{uploadProgress}%</p>
                </div>
              )}
            </div>
          )}
        </form>
      </Modal>
    </div>
  );
}
