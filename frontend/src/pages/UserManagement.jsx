import { useState, useEffect } from 'react';
import { Search as SearchIcon, Edit, Trash2, Shield, ShieldOff, CheckCircle, XCircle, MoreVertical } from 'lucide-react';
import { adminAPI } from '../services/api';
import Modal from '../components/Modal';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [pagination, setPagination] = useState({ page: 1, per_page: 50, total: 0, pages: 0 });
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(null);

  useEffect(() => {
    loadUsers();
  }, [searchTerm, pagination.page]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
      };
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      
      const response = await adminAPI.listUsers(params);
      setUsers(response.data.users);
      setPagination(response.data.pagination);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditForm({
      display_name: user.display_name || '',
      email: user.email || '',
      is_active: user.is_active,
      is_admin: user.is_admin
    });
    setShowEditModal(true);
    setDropdownOpen(null);
  };

  const handleSaveUser = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      await adminAPI.updateUser(selectedUser.id, editForm);
      await loadUsers();
      setShowEditModal(false);
      setSelectedUser(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivateUser = async (user) => {
    if (!confirm(`Are you sure you want to deactivate ${user.username}?`)) {
      return;
    }

    try {
      await adminAPI.deleteUser(user.id);
      await loadUsers();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to deactivate user');
    }
    setDropdownOpen(null);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div style={{ padding: '2rem', maxWidth: 1400, margin: '0 auto' }}>
      <div className="mb-4">
        <h2 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          User Management
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Manage user accounts and permissions
        </p>
      </div>

      {/* Search */}
      <div style={{ marginBottom: '2rem', maxWidth: 500 }}>
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
            placeholder="Search users by name, email, or username..."
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

      {/* User Table */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner" />
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <p>No users found</p>
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
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>User</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Email</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Role</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Stats</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Joined</th>
                  <th style={{ padding: '1rem', textAlign: 'center', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '1rem' }}>
                      <div>
                        <div style={{ fontWeight: 500 }}>{user.display_name || user.username}</div>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                          @{user.username}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>
                      {user.email}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {user.is_active ? (
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
                          <CheckCircle size={14} />
                          Active
                        </span>
                      ) : (
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          gap: '0.25rem',
                          padding: '0.25rem 0.5rem',
                          background: 'var(--error-light)',
                          color: 'var(--error)',
                          borderRadius: '0.25rem',
                          fontSize: '0.875rem'
                        }}>
                          <XCircle size={14} />
                          Inactive
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {user.is_admin ? (
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          gap: '0.25rem',
                          padding: '0.25rem 0.5rem',
                          background: 'var(--primary-light)',
                          color: 'var(--primary)',
                          borderRadius: '0.25rem',
                          fontSize: '0.875rem',
                          fontWeight: 500
                        }}>
                          <Shield size={14} />
                          Admin
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                          User
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {user.stats.owned_wikis} wikis · {user.stats.pages_created} pages
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                      {formatDate(user.created_at)}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <div style={{ position: 'relative', display: 'inline-block' }}>
                        <button
                          className="btn btn-ghost btn-icon"
                          onClick={() => setDropdownOpen(dropdownOpen === user.id ? null : user.id)}
                        >
                          <MoreVertical size={18} />
                        </button>
                        
                        {dropdownOpen === user.id && (
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
                              minWidth: '160px',
                              zIndex: 20
                            }}>
                              <button
                                className="dropdown-item"
                                onClick={() => handleEditUser(user)}
                              >
                                <Edit size={16} />
                                Edit User
                              </button>
                              <button
                                className="dropdown-item"
                                onClick={() => handleDeactivateUser(user)}
                                style={{ color: 'var(--error)' }}
                              >
                                <Trash2 size={16} />
                                Deactivate
                              </button>
                            </div>
                          </>
                        )}
                      </div>
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
                Page {pagination.page} of {pagination.pages} ({pagination.total} total users)
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

      {/* Edit User Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedUser(null);
          setError('');
        }}
        title={`Edit User: ${selectedUser?.username}`}
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowEditModal(false);
                setSelectedUser(null);
                setError('');
              }}
              disabled={saving}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleSaveUser}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
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

        <form onSubmit={handleSaveUser}>
          <div className="form-group">
            <label className="form-label">Display Name</label>
            <input
              type="text"
              className="form-input"
              value={editForm.display_name || ''}
              onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              value={editForm.email || ''}
              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={editForm.is_active || false}
                onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
              />
              <span>Account is active</span>
            </label>
          </div>

          <div className="form-group">
            <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={editForm.is_admin || false}
                onChange={(e) => setEditForm({ ...editForm, is_admin: e.target.checked })}
              />
              <span>Administrator privileges</span>
            </label>
          </div>
        </form>
      </Modal>
    </div>
  );
}
