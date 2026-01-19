import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  User, Upload, Trash2, Settings as SettingsIcon, 
  Book, Home, Users, Lock, Globe, ArrowLeft, AlertTriangle,
  Sun, Moon
} from 'lucide-react';
import { authAPI, wikisAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import Modal from '../components/Modal';
import UserMenu from '../components/UserMenu';

export default function UserSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [wikis, setWikis] = useState([]);
  const [profile, setProfile] = useState({
    display_name: '',
    email: '',
    avatar_url: ''
  });
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false);
  const [showDeleteWithWikisModal, setShowDeleteWithWikisModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { user, logout, refreshUser } = useAuth();
  const { theme, setLightTheme, setDarkTheme } = useTheme();
  const navigate = useNavigate();

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    setLoading(true);
    try {
      const [userRes, wikisRes] = await Promise.all([
        authAPI.getMe(),
        wikisAPI.list()
      ]);
      
      const userData = userRes.data.user;
      setProfile({
        display_name: userData.display_name || '',
        email: userData.email || '',
        avatar_url: userData.avatar_url || ''
      });
      
      // Filter to only owned wikis
      const ownedWikis = wikisRes.data.wikis.filter(w => w.owner && w.owner.id === user.id);
      setWikis(ownedWikis);
    } catch (err) {
      console.error('Failed to load user data:', err);
      setError('Failed to load user data');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await authAPI.updateMe({
        display_name: profile.display_name,
        avatar_url: profile.avatar_url
      });
      setSuccess('Profile updated successfully');
      await refreshUser();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image size must be less than 5MB');
      return;
    }

    setUploadingAvatar(true);
    setError('');

    try {
      // Create a data URL for the image
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64String = reader.result;
        setProfile({ ...profile, avatar_url: base64String });
        
        // Auto-save avatar
        try {
          await authAPI.updateMe({ avatar_url: base64String });
          setSuccess('Avatar updated successfully');
          await refreshUser();
          setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
          setError('Failed to save avatar');
        }
      };
      reader.readAsDataURL(file);
    } catch (err) {
      setError('Failed to upload avatar');
    } finally {
      setUploadingAvatar(false);
    }
  };

  const handleRemoveAvatar = async () => {
    try {
      await authAPI.updateMe({ avatar_url: '' });
      setProfile({ ...profile, avatar_url: '' });
      setSuccess('Avatar removed successfully');
      await refreshUser();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to remove avatar');
    }
  };

  const handleDeleteWiki = async (wikiId) => {
    if (!confirm('Are you sure you want to delete this wiki? All pages will be deleted.')) {
      return;
    }

    try {
      await wikisAPI.delete(wikiId);
      setWikis(wikis.filter(w => w.id !== wikiId));
      setSuccess('Wiki deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete wiki');
    }
  };

  const handleDeleteAccount = async (deleteWikis = false) => {
    if (deleteConfirmation !== 'DELETE') {
      setError('Please type DELETE to confirm');
      return;
    }

    try {
      // Call delete account endpoint
      await authAPI.deleteAccount({ delete_wikis: deleteWikis });
      logout();
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete account');
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
        <header style={{ 
          borderBottom: '1px solid var(--border)',
          background: 'var(--card)',
          padding: '1rem 0'
        }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2rem' }}>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <SettingsIcon size={28} style={{ color: 'var(--primary)' }} />
                <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                  User Settings
                </h1>
              </div>
              <UserMenu />
            </div>
          </div>
        </header>
        <div className="loading-container" style={{ padding: '4rem 0' }}>
          <div className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{ 
        borderBottom: '1px solid var(--border)',
        background: 'var(--card)',
        padding: '1rem 0'
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 2rem' }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <SettingsIcon size={28} style={{ color: 'var(--primary)' }} />
              <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                User Settings
              </h1>
            </div>
            <div className="flex gap-2 items-center">
              <Link to="/dashboard" className="btn btn-ghost">
                <ArrowLeft size={18} />
                Back to Dashboard
              </Link>
              <UserMenu />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: 1000, margin: '0 auto', padding: '2rem' }}>
        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
            {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success" style={{ marginBottom: '1.5rem', background: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' }}>
            {success}
          </div>
        )}

        {/* Profile Section */}
        <section className="card" style={{ marginBottom: '2rem' }}>
          <div className="card-body">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
              Profile Settings
            </h2>

            <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
              {/* Avatar */}
              <div style={{ flex: '0 0 auto' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    overflow: 'hidden',
                    border: '3px solid var(--border)',
                    marginBottom: '1rem'
                  }}>
                    {profile.avatar_url ? (
                      <img
                        src={profile.avatar_url}
                        alt="Avatar"
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{
                        width: '100%',
                        height: '100%',
                        background: 'var(--primary)',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '3rem',
                        fontWeight: 600
                      }}>
                        {(profile.display_name || user.username).charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <input
                    type="file"
                    id="avatar-upload"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="avatar-upload" className="btn btn-secondary btn-sm" style={{ marginBottom: '0.5rem', cursor: 'pointer' }}>
                    <Upload size={14} />
                    {uploadingAvatar ? 'Uploading...' : 'Upload Avatar'}
                  </label>
                  {profile.avatar_url && (
                    <button
                      onClick={handleRemoveAvatar}
                      className="btn btn-ghost btn-sm"
                      style={{ display: 'block', width: '100%' }}
                    >
                      Remove Avatar
                    </button>
                  )}
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    Max size: 5MB
                  </p>
                </div>
              </div>

              {/* Profile Form */}
              <div style={{ flex: 1 }}>
                <form onSubmit={handleProfileUpdate}>
                  <div className="form-group">
                    <label className="form-label">Display Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={profile.display_name}
                      onChange={(e) => setProfile({ ...profile, display_name: e.target.value })}
                      placeholder="Your name"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Email</label>
                    <input
                      type="email"
                      className="form-input"
                      value={profile.email}
                      disabled
                      style={{ background: 'var(--surface)', cursor: 'not-allowed' }}
                    />
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      Email cannot be changed
                    </p>
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </section>

        {/* Appearance Section */}
        <section className="card" style={{ marginBottom: '2rem' }}>
          <div className="card-body">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
              Appearance
            </h2>

            <div className="form-group">
              <label className="form-label">Theme</label>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={setLightTheme}
                  className={`btn ${theme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem'
                  }}
                >
                  <Sun size={18} />
                  Light Mode
                </button>
                <button
                  onClick={setDarkTheme}
                  className={`btn ${theme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem'
                  }}
                >
                  <Moon size={18} />
                  Dark Mode
                </button>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Choose your preferred color scheme
              </p>
            </div>
          </div>
        </section>

        {/* My Wikis Section */}
        <section className="card" style={{ marginBottom: '2rem' }}>
          <div className="card-body">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
              My Wikis ({wikis.length})
            </h2>

            {wikis.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem 0' }}>
                <Book size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
                <p className="text-secondary">You haven't created any wikis yet</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {wikis.map(wiki => (
                  <div
                    key={wiki.id}
                    className="card"
                    style={{
                      border: '1px solid var(--border)',
                      padding: '1rem'
                    }}
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div>
                          <Link
                            to={`/wiki/${wiki.id}`}
                            style={{
                              fontSize: '1rem',
                              fontWeight: 600,
                              color: 'var(--primary)',
                              textDecoration: 'none'
                            }}
                          >
                            {wiki.name}
                          </Link>
                          <div className="flex items-center gap-2 text-xs text-secondary" style={{ marginTop: '0.25rem' }}>
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
                      </div>
                      <div className="flex gap-2">
                        <Link
                          to={`/wiki/${wiki.id}/settings`}
                          className="btn btn-ghost btn-sm"
                        >
                          <Users size={14} />
                          Permissions
                        </Link>
                        <button
                          onClick={() => handleDeleteWiki(wiki.id)}
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--danger, #dc2626)' }}
                        >
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Danger Zone */}
        <section className="card" style={{ borderColor: 'var(--danger, #dc2626)' }}>
          <div className="card-body">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--danger, #dc2626)' }}>
              Danger Zone
            </h2>
            <p className="text-secondary" style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              Irreversible actions that will permanently affect your account.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                padding: '1rem',
                border: '1px solid var(--border)',
                borderRadius: '0.5rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                    Delete Account (Keep Wikis)
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
                    Delete your account but transfer wiki ownership. Your wikis will remain accessible.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteAccountModal(true)}
                  className="btn btn-secondary"
                  style={{
                    borderColor: 'var(--danger, #dc2626)',
                    color: 'var(--danger, #dc2626)'
                  }}
                >
                  Delete Account
                </button>
              </div>

              <div style={{
                padding: '1rem',
                border: '1px solid var(--danger, #dc2626)',
                borderRadius: '0.5rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(220, 38, 38, 0.05)'
              }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem', color: 'var(--danger, #dc2626)' }}>
                    Delete Account & All Wikis
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
                    Permanently delete your account and all wikis you own. This cannot be undone.
                  </p>
                </div>
                <button
                  onClick={() => setShowDeleteWithWikisModal(true)}
                  className="btn"
                  style={{
                    background: 'var(--danger, #dc2626)',
                    color: 'white'
                  }}
                >
                  Delete Everything
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Delete Account Modal (Keep Wikis) */}
      <Modal
        isOpen={showDeleteAccountModal}
        onClose={() => {
          setShowDeleteAccountModal(false);
          setDeleteConfirmation('');
          setError('');
        }}
        title="Delete Account"
        footer={
          <>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowDeleteAccountModal(false);
                setDeleteConfirmation('');
                setError('');
              }}
            >
              Cancel
            </button>
            <button
              className="btn"
              style={{ background: 'var(--danger, #dc2626)', color: 'white' }}
              onClick={() => handleDeleteAccount(false)}
              disabled={deleteConfirmation !== 'DELETE'}
            >
              Delete Account
            </button>
          </>
        }
      >
        <div style={{ marginBottom: '1rem' }}>
          <div className="flex items-start gap-3" style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(220, 38, 38, 0.1)', borderRadius: '0.5rem' }}>
            <AlertTriangle size={24} style={{ color: 'var(--danger, #dc2626)', flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>This action cannot be undone</div>
              <p style={{ fontSize: '0.875rem', margin: 0 }}>
                Your account will be permanently deleted. Your wikis will remain public and accessible, but you will lose ownership.
              </p>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              Type <strong>DELETE</strong> to confirm
            </label>
            <input
              type="text"
              className="form-input"
              value={deleteConfirmation}
              onChange={(e) => setDeleteConfirmation(e.target.value)}
              placeholder="DELETE"
            />
          </div>
        </div>
      </Modal>

      {/* Delete Account & Wikis Modal */}
      <Modal
        isOpen={showDeleteWithWikisModal}
        onClose={() => {
          setShowDeleteWithWikisModal(false);
          setDeleteConfirmation('');
          setError('');
        }}
        title="Delete Account & All Wikis"
        footer={
          <>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowDeleteWithWikisModal(false);
                setDeleteConfirmation('');
                setError('');
              }}
            >
              Cancel
            </button>
            <button
              className="btn"
              style={{ background: 'var(--danger, #dc2626)', color: 'white' }}
              onClick={() => handleDeleteAccount(true)}
              disabled={deleteConfirmation !== 'DELETE'}
            >
              Delete Everything
            </button>
          </>
        }
      >
        <div style={{ marginBottom: '1rem' }}>
          <div className="flex items-start gap-3" style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(220, 38, 38, 0.1)', borderRadius: '0.5rem' }}>
            <AlertTriangle size={24} style={{ color: 'var(--danger, #dc2626)', flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--danger, #dc2626)' }}>
                Warning: This will delete everything
              </div>
              <p style={{ fontSize: '0.875rem', margin: 0 }}>
                Your account AND all {wikis.length} wiki{wikis.length !== 1 ? 's' : ''} you own (including all pages and content) will be permanently deleted. This action cannot be undone.
              </p>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              Type <strong>DELETE</strong> to confirm
            </label>
            <input
              type="text"
              className="form-input"
              value={deleteConfirmation}
              onChange={(e) => setDeleteConfirmation(e.target.value)}
              placeholder="DELETE"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
