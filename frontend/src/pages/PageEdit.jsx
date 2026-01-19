import { useState, useEffect, useRef } from 'react';
import { useParams, useOutletContext, useNavigate, Link } from 'react-router-dom';
import { Save, X, ChevronRight, Upload, Paperclip, Trash2, Search } from 'lucide-react';
import { pagesAPI, attachmentsAPI } from '../services/api';
import MarkdownEditor from '../components/MarkdownEditor';
import TagManager from '../components/TagManager';

export default function PageEdit() {
  const { wikiId, pageId } = useParams();
  const { wiki, pages, refreshPages } = useOutletContext();
  const navigate = useNavigate();

  const [page, setPage] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [summary, setSummary] = useState('');
  const [parentId, setParentId] = useState(null);
  const [changeSummary, setChangeSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [showAttachments, setShowAttachments] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fileInputRef = useRef(null);
  const editorRef = useRef(null);

  useEffect(() => {
    loadPage();
  }, [pageId]);

  const loadPage = async () => {
    setLoading(true);
    try {
      const response = await pagesAPI.get(wikiId, pageId);
      const pageData = response.data.page;
      setPage(pageData);
      setTitle(pageData.title);
      setContent(pageData.content || '');
      setSummary(pageData.summary || '');
      setParentId(pageData.parent_id);

      // Load all wiki attachments instead of just page attachments
      const attachRes = await attachmentsAPI.listAll(wikiId);
      setAttachments(attachRes.data.attachments);
    } catch (err) {
      console.error('Failed to load page:', err);
      navigate(`/wiki/${wikiId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await pagesAPI.update(wikiId, pageId, {
        title,
        content,
        summary,
        parent_id: parentId,
        change_summary: changeSummary || 'Content updated'
      });
      
      await refreshPages();
      navigate(`/wiki/${wikiId}/page/${pageId}`);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to save page');
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const response = await attachmentsAPI.upload(wikiId, pageId, file);
      setAttachments([...attachments, response.data.attachment]);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to upload file');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm('Delete this attachment?')) return;

    try {
      await attachmentsAPI.delete(attachmentId);
      setAttachments(attachments.filter(a => a.id !== attachmentId));
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete attachment');
    }
  };

  const flattenPages = (pageList, level = 0, excludeId = null) => {
    let result = [];
    for (const p of pageList) {
      if (p.id === excludeId) continue;
      result.push({ ...p, level });
      if (p.children) {
        result = result.concat(flattenPages(p.children, level + 1, excludeId));
      }
    }
    return result;
  };
  
  const flatPages = flattenPages(pages, 0, parseInt(pageId));

  // Separate attachments by page
  const currentPageAttachments = attachments.filter(att => att.page?.id === parseInt(pageId));
  const otherPageAttachments = attachments.filter(att => att.page?.id !== parseInt(pageId));

  // Filter attachments based on search query
  const filterAttachment = (att) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      att.filename.toLowerCase().includes(query) ||
      att.file_type.toLowerCase().includes(query) ||
      att.page?.title.toLowerCase().includes(query)
    );
  };

  const filteredCurrentPage = currentPageAttachments.filter(filterAttachment);
  const filteredOtherPages = otherPageAttachments.filter(filterAttachment);
  const currentPageAttachmentCount = currentPageAttachments.length;

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{ 
        padding: '0.75rem 1.5rem', 
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem'
      }}>
        <div className="flex items-center gap-4 flex-1">
          <button 
            className="btn btn-ghost"
            onClick={() => navigate(`/wiki/${wikiId}/page/${pageId}`)}
          >
            <X size={18} />
            Cancel
          </button>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, maxWidth: 600 }}>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Page title"
              className="form-input"
              style={{ fontSize: '1.25rem', fontWeight: 600 }}
            />
            {page && (
              <TagManager
                wikiId={wikiId}
                pageId={pageId}
                initialTags={page.tags || []}
              />
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn btn-secondary"
            onClick={() => setShowAttachments(true)}
          >
            <Paperclip size={16} />
            Attachments ({currentPageAttachmentCount}/{attachments.length})
          </button>
          
          <button 
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving || !title.trim()}
          >
            <Save size={16} />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </header>

      {/* Editor */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <MarkdownEditor
          ref={editorRef}
          wikiId={parseInt(wikiId)}
          pageId={parseInt(pageId)}
          initialValue={content}
          onChange={setContent}
          height="100%"
          placeholder="Start writing your page content..."
        />
      </div>

      {/* Footer with metadata */}
      <footer style={{ 
        padding: '0.75rem 1.5rem', 
        borderTop: '1px solid var(--border)',
        background: 'var(--surface)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <div className="form-group" style={{ marginBottom: 0, flex: 1, maxWidth: 300 }}>
          <label className="text-xs text-secondary mb-1" style={{ display: 'block' }}>
            Parent Page
          </label>
          <select
            className="form-input"
            value={parentId || ''}
            onChange={(e) => setParentId(e.target.value ? parseInt(e.target.value) : null)}
            style={{ fontSize: '0.875rem' }}
          >
            <option value="">None (top level)</option>
            {flatPages.map(p => (
              <option key={p.id} value={p.id}>
                {'  '.repeat(p.level)}{p.title}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group" style={{ marginBottom: 0, flex: 1, maxWidth: 300 }}>
          <label className="text-xs text-secondary mb-1" style={{ display: 'block' }}>
            Summary (for search)
          </label>
          <input
            type="text"
            className="form-input"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Brief description"
            style={{ fontSize: '0.875rem' }}
          />
        </div>

        <div className="form-group" style={{ marginBottom: 0, flex: 1, maxWidth: 300 }}>
          <label className="text-xs text-secondary mb-1" style={{ display: 'block' }}>
            Change Summary
          </label>
          <input
            type="text"
            className="form-input"
            value={changeSummary}
            onChange={(e) => setChangeSummary(e.target.value)}
            placeholder="What did you change?"
            style={{ fontSize: '0.875rem' }}
          />
        </div>
      </footer>

      {/* Attachments Modal */}
      {showAttachments && (
        <div className="modal-overlay" onClick={() => setShowAttachments(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 800, maxHeight: '90vh' }}>
            <div className="modal-header">
              <h3 className="modal-title">Wiki Attachments</h3>
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => setShowAttachments(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body" style={{ maxHeight: 'calc(90vh - 120px)', overflow: 'auto' }}>
              <div className="mb-4" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                />
                <button
                  className="btn btn-secondary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Upload size={16} />
                  {uploading ? 'Uploading...' : 'Upload to this page'}
                </button>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search attachments..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ paddingLeft: '2.5rem' }}
                  />
                </div>
              </div>
              <p className="text-xs text-secondary mb-4">
                {filteredCurrentPage.length + filteredOtherPages.length} of {attachments.length} attachments
                {searchQuery && ' matching your search'}. Tip: You can also paste images directly into the editor (Ctrl+V)
              </p>

              {/* Current Page Attachments */}
              {filteredCurrentPage.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text)' }}>
                    This Page ({filteredCurrentPage.length})
                  </h4>
                  <div style={{ display: 'grid', gap: '1rem' }}>
                    {filteredCurrentPage.map(att => (
                      <div key={att.id} style={{
                        border: '1px solid var(--border)',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        display: 'flex',
                        gap: '1rem',
                        backgroundColor: 'var(--surface-hover)'
                      }}>
                        {/* Image Preview */}
                        {att.file_type === 'image' && (
                          <div style={{
                            width: '120px',
                            height: '120px',
                            flexShrink: 0,
                            borderRadius: '0.25rem',
                            overflow: 'hidden',
                            backgroundColor: 'var(--surface)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}>
                            <img
                              src={attachmentsAPI.getViewUrl(att.id)}
                              alt={att.filename}
                              style={{
                                maxWidth: '100%',
                                maxHeight: '100%',
                                objectFit: 'contain'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.parentElement.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.875rem;">Preview unavailable</div>';
                              }}
                            />
                          </div>
                        )}

                        {/* Attachment Info */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem', wordBreak: 'break-word' }}>
                            {att.filename}
                          </div>
                          <div className="text-xs text-secondary" style={{ marginBottom: '0.5rem' }}>
                            {Math.round(att.file_size / 1024)}KB • {att.file_type}
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <button
                              className="btn btn-sm btn-secondary"
                              onClick={() => {
                                const url = att.file_type === 'image'
                                  ? `/api/attachments/${att.id}/view`
                                  : `/api/attachments/${att.id}/download`;
                                const markdown = att.file_type === 'image'
                                  ? `![${att.filename}](${url})`
                                  : `[${att.filename}](${url})`;
                                if (editorRef.current?.insertText) {
                                  editorRef.current.insertText('\n' + markdown + '\n');
                                }
                                setShowAttachments(false);
                              }}
                            >
                              Insert
                            </button>
                            <a
                              href={attachmentsAPI.getDownloadUrl(att.id)}
                              className="btn btn-sm btn-secondary"
                              download
                            >
                              Download
                            </a>
                            <button
                              className="btn btn-sm btn-ghost"
                              onClick={() => handleDeleteAttachment(att.id)}
                              title="Delete attachment"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Other Pages Attachments */}
              {filteredOtherPages.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text)' }}>
                    Other Pages ({filteredOtherPages.length})
                  </h4>
                  <div style={{ display: 'grid', gap: '1rem' }}>
                    {filteredOtherPages.map(att => (
                      <div key={att.id} style={{
                        border: '1px solid var(--border)',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        display: 'flex',
                        gap: '1rem',
                        backgroundColor: 'transparent'
                      }}>
                        {/* Image Preview */}
                        {att.file_type === 'image' && (
                          <div style={{
                            width: '120px',
                            height: '120px',
                            flexShrink: 0,
                            borderRadius: '0.25rem',
                            overflow: 'hidden',
                            backgroundColor: 'var(--surface)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}>
                            <img
                              src={attachmentsAPI.getViewUrl(att.id)}
                              alt={att.filename}
                              style={{
                                maxWidth: '100%',
                                maxHeight: '100%',
                                objectFit: 'contain'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.parentElement.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.875rem;">Preview unavailable</div>';
                              }}
                            />
                          </div>
                        )}

                        {/* Attachment Info */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem', wordBreak: 'break-word' }}>
                            {att.filename}
                          </div>
                          <div className="text-xs text-secondary" style={{ marginBottom: '0.5rem' }}>
                            {Math.round(att.file_size / 1024)}KB • {att.file_type}
                            {att.page && (
                              <>
                                {' • '}
                                <span style={{ color: 'var(--text-secondary)' }}>
                                  {att.page.title}
                                </span>
                              </>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <button
                              className="btn btn-sm btn-secondary"
                              onClick={() => {
                                const url = att.file_type === 'image'
                                  ? `/api/attachments/${att.id}/view`
                                  : `/api/attachments/${att.id}/download`;
                                const markdown = att.file_type === 'image'
                                  ? `![${att.filename}](${url})`
                                  : `[${att.filename}](${url})`;
                                if (editorRef.current?.insertText) {
                                  editorRef.current.insertText('\n' + markdown + '\n');
                                }
                                setShowAttachments(false);
                              }}
                            >
                              Insert
                            </button>
                            <a
                              href={attachmentsAPI.getDownloadUrl(att.id)}
                              className="btn btn-sm btn-secondary"
                              download
                            >
                              Download
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No results */}
              {filteredCurrentPage.length === 0 && filteredOtherPages.length === 0 && (
                <p className="text-secondary text-center py-4">
                  {searchQuery ? 'No attachments match your search' : 'No attachments yet'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
