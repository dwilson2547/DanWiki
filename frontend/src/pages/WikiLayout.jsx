import { useState, useEffect } from 'react';
import { Outlet, Link, useParams, useNavigate } from 'react-router-dom';
import { 
  ChevronLeft, Plus, Settings, Home, FileText, 
  Search as SearchIcon, Menu, X, Book, ArrowLeft
} from 'lucide-react';
import { wikisAPI, pagesAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageTree from '../components/PageTree';
import Search from '../components/Search';
import Modal from '../components/Modal';
import UserMenu from '../components/UserMenu';
import ParentPageSelect from '../components/ParentPageSelect';

export default function WikiLayout() {
  const { wikiId } = useParams();
  const [wiki, setWiki] = useState(null);
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('wikiSidebarWidth');
    return saved ? parseInt(saved, 10) : 260;
  });
  const [isResizing, setIsResizing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPage, setNewPage] = useState({ title: '', parent_id: null });
  const [creating, setCreating] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadWikiData();
  }, [wikiId]);

  // Save sidebar width to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('wikiSidebarWidth', sidebarWidth.toString());
  }, [sidebarWidth]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = e.clientX;
      if (newWidth >= 200 && newWidth <= 600) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  const loadWikiData = async () => {
    setLoading(true);
    try {
      const [wikiRes, pagesRes] = await Promise.all([
        wikisAPI.get(wikiId),
        pagesAPI.list(wikiId, 'tree')
      ]);
      setWiki(wikiRes.data.wiki);
      setPages(pagesRes.data.pages);
    } catch (err) {
      console.error('Failed to load wiki:', err);
      if (err.response?.status === 404) {
        navigate('/');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePage = async (e) => {
    e.preventDefault();
    setCreating(true);

    try {
      const response = await pagesAPI.create(wikiId, {
        title: newPage.title,
        parent_id: newPage.parent_id,
        content: ''
      });
      
      // Reload pages to get updated tree
      const pagesRes = await pagesAPI.list(wikiId, 'tree');
      setPages(pagesRes.data.pages);
      
      setShowCreateModal(false);
      setNewPage({ title: '', parent_id: null });
      
      // Navigate to the new page in edit mode
      navigate(`/wiki/${wikiId}/page/${response.data.page.id}/edit`);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to create page');
    } finally {
      setCreating(false);
    }
  };

  const refreshPages = async () => {
    const pagesRes = await pagesAPI.list(wikiId, 'tree');
    setPages(pagesRes.data.pages);
  };

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }

  // Flatten pages for parent select
  const flattenPages = (pages, level = 0) => {
    let result = [];
    for (const page of pages) {
      result.push({ ...page, level });
      if (page.children) {
        result = result.concat(flattenPages(page.children, level + 1));
      }
    }
    return result;
  };
  const flatPages = flattenPages(pages);

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
        <div style={{ maxWidth: 1600, margin: '0 auto', padding: '0 2rem' }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                title="Toggle sidebar"
              >
                <Menu size={20} />
              </button>
              <Book size={28} style={{ color: 'var(--primary)' }} />
              <div>
                <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                  <a href={`/wiki/${wiki?.id}`}>{wiki?.name}</a>
                </h1>
              </div>
            </div>
            <div className="flex gap-2 items-center">
              <Link to="/dashboard" className="btn btn-ghost">
                <ArrowLeft size={18} />
                My Wikis
              </Link>
              <Link to="/" className="btn btn-ghost">
                <Home size={18} />
                Home
              </Link>
              <Link 
                to={`/wiki/${wikiId}/settings`}
                className="btn btn-ghost"
              >
                <Settings size={18} />
                Wiki Settings
              </Link>
              <button
                className="btn btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={18} />
                New Page
              </button>
              <UserMenu />
            </div>
          </div>
        </div>
      </header>

      <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? '' : 'hidden'}`} style={{
        width: `${sidebarWidth}px`,
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: isResizing ? 'none' : 'transform 0.2s ease'
      }}>
        <div className="sidebar-header">
          <h2 className="font-semibold" style={{ fontSize: '1.125rem' }}>
            Pages
          </h2>
        </div>

        <div className="px-4 py-2">
          <Search wikiId={wikiId} placeholder="Search pages..." />
        </div>

        <div className="sidebar-content">
          <PageTree pages={pages} wikiId={wikiId} />
        </div>
        
        {/* Resize handle */}
        <div 
          className="sidebar-resize-handle"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
          title="Drag to resize sidebar"
        />
      </aside>

      {/* Main content */}
      <main className="main-content" style={{
        marginLeft: sidebarOpen ? `${sidebarWidth}px` : '0',
        width: sidebarOpen ? `calc(100% - ${sidebarWidth}px)` : '100%',
        transition: isResizing ? 'none' : 'margin-left 0.2s ease, width 0.2s ease'
      }}>
        <Outlet context={{ wiki, pages, refreshPages }} />
      </main>
    </div>

      {/* Create Page Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Page"
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowCreateModal(false)}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleCreatePage}
              disabled={creating || !newPage.title.trim()}
            >
              {creating ? 'Creating...' : 'Create Page'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreatePage}>
          <div className="form-group">
            <label className="form-label">Page Title</label>
            <input
              type="text"
              className="form-input"
              value={newPage.title}
              onChange={(e) => setNewPage({ ...newPage, title: e.target.value })}
              placeholder="Getting Started"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Parent Page (optional)</label>
            <ParentPageSelect
              pages={pages}
              value={newPage.parent_id}
              onChange={(value) => setNewPage({ ...newPage, parent_id: value })}
              placeholder="None (top level)"
            />
          </div>
        </form>
      </Modal>
    </div>
  );
}
