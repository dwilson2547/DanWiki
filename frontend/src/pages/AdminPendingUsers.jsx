import { useState, useEffect } from 'react';
import { UserCheck, UserX, Mail, Calendar, Loader } from 'lucide-react';
import { adminAPI } from '../services/api';

export default function AdminPendingUsers() {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingUserId, setProcessingUserId] = useState(null);

  useEffect(() => {
    loadPendingUsers();
  }, []);

  const loadPendingUsers = async () => {
    try {
      setError('');
      const response = await adminAPI.listPendingUsers();
      setPendingUsers(response.data.users);
    } catch (err) {
      setError('Failed to load pending users');
      console.error('Failed to load pending users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId, username) => {
    if (!confirm(`Approve user "${username}"?`)) return;

    setProcessingUserId(userId);
    try {
      await adminAPI.approveUser(userId);
      setPendingUsers(prev => prev.filter(u => u.id !== userId));
      // Show success message or toast
    } catch (err) {
      setError(`Failed to approve user: ${err.response?.data?.error || err.message}`);
    } finally {
      setProcessingUserId(null);
    }
  };

  const handleReject = async (userId, username) => {
    if (!confirm(`Reject and delete user "${username}"? This action cannot be undone.`)) return;

    setProcessingUserId(userId);
    try {
      await adminAPI.rejectUser(userId);
      setPendingUsers(prev => prev.filter(u => u.id !== userId));
      // Show success message or toast
    } catch (err) {
      setError(`Failed to reject user: ${err.response?.data?.error || err.message}`);
    } finally {
      setProcessingUserId(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="loading-container" style={{ minHeight: '400px' }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
      <div className="mb-6">
        <h2 style={{ fontSize: '1.875rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Pending User Approvals
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Review and approve or reject new user registrations
        </p>
      </div>

      {error && (
        <div className="alert alert-error mb-4">
          {error}
        </div>
      )}

      {pendingUsers.length === 0 ? (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '0.5rem',
          padding: '3rem',
          textAlign: 'center'
        }}>
          <UserCheck size={48} style={{ color: 'var(--text-secondary)', margin: '0 auto 1rem' }} />
          <p style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            No pending approvals
          </p>
          <p style={{ color: 'var(--text-secondary)' }}>
            All user registrations have been processed
          </p>
        </div>
      ) : (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '0.5rem',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: 'var(--background)', borderBottom: '1px solid var(--border)' }}>
              <tr>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>User</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Email</th>
                <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600 }}>Registered</th>
                <th style={{ padding: '1rem', textAlign: 'right', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pendingUsers.map((user) => (
                <tr key={user.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: 600 }}>{user.username}</div>
                    {user.display_name && user.display_name !== user.username && (
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        {user.display_name}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div className="flex items-center gap-2">
                      <Mail size={16} style={{ color: 'var(--text-secondary)' }} />
                      <span style={{ fontSize: '0.875rem' }}>{user.email}</span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <div className="flex items-center gap-2">
                      <Calendar size={16} style={{ color: 'var(--text-secondary)' }} />
                      <span style={{ fontSize: '0.875rem' }}>
                        {formatDate(user.created_at)}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleApprove(user.id, user.username)}
                        disabled={processingUserId === user.id}
                        className="btn btn-sm"
                        style={{
                          background: 'var(--success)',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                        title="Approve user"
                      >
                        {processingUserId === user.id ? (
                          <Loader size={16} className="spinner" />
                        ) : (
                          <UserCheck size={16} />
                        )}
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(user.id, user.username)}
                        disabled={processingUserId === user.id}
                        className="btn btn-sm"
                        style={{
                          background: 'var(--danger)',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                        title="Reject and delete user"
                      >
                        {processingUserId === user.id ? (
                          <Loader size={16} className="spinner" />
                        ) : (
                          <UserX size={16} />
                        )}
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pendingUsers.length > 0 && (
        <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {pendingUsers.length} user{pendingUsers.length !== 1 ? 's' : ''} pending approval
        </div>
      )}
    </div>
  );
}
