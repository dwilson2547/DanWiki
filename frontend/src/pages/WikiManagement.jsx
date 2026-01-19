import { useState, useEffect } from 'react';
import { Search as SearchIcon, Trash2, Globe, Lock, BookOpen, Users as UsersIcon, FileText, MoreVertical, UserCheck } from 'lucide-react';
import { adminAPI } from '../services/api';
import Modal from '../components/Modal';

export default function WikiManagement() {
  const [wikis, setWikis] = useState([]);
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('flat'); // flat or grouped
  const [pagination, setPagination] = useState({ page: 1, per_page: 50, total: 0, pages: 0 });
  const [selectedWiki, setSelectedWiki] = useState(null);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferUserId, setTransferUserId] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(null);

  useEffect(() => {
    loadWikis();
  }, [searchTerm, viewMode, pagination.page]);

  const loadWikis = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        group_by: viewMode === 'grouped' ? 'owner' : 'none'
      };
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      
      const response = await adminAPI.listWikis(params);
      
      if (viewMode === 'grouped') {
        setOwners(response.data.owners || []);
        setPagination(prev => ({ ...prev, total: response.data.total_wikis || 0 }));
      } else {
        setWikis(response.data.wikis || []);
        setPagination(response.data.pagination);
      }
    } catch (err) {
      console.error('Failed to load wikis:', err);
      setError('Failed to load wikis');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWiki = async (wiki) => {
    if (!confirm(`Are you sure you want to delete "${wiki.name}"? This will delete ALL pages and cannot be undone.`)) {
      return;
    }

    try {
      await adminAPI.deleteWiki(wiki.id);
      setSuccess(`Wiki "${wiki.name}" deleted successfully`);
      await loadWikis();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete wiki');
    }
    setDropdownOpen(null);
  };

  const handleTransferWiki = (wiki) => {
    setSelectedWiki(wiki);
    setTransferUserId('');
    setShowTransferModal(true);
    setDropdownOpen(null);
  };

  const handleTransferSubmit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setError('');

    try {
      await adminAPI.transferWikiOwnership(selectedWiki.id, { owner_id: parseInt(transferUserId) });
      setSuccess(`Wiki "${selectedWiki.name}" transferred successfully`);
      await loadWikis();
      setShowTransferModal(false);
      setSelectedWiki(null);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to transfer wiki');
    } finally {
      setProcessing(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const WikiRow = ({ wiki, owner }) => (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      <td style={{ padding: '1rem' }}>
        <div>
          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>{wiki.name}</div>
          {wiki.description && (
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {wiki.description}
            </div>
          )}
        </div>
      </td>
      <td style={{ padding: '1rem' }}>
        <div>
          <div style={{ fontWeight: 500 }}>{owner?.display_name || owner?.username}</div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            @{owner?.username}
          </div>
        </div>
      </td>
      <td style={{ padding: '1rem' }}>
        {wiki.is_public ? (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.25rem 0.5rem',
            background: 'var(--success-light)',
            color: 'var(--success)',
            borderRadius: '0.25rem',
            fontSize: '0.875rem'
          }}>
            <Globe size={14} />
            Public
          </span>
        ) : (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.25rem 0.5rem',
            background: 'var(--bg)',
            color: 'var(--text-secondary)',
            borderRadius: '0.25rem',
            fontSize: '0.875rem'
          }}>
            <Lock size={14} />
            Private
          </span>
        )}
      </td>
      <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        {wiki.stats?.pages || wiki.page_count || 0} pages · {wiki.stats?.members || wiki.member_count || 0} members
      </td>
      <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        {formatDate(wiki.created_at)}
      </td>
      <td style={{ padding: '1rem', textAlign: 'center' }}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <button
            className="btn btn-ghost btn-icon"
            onClick={() => setDropdownOpen(dropdownOpen === wiki.id ? null : wiki.id)}
          >
            <MoreVertical size={18} />
          </button>
          
          {dropdownOpen === wiki.id && (
            <>
              <div 
                style={{ 
                  position: 'fixed', 
                  inset: 0, 
                  zIndex: 10 
                }}
                onClick={() => setDropdownOpen(null)}
              />
              <div className="dropdown-menu" style={{
                position: 'absolute',
                right: 0,
                top: '100%',
                marginTop: '0.25rem',
                minWidth: '180px',
                zIndex: 20
              }}>
                <a
                  href={`/wiki/${wiki.id}`}
                  className="dropdown-item"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <BookOpen size={16} />
                  Open Wiki
                </a>
                <button
                  className="dropdown-item"
                  onClick={() => handleTransferWiki(wiki)}
                >
                  <UserCheck size={16} />
                  Transfer Owner
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => handleDeleteWiki(wiki)}
                  style={{ color: 'var(--error)' }}
                >
                  <Trash2 size={16} />
                  Delete Wiki
                </button>
              </div>
            </>
          )}
        </div>
      </td>
    </tr>
  );

  return (
    <div style={{ padding: '2rem', maxWidth: 1600, margin: '0 auto' }}>
      <div className="mb-4">
        <h2 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Wiki Management
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Manage all wikis across the platform
        </p>
      </div>

      {/* Controls */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        marginBottom: '2rem',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ flex: '1', minWidth: '300px', maxWidth: '500px' }}>
          <div style={{ position: 'relative' }}>
            <SearchIcon 
              size={20} 
              style={{ 
                position: 'absolute', 
                left: '0.75rem', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: 'var(--text-secondary)' 
              }} 
            />
            <input
              type="text"
              placeholder="Search wikis by name, description, or owner..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPagination(prev => ({ ...prev, page: 1 }));
              }}
              style={{
                width: '100%',
                padding: '0.75rem 1rem 0.75rem 2.75rem',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                background: 'var(--surface)',
                color: 'var(--text)'
              }}
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button
            className={`btn ${viewMode === 'flat' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setViewMode('flat');
              setPagination(prev => ({ ...prev, page: 1 }));
            }}
          >
            Flat View
          </button>
          <button
            className={`btn ${viewMode === 'grouped' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setViewMode('grouped');
              setPagination(prev => ({ ...prev, page: 1 }));
            }}
          >
            Group by Owner
          </button>
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

      {/* Wikis Display */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
        </div>
      ) : viewMode === 'grouped' ? (
        // Grouped by owner view
        owners.length === 0 ? (
          <div className="empty-state">
            <p>No wikis found</p>
          </div>
        ) : (
          owners.map((ownerData) => (
            <div key={ownerData.owner.id} style={{ marginBottom: '2rem' }}>
              <div style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                overflow: 'hidden'
              }}>
                <div style={{
                  background: 'var(--bg)',
                  padding: '1rem 1.5rem',
                  borderBottom: '1px solid var(--border)'
                }}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '1.125rem' }}>
                        {ownerData.owner.display_name}
                      </div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        @{ownerData.owner.username} · {ownerData.wikis.length} {ownerData.wikis.length === 1 ? 'wiki' : 'wikis'}
                      </div>
                    </div>
                  </div>
                </div>

                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Wiki</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Visibility</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Stats</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Created</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'center', fontWeight: 600, fontSize: '0.875rem' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ownerData.wikis.map((wiki) => (
                      <WikiRow key={wiki.id} wiki={wiki} owner={ownerData.owner} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))
        )
      ) : (
        // Flat view
        <>
          {wikis.length === 0 ? (
            <div className="empty-state">
              <p>No wikis found</p>
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
                      <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Wiki</th>
                      <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Owner</th>
                      <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Visibility</th>
                      <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Stats</th>
                      <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Created</th>
                      <th style={{ padding: '1rem', textAlign: 'center', fontWeight: 600 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wikis.map((wiki) => (
                      <WikiRow key={wiki.id} wiki={wiki} owner={wiki.owner} />
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination.pages > 1 && (
                <div className="flex justify-between items-center mt-4">
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Page {pagination.page} of {pagination.pages} ({pagination.total} total wikis)
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
        </>
      )}

      {/* Transfer Ownership Modal */}
      <Modal
        isOpen={showTransferModal}
        onClose={() => {
          setShowTransferModal(false);
          setSelectedWiki(null);
          setError('');
        }}
        title={`Transfer Wiki: ${selectedWiki?.name}`}
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowTransferModal(false);
                setSelectedWiki(null);
                setError('');
              }}
              disabled={processing}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleTransferSubmit}
              disabled={processing || !transferUserId}
            >
              {processing ? 'Transferring...' : 'Transfer Ownership'}
            </button>
          </>
        }
      >
        {error && (
          <div style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            background: 'var(--error-light)',
            border: '1px solid var(--error)',
            borderRadius: '0.375rem',
            color: 'var(--error)',
            fontSize: '0.875rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleTransferSubmit}>
          <div className="form-group">
            <label className="form-label">New Owner User ID</label>
            <input
              type="number"
              className="form-input"
              value={transferUserId}
              onChange={(e) => setTransferUserId(e.target.value)}
              placeholder="Enter user ID"
              required
            />
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Enter the ID of the user who should become the new owner of this wiki.
            </p>
          </div>
        </form>
      </Modal>
    </div>
  );
}
