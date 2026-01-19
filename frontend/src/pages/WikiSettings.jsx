import { useState, useEffect } from 'react';
import { useParams, useOutletContext, useNavigate } from 'react-router-dom';
import { Save, UserPlus, Trash2, X, Upload, FileArchive } from 'lucide-react';
import { wikisAPI, searchAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';

export default function WikiSettings() {
  const { wikiId } = useParams();
  const { wiki } = useOutletContext();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false
  });
  const [saving, setSaving] = useState(false);
  const [members, setMembers] = useState([]);
  const [owner, setOwner] = useState(null);
  const [loadingMembers, setLoadingMembers] = useState(true);
  
  // Add member modal
  const [showAddMember, setShowAddMember] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [userResults, setUserResults] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newMemberRole, setNewMemberRole] = useState('viewer');
  const [addingMember, setAddingMember] = useState(false);
  
  // Import state
  const [showImport, setShowImport] = useState(false);
  const [archiveFile, setArchiveFile] = useState(null);
  const [pageTree, setPageTree] = useState([]);
  const [selectedParentPage, setSelectedParentPage] = useState(null);
  const [importing, setImporting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [importResult, setImportResult] = useState(null);
  const [importError, setImportError] = useState('');

  useEffect(() => {
    if (wiki) {
      setFormData({
        name: wiki.name,
        description: wiki.description || '',
        is_public: wiki.is_public
      });
    }
    loadMembers();
  }, [wiki]);

  const loadMembers = async () => {
    try {
      const response = await wikisAPI.listMembers(wikiId);
      setOwner(response.data.owner);
      setMembers(response.data.members);
    } catch (err) {
      console.error('Failed to load members:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await wikisAPI.update(wikiId, formData);
      alert('Settings saved successfully');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSearchUsers = async (query) => {
    setUserSearch(query);
    if (query.length < 2) {
      setUserResults([]);
      return;
    }

    try {
      const response = await searchAPI.searchUsers(query);
      // Filter out existing members and owner
      const existingIds = [owner?.id, ...members.map(m => m.id)];
      setUserResults(response.data.users.filter(u => !existingIds.includes(u.id)));
    } catch (err) {
      console.error('User search failed:', err);
    }
  };

  const handleAddMember = async () => {
    if (!selectedUser) return;

    setAddingMember(true);
    try {
      await wikisAPI.addMember(wikiId, {
        user_id: selectedUser.id,
        role: newMemberRole
      });
      await loadMembers();
      setShowAddMember(false);
      setSelectedUser(null);
      setUserSearch('');
      setUserResults([]);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to add member');
    } finally {
      setAddingMember(false);
    }
  };

  const handleUpdateRole = async (userId, role) => {
    try {
      await wikisAPI.updateMember(wikiId, userId, { role });
      setMembers(members.map(m => 
        m.id === userId ? { ...m, role } : m
      ));
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to update role');
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!confirm('Remove this member from the wiki?')) return;

    try {
      await wikisAPI.removeMember(wikiId, userId);
      setMembers(members.filter(m => m.id !== userId));
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to remove member');
    }
  };

  const handleDeleteWiki = async () => {
    if (!confirm('Are you sure you want to delete this wiki? This action cannot be undone.')) {
      return;
    }

    try {
      await wikisAPI.delete(wikiId);
      navigate('/');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete wiki');
    }
  };
  
  const loadPageTree = async () => {
    try {
      const response = await wikisAPI.getPageTree(wikiId);
      setPageTree(response.data.pages);
    } catch (err) {
      console.error('Failed to load page tree:', err);
    }
  };
  
  const handleShowImport = () => {
    setShowImport(true);
    loadPageTree();
  };
  
  const handleArchiveFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
      const fileName = file.name.toLowerCase();
      const isValid = validExtensions.some(ext => fileName.endsWith(ext));
      
      if (!isValid) {
        setImportError('Invalid file type. Please upload a .zip or .tar.gz file');
        setArchiveFile(null);
        return;
      }
      
      const maxSize = 500 * 1024 * 1024;
      if (file.size > maxSize) {
        setImportError(`File too large. Maximum size is 500MB (${(file.size / (1024 * 1024)).toFixed(1)}MB)`);
        setArchiveFile(null);
        return;
      }
      
      setArchiveFile(file);
      setImportError('');
    }
  };
  
  const handleImport = async () => {
    if (!archiveFile) return;
    
    setImporting(true);
    setImportError('');
    setImportResult(null);
    
    try {
      const formData = new FormData();
      formData.append('archive', archiveFile);
      if (selectedParentPage) {
        formData.append('parent_page_id', selectedParentPage.toString());
      }
      
      const response = await wikisAPI.importToExisting(wikiId, formData, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });
      
      setImportResult(response.data.import_result);
      
      // Reset form after short delay
      setTimeout(() => {
        setShowImport(false);
        setArchiveFile(null);
        setSelectedParentPage(null);
        setUploadProgress(0);
      }, 3000);
    } catch (err) {
      setImportError(err.response?.data?.error || 'Import failed');
      setImportResult(err.response?.data?.details || null);
    } finally {
      setImporting(false);
      setUploadProgress(0);
    }
  };

  const isOwner = owner?.id === user?.id;

  return (
    <div className="page-content">
      <h1 className="page-title mb-6">Wiki Settings</h1>

      <div className="card mb-6">
        <div className="card-header">
          <h3 className="font-semibold">General Settings</h3>
        </div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Wiki Name</label>
            <input
              type="text"
              className="form-input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-input"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="form-group">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_public}
                onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
              />
              <span>Make this wiki public</span>
            </label>
            <p className="text-xs text-secondary mt-1">
              Public wikis can be viewed by anyone with the link
            </p>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            <Save size={16} />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header flex justify-between items-center">
          <h3 className="font-semibold">Members</h3>
          {isOwner && (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setShowAddMember(true)}
            >
              <UserPlus size={16} />
              Add Member
            </button>
          )}
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {loadingMembers ? (
            <div className="loading-container">
              <div className="spinner" />
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 500 }}>User</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 500 }}>Role</th>
                  {isOwner && (
                    <th style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: 500 }}>Actions</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {owner && (
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div className="font-medium">{owner.display_name || owner.username}</div>
                      <div className="text-xs text-secondary">@{owner.username}</div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className="text-sm" style={{ 
                        background: 'var(--primary)', 
                        color: 'white',
                        padding: '0.125rem 0.5rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem'
                      }}>
                        Owner
                      </span>
                    </td>
                    {isOwner && <td></td>}
                  </tr>
                )}
                {members.map(member => (
                  <tr key={member.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <div className="font-medium">{member.display_name || member.username}</div>
                      <div className="text-xs text-secondary">@{member.username}</div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {isOwner ? (
                        <select
                          className="form-input"
                          value={member.role}
                          onChange={(e) => handleUpdateRole(member.id, e.target.value)}
                          style={{ width: 'auto', fontSize: '0.875rem' }}
                        >
                          <option value="viewer">Viewer</option>
                          <option value="editor">Editor</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span className="text-sm capitalize">{member.role}</span>
                      )}
                    </td>
                    {isOwner && (
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                        <button
                          className="btn btn-ghost btn-sm text-danger"
                          onClick={() => handleRemoveMember(member.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Import Section */}
      {(isOwner || user?.can_edit_wiki?.(wikiId)) && (
        <div className="card mb-6">
          <div className="card-header flex justify-between items-center">
            <h3 className="font-semibold">Import Pages from Archive</h3>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleShowImport}
            >
              <FileArchive size={16} />
              Import Archive
            </button>
          </div>
          <div className="card-body">
            <p className="text-sm text-secondary">
              Upload a .zip or .tar.gz archive containing markdown files and other assets. 
              The directory structure will be preserved as page hierarchy, and non-markdown files will be imported as attachments.
            </p>
          </div>
        </div>
      )}

      {isOwner && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <div className="card-header">
            <h3 className="font-semibold text-danger">Danger Zone</h3>
          </div>
          <div className="card-body">
            <p className="text-sm text-secondary mb-4">
              Once you delete a wiki, there is no going back. All pages and attachments will be permanently deleted.
            </p>
            <button
              className="btn btn-danger"
              onClick={handleDeleteWiki}
            >
              <Trash2 size={16} />
              Delete Wiki
            </button>
          </div>
        </div>
      )}

      {/* Add Member Modal */}
      <Modal
        isOpen={showAddMember}
        onClose={() => {
          setShowAddMember(false);
          setSelectedUser(null);
          setUserSearch('');
          setUserResults([]);
        }}
        title="Add Member"
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowAddMember(false)}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleAddMember}
              disabled={!selectedUser || addingMember}
            >
              {addingMember ? 'Adding...' : 'Add Member'}
            </button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Search Users</label>
          <input
            type="text"
            className="form-input"
            value={userSearch}
            onChange={(e) => handleSearchUsers(e.target.value)}
            placeholder="Search by username..."
          />
          
          {userResults.length > 0 && (
            <ul style={{ 
              listStyle: 'none', 
              border: '1px solid var(--border)',
              borderRadius: '0.375rem',
              marginTop: '0.5rem',
              maxHeight: 200,
              overflow: 'auto'
            }}>
              {userResults.map(u => (
                <li 
                  key={u.id}
                  className={`p-2 cursor-pointer ${selectedUser?.id === u.id ? 'bg-primary text-white' : ''}`}
                  style={{ 
                    background: selectedUser?.id === u.id ? 'var(--primary)' : undefined,
                    color: selectedUser?.id === u.id ? 'white' : undefined
                  }}
                  onClick={() => setSelectedUser(u)}
                >
                  <div className="font-medium">{u.display_name || u.username}</div>
                  <div className="text-xs" style={{ opacity: 0.7 }}>@{u.username}</div>
                </li>
              ))}
            </ul>
          )}
          
          {selectedUser && (
            <div className="mt-2 p-2 rounded" style={{ background: 'var(--background)' }}>
              Selected: <strong>{selectedUser.display_name || selectedUser.username}</strong>
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Role</label>
          <select
            className="form-input"
            value={newMemberRole}
            onChange={(e) => setNewMemberRole(e.target.value)}
          >
            <option value="viewer">Viewer - Can view pages</option>
            <option value="editor">Editor - Can edit pages</option>
            <option value="admin">Admin - Can manage members</option>
          </select>
        </div>
      </Modal>
      
      {/* Import Archive Modal */}
      <Modal
        isOpen={showImport}
        onClose={() => {
          setShowImport(false);
          setArchiveFile(null);
          setSelectedParentPage(null);
          setImportError('');
          setImportResult(null);
          setUploadProgress(0);
        }}
        title="Import Pages from Archive"
        footer={
          <>
            <button 
              className="btn btn-secondary"
              onClick={() => setShowImport(false)}
              disabled={importing}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleImport}
              disabled={!archiveFile || importing}
            >
              {importing ? (uploadProgress > 0 ? `Importing... ${uploadProgress}%` : 'Processing...') : 'Import'}
            </button>
          </>
        }
      >
        {importError && <div className="alert alert-error mb-4">{importError}</div>}
        
        {importResult && (
          <div className={`alert ${importResult.failure_count > 0 ? 'alert-warning' : 'alert-success'} mb-4`}>
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
        
        <div className="form-group">
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
            Maximum file size: 500MB. Supported formats: .zip, .tar, .tar.gz, .tgz
          </p>
        </div>
        
        <div className="form-group">
          <label className="form-label">Import Location (Optional)</label>
          <select
            className="form-input"
            value={selectedParentPage || ''}
            onChange={(e) => setSelectedParentPage(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">Root level (no parent)</option>
            {renderPageTreeOptions(pageTree)}
          </select>
          <p className="text-xs text-secondary mt-1">
            Select a parent page to import the archive under, or leave as root level to import at the top level
          </p>
        </div>
        
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
        
        <div className="alert alert-info mt-4" style={{ fontSize: '0.875rem' }}>
          <strong>How it works:</strong>
          <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
            <li>Markdown files (.md) become pages</li>
            <li>Directory structure maps to page hierarchy</li>
            <li>Directories with matching .md files: contents become children of that page</li>
            <li>Directories without .md files: blank page created with directory name</li>
            <li>Non-markdown files become attachments to their parent page</li>
            <li>Frontmatter (YAML) in markdown files used for title and tags</li>
            <li>If no frontmatter title, first H1 heading is used, otherwise filename</li>
          </ul>
        </div>
      </Modal>
    </div>
  );
}

function renderPageTreeOptions(pages, depth = 0) {
  return pages.flatMap(page => [
    <option key={page.id} value={page.id}>
      {'  '.repeat(depth)}└─ {page.title}
    </option>,
    ...renderPageTreeOptions(page.children || [], depth + 1)
  ]);
}
