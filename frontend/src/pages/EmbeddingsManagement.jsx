import { useState, useEffect } from 'react';
import { RefreshCw, PlayCircle, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import { adminAPI } from '../services/api';

export default function EmbeddingsManagement() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [pagination, setPagination] = useState({ page: 1, per_page: 50, total: 0, pages: 0 });
  const [processing, setProcessing] = useState(null);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadPages();
  }, [statusFilter, pagination.page]);

  const loadPages = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        status: statusFilter
      };
      
      const response = await adminAPI.listPendingEmbeddings(params);
      setPages(response.data.pages);
      setPagination(response.data.pagination);
    } catch (err) {
      console.error('Failed to load pages:', err);
      setError('Failed to load pages');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateEmbedding = async (pageId) => {
    setProcessing(pageId);
    setError('');
    setSuccess('');

    try {
      await adminAPI.generatePageEmbedding(pageId);
      setSuccess(`Embedding generation queued for page ${pageId}`);
      
      // Update the page status in the list
      setPages(pages.map(p => 
        p.id === pageId ? { ...p, embeddings_status: 'pending' } : p
      ));
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to queue embedding');
    } finally {
      setProcessing(null);
    }
  };

  const handleGenerateAll = async () => {
    if (!confirm(`Generate embeddings for all ${pagination.total} pages with status "${statusFilter}"?`)) {
      return;
    }

    setBulkProcessing(true);
    setError('');
    setSuccess('');

    try {
      const response = await adminAPI.generateAllEmbeddings({ status: statusFilter });
      setSuccess(`Queued ${response.data.queued} pages for embedding generation`);
      await loadPages();
      
      setTimeout(() => setSuccess(''), 5000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to queue bulk embeddings');
    } finally {
      setBulkProcessing(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock size={16} className="text-warning" />;
      case 'processing':
        return <RefreshCw size={16} className="text-info" style={{ animation: 'spin 1s linear infinite' }} />;
      case 'failed':
        return <AlertCircle size={16} className="text-error" />;
      case 'completed':
        return <CheckCircle size={16} className="text-success" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { bg: 'var(--warning-light)', color: 'var(--warning)' },
      processing: { bg: 'var(--info-light)', color: 'var(--info)' },
      failed: { bg: 'var(--error-light)', color: 'var(--error)' },
      completed: { bg: 'var(--success-light)', color: 'var(--success)' }
    };

    const style = styles[status] || styles.pending;

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        padding: '0.25rem 0.5rem',
        background: style.bg,
        color: style.color,
        borderRadius: '0.25rem',
        fontSize: '0.875rem',
        fontWeight: 500
      }}>
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div style={{ padding: '2rem', maxWidth: 1400, margin: '0 auto' }}>
      <div className="mb-4">
        <h2 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Embeddings Management
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Manage and generate page embeddings for semantic search
        </p>
      </div>

      {/* Controls */}
      <div style={{ 
        background: 'var(--surface)', 
        border: '1px solid var(--border)', 
        borderRadius: '0.5rem',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div className="flex justify-between items-center gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <label style={{ fontWeight: 500 }}>Status Filter:</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPagination(prev => ({ ...prev, page: 1 }));
              }}
              style={{
                padding: '0.5rem 1rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                background: 'var(--bg)',
                color: 'var(--text)'
              }}
            >
              <option value="all">All Incomplete</option>
              <option value="pending">Pending Only</option>
              <option value="failed">Failed Only</option>
              <option value="processing">Processing Only</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              className="btn btn-secondary"
              onClick={loadPages}
              disabled={loading}
            >
              <RefreshCw size={18} />
              Refresh
            </button>
            <button
              className="btn btn-primary"
              onClick={handleGenerateAll}
              disabled={bulkProcessing || pages.length === 0}
            >
              <Zap size={18} />
              {bulkProcessing ? 'Processing...' : `Generate All (${pagination.total})`}
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div style={{
          padding: '1rem',
          marginBottom: '1rem',
          background: 'var(--error-light)',
          border: '1px solid var(--error)',
          borderRadius: '0.375rem',
          color: 'var(--error)'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '1rem',
          marginBottom: '1rem',
          background: 'var(--success-light)',
          border: '1px solid var(--success)',
          borderRadius: '0.375rem',
          color: 'var(--success)'
        }}>
          {success}
        </div>
      )}

      {/* Pages Table */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
        </div>
      ) : pages.length === 0 ? (
        <div className="empty-state">
          <CheckCircle size={48} className="empty-state-icon" style={{ margin: '0 auto', color: 'var(--success)' }} />
          <h3 className="font-semibold mb-2">All pages have embeddings!</h3>
          <p className="text-secondary">No pages found with the selected status filter</p>
        </div>
      ) : (
        <>
          <div style={{ 
            background: 'var(--surface)', 
            border: '1px solid var(--border)', 
            borderRadius: '0.5rem',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Page</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Wiki</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Created</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Updated</th>
                  <th style={{ padding: '1rem', textAlign: 'center', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pages.map((page) => (
                  <tr key={page.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '1rem' }}>
                      <div>
                        <div style={{ fontWeight: 500 }}>{page.title}</div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                          ID: {page.id}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {page.wiki_name || 'Unknown'}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {getStatusBadge(page.embeddings_status)}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {formatDate(page.created_at)}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {formatDate(page.updated_at)}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleGenerateEmbedding(page.id)}
                        disabled={processing === page.id}
                        style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                      >
                        {processing === page.id ? (
                          <>
                            <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} />
                            Processing...
                          </>
                        ) : (
                          <>
                            <PlayCircle size={14} />
                            Generate
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex justify-between items-center mt-4">
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                Page {pagination.page} of {pagination.pages} ({pagination.total} total pages)
              </div>
              <div className="flex gap-2">
                <button
                  className="btn btn-secondary"
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1}
                >
                  Previous
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page === pagination.pages}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
