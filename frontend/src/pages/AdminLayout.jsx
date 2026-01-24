import { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Users, Menu, Home, ArrowLeft, BarChart3, Database, BookOpen, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import UserMenu from '../components/UserMenu';

export default function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('adminSidebarWidth');
    return saved ? parseInt(saved, 10) : 260;
  });
  const [isResizing, setIsResizing] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if not admin
  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Save sidebar width to localStorage
  useEffect(() => {
    localStorage.setItem('adminSidebarWidth', sidebarWidth.toString());
  }, [sidebarWidth]);

  // Handle resize
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

  if (!user?.is_admin) {
    return null;
  }

  const isActive = (path) => location.pathname === path;

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
              <Shield size={28} style={{ color: 'var(--primary)' }} />
              <div>
                <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                  Admin Panel
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
          transition: isResizing ? 'none' : 'transform 0.2s ease',
          top: '65px'
        }}>
          <div className="sidebar-header">
            <h2 className="font-semibold" style={{ fontSize: '1.125rem'}}>
              Administration
            </h2>
          </div>

          <div className="sidebar-content">
            <nav>
              <Link 
                to="/admin"
                className={`nav-item ${isActive('/admin') ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive('/admin') ? 'var(--primary)' : 'var(--text)',
                  background: isActive('/admin') ? 'var(--primary-light)' : 'transparent',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                <BarChart3 size={20} />
                <span>Dashboard</span>
              </Link>
              
              <Link 
                to="/admin/users"
                className={`nav-item ${isActive('/admin/users') ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive('/admin/users') ? 'var(--primary)' : 'var(--text)',
                  background: isActive('/admin/users') ? 'var(--primary-light)' : 'transparent',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                <Users size={20} />
                <span>User Management</span>
              </Link>
              
              <Link 
                to="/admin/pending-users"
                className={`nav-item ${isActive('/admin/pending-users') ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive('/admin/pending-users') ? 'var(--primary)' : 'var(--text)',
                  background: isActive('/admin/pending-users') ? 'var(--primary-light)' : 'transparent',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                <UserCheck size={20} />
                <span>Pending Approvals</span>
              </Link>
              
              <Link 
                to="/admin/wikis"
                className={`nav-item ${isActive('/admin/wikis') ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive('/admin/wikis') ? 'var(--primary)' : 'var(--text)',
                  background: isActive('/admin/wikis') ? 'var(--primary-light)' : 'transparent',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                <BookOpen size={20} />
                <span>Wiki Management</span>
              </Link>
              
              <Link 
                to="/admin/embeddings"
                className={`nav-item ${isActive('/admin/embeddings') ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  textDecoration: 'none',
                  color: isActive('/admin/embeddings') ? 'var(--primary)' : 'var(--text)',
                  background: isActive('/admin/embeddings') ? 'var(--primary-light)' : 'transparent',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                <Database size={20} />
                <span>Embeddings</span>
              </Link>
            </nav>
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
        //   marginLeft: sidebarOpen ? `${sidebarWidth}px` : '0',
          marginLeft: sidebarOpen ? `${sidebarWidth}px` : '0',
          width: sidebarOpen ? `calc(100% - ${sidebarWidth}px)` : '100%',
          transition: isResizing ? 'none' : 'margin-left 0.2s ease'
        }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
