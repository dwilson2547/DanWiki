import { useState, useEffect, useRef } from 'react';
import { useParams, useOutletContext, Link, useNavigate } from 'react-router-dom';
import { 
  Edit, Trash2, Clock, User, ChevronRight, 
  Paperclip, History, MoreVertical, FileText 
} from 'lucide-react';
import { pagesAPI, attachmentsAPI } from '../services/api';
import { Viewer } from '@toast-ui/react-editor';
import '@toast-ui/editor/dist/toastui-editor-viewer.css';
import '@toast-ui/editor/dist/theme/toastui-editor-dark.css';
import { useTheme } from '../context/ThemeContext';
import codeSyntaxHighlight from '@toast-ui/editor-plugin-code-syntax-highlight';
import '@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css';
import Prism from 'prismjs';
import '../styles/prism-theme.css';
import TagManager from '../components/TagManager';

// Import base dependencies first
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-markup-templating';

// Import commonly used languages for syntax highlighting
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-tsx';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-scss';
import 'prismjs/components/prism-docker';
import 'prismjs/components/prism-git';

export default function PageView() {
  const { wikiId, pageId } = useParams();
  const { wiki, refreshPages } = useOutletContext();
  const { theme } = useTheme();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [attachments, setAttachments] = useState([]);
  const [showAttachments, setShowAttachments] = useState(false);
  const [showRevisions, setShowRevisions] = useState(false);
  const [revisions, setRevisions] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const viewerRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadPage();
  }, [pageId]);

  // Add IDs to headings and handle anchor link clicks
  useEffect(() => {
    if (!page?.content) return;

    // Generate slug from text (similar to markdown processors)
    const generateSlug = (text) => {
      return text
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '') // Remove special chars except spaces and hyphens
        .replace(/[\s_]+/g, '-')  // Replace spaces and underscores with hyphens
        .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
    };

    // Add auth token to attachment image URLs
    const addTokenToAttachmentImages = () => {
      const contentDiv = viewerRef.current?.querySelector('.toastui-editor-contents') || 
                        document.querySelector('.toastui-editor-contents');
      
      if (contentDiv) {
        const token = localStorage.getItem('access_token');
        if (token) {
          // Find all images with attachment URLs
          const images = contentDiv.querySelectorAll('img[src*="/api/attachments/"]');
          images.forEach(img => {
            const src = img.getAttribute('src');
            // Only add token if not already present
            if (src && !src.includes('token=')) {
              const separator = src.includes('?') ? '&' : '?';
              img.setAttribute('src', `${src}${separator}token=${encodeURIComponent(token)}`);
            }
          });
        }
      }
    };

    const handleAnchorClick = (e) => {
      // Check if clicked element is an anchor link
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;

      const hash = link.getAttribute('href');
      if (!hash || !hash.startsWith('#')) return;

      e.preventDefault();
      e.stopPropagation();

      const targetId = hash.slice(1);
      const targetElement = document.getElementById(targetId);
      
      if (targetElement) {
        // Get header height to offset the scroll
        const header = document.querySelector('.wiki-header') || document.querySelector('header');
        const headerHeight = header ? header.offsetHeight : 80; // Default to 80px if header not found
        const offset = headerHeight + 20; // Add extra 20px padding
        
        const elementPosition = targetElement.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
        
        window.history.replaceState(null, '', hash);
      }
    };

    const processHeadings = () => {
      const contentDiv = viewerRef.current?.querySelector('.toastui-editor-contents') || 
                        document.querySelector('.toastui-editor-contents');
      
      if (contentDiv) {
        // Add IDs to all headings
        const headings = contentDiv.querySelectorAll('h1, h2, h3, h4, h5, h6');
        headings.forEach(heading => {
          const text = heading.textContent || '';
          const id = generateSlug(text);
          if (id) {
            heading.id = id;
          }
        });

        // Add click handler for anchor links
        contentDiv.addEventListener('click', handleAnchorClick, true);
        
        // Add auth tokens to attachment images
        addTokenToAttachmentImages();
        
        // Handle URL hash on initial load
        const hash = window.location.hash;
        if (hash) {
          const targetId = hash.slice(1);
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
            setTimeout(() => {
              const header = document.querySelector('.wiki-header') || document.querySelector('header');
              const headerHeight = header ? header.offsetHeight : 80;
              const offset = headerHeight + 20;
              
              const elementPosition = targetElement.getBoundingClientRect().top;
              const offsetPosition = elementPosition + window.pageYOffset - offset;
              
              window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
              });
            }, 150);
          }
        }
        
        return true;
      }
      return false;
    };

    // Try processing immediately
    if (!processHeadings()) {
      // If not ready, try again after a short delay
      const timer = setTimeout(processHeadings, 100);
      
      return () => {
        clearTimeout(timer);
        const contentDiv = viewerRef.current?.querySelector('.toastui-editor-contents') || 
                          document.querySelector('.toastui-editor-contents');
        if (contentDiv) {
          contentDiv.removeEventListener('click', handleAnchorClick, true);
        }
      };
    }

    return () => {
      const contentDiv = viewerRef.current?.querySelector('.toastui-editor-contents') || 
                        document.querySelector('.toastui-editor-contents');
      if (contentDiv) {
        contentDiv.removeEventListener('click', handleAnchorClick, true);
      }
    };
  }, [page, theme]);

  const loadPage = async () => {
    setLoading(true);
    try {
      const response = await pagesAPI.get(wikiId, pageId, true);
      setPage(response.data.page);
      
      // Load attachments
      const attachRes = await attachmentsAPI.list(wikiId, pageId);
      setAttachments(attachRes.data.attachments);
    } catch (err) {
      console.error('Failed to load page:', err);
      if (err.response?.status === 404) {
        navigate(`/wiki/${wikiId}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadRevisions = async () => {
    try {
      const response = await pagesAPI.getRevisions(wikiId, pageId);
      setRevisions(response.data.revisions);
      setShowRevisions(true);
    } catch (err) {
      console.error('Failed to load revisions:', err);
    }
  };

  const handleDelete = async () => {
    const childCount = page.children?.length || 0;
    const message = childCount > 0
      ? `This page has ${childCount} child page(s). Delete this page and all children?`
      : 'Are you sure you want to delete this page?';
    
    if (!confirm(message)) return;

    try {
      await pagesAPI.delete(wikiId, pageId);
      await refreshPages();
      navigate(`/wiki/${wikiId}`);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete page');
    }
  };

  const handleRestoreRevision = async (revisionId) => {
    if (!confirm('Restore this revision? Current content will be saved as a new revision.')) {
      return;
    }

    try {
      await pagesAPI.restoreRevision(wikiId, pageId, revisionId);
      await loadPage();
      setShowRevisions(false);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to restore revision');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
      </div>
    );
  }

  if (!page) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <FileText size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <h3 className="font-semibold">Page not found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      {/* Breadcrumbs */}
      <nav className="breadcrumbs">
        <Link to={`/wiki/${wikiId}`}>{wiki?.name}</Link>
        {page.breadcrumbs.map((crumb, index) => (
          <span key={crumb.id} className="flex items-center gap-2">
            <ChevronRight size={14} className="breadcrumbs-separator" />
            {index === page.breadcrumbs.length - 1 ? (
              <span>{crumb.title}</span>
            ) : (
              <Link to={`/wiki/${wikiId}/page/${crumb.id}`}>{crumb.title}</Link>
            )}
          </span>
        ))}
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div className="flex justify-between items-start">
          <h1 className="page-title">{page.title}</h1>
          
          <div className="flex gap-2">
            <div className=''>
              <Link 
                to={`/wiki/${wikiId}/page/${pageId}/edit`}
                className="btn btn-primary"
              >
                <Edit size={16} />
                Edit
              </Link>
            </div>
            
            <div className="dropdown">
              <button 
                className="btn btn-secondary btn-ellipsis"
                onClick={() => setDropdownOpen(!dropdownOpen)}
              >
                <MoreVertical size={16} />
              </button>
              {dropdownOpen && (
                <div className="dropdown-menu">
                  <button 
                    className="dropdown-item flex items-center gap-2"
                    onClick={() => {
                      setDropdownOpen(false);
                      loadRevisions();
                    }}
                  >
                    <History size={14} />
                    View History
                  </button>
                  <button 
                    className="dropdown-item flex items-center gap-2"
                    onClick={() => {
                      setDropdownOpen(false);
                      setShowAttachments(true);
                    }}
                  >
                    <Paperclip size={14} />
                    Attachments ({attachments.length})
                  </button>
                  <button 
                    className="dropdown-item dropdown-item-danger flex items-center gap-2"
                    onClick={() => {
                      setDropdownOpen(false);
                      handleDelete();
                    }}
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="page-meta flex items-center gap-4 mt-2">
          <span className="flex items-center gap-1">
            <User size={14} />
            {page.last_modified_by?.display_name || page.last_modified_by?.username}
          </span>
          <span className="flex items-center gap-1">
            <Clock size={14} />
            {new Date(page.updated_at).toLocaleString()}
          </span>
          {attachments.length > 0 && (
            <button 
              className="flex items-center gap-1 text-secondary"
              onClick={() => setShowAttachments(true)}
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <Paperclip size={14} />
              {attachments.length} attachment{attachments.length !== 1 ? 's' : ''}
            </button>
          )}
        </div>

        {/* Tags Section */}
        <div className="mt-3">
          <TagManager
            wikiId={wikiId}
            pageId={pageId}
            initialTags={page.tags || []}
            onTagsChange={(updatedTags) => {
              setPage({ ...page, tags: updatedTags });
            }}
          />
        </div>
      </div>

      {/* Page Content */}
      <div className="card mt-4" ref={viewerRef}>
        <div className="card-body">
          {page.content ? (
            <Viewer 
              key={theme}
              initialValue={page.content} 
              plugins={[[codeSyntaxHighlight, { highlighter: Prism }]]}
              theme={theme}
            />
          ) : (
            <p className="text-secondary text-center py-8">
              This page is empty.{' '}
              <Link to={`/wiki/${wikiId}/page/${pageId}/edit`}>Start editing</Link>
            </p>
          )}
        </div>
      </div>

      {/* Child Pages */}
      {page.children && page.children.length > 0 && (
        <div className="card mt-4">
          <div className="card-header">
            <h3 className="font-semibold">Child Pages</h3>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <ul style={{ listStyle: 'none' }}>
              {page.children.map(child => (
                <li key={child.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <Link
                    to={`/wiki/${wikiId}/page/${child.id}`}
                    className="flex items-center gap-2 p-3"
                    style={{ color: 'var(--text)', textDecoration: 'none' }}
                  >
                    <FileText size={16} className="text-secondary" />
                    <span>{child.title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Attachments Modal */}
      {showAttachments && (
        <div className="modal-overlay" onClick={() => setShowAttachments(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h3 className="modal-title">Attachments</h3>
              <button 
                className="btn btn-ghost btn-icon"
                onClick={() => setShowAttachments(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {attachments.length === 0 ? (
                <p className="text-secondary text-center py-4">No attachments</p>
              ) : (
                <ul style={{ listStyle: 'none' }}>
                  {attachments.map(att => (
                    <li key={att.id} className="flex items-center justify-between py-2" 
                        style={{ borderBottom: '1px solid var(--border)' }}>
                      <div className="flex items-center gap-2">
                        <Paperclip size={16} className="text-secondary" />
                        <span>{att.filename}</span>
                        <span className="text-xs text-secondary">
                          ({Math.round(att.file_size / 1024)}KB)
                        </span>
                      </div>
                      <a 
                        href={attachmentsAPI.getDownloadUrl(att.id)}
                        className="btn btn-sm btn-secondary"
                        download
                      >
                        Download
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Revisions Modal */}
      {showRevisions && (
        <div className="modal-overlay" onClick={() => setShowRevisions(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
            <div className="modal-header">
              <h3 className="modal-title">Revision History</h3>
              <button 
                className="btn btn-ghost btn-icon"
                onClick={() => setShowRevisions(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {revisions.length === 0 ? (
                <p className="text-secondary text-center py-4">No revision history</p>
              ) : (
                <ul style={{ listStyle: 'none' }}>
                  {revisions.map(rev => (
                    <li key={rev.id} className="flex items-center justify-between py-3" 
                        style={{ borderBottom: '1px solid var(--border)' }}>
                      <div>
                        <div className="font-medium">Revision {rev.revision_number}</div>
                        <div className="text-sm text-secondary">
                          {rev.created_by?.display_name || rev.created_by?.username} •{' '}
                          {new Date(rev.created_at).toLocaleString()}
                        </div>
                        {rev.change_summary && (
                          <div className="text-sm text-secondary mt-1">
                            {rev.change_summary}
                          </div>
                        )}
                      </div>
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleRestoreRevision(rev.id)}
                      >
                        Restore
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
