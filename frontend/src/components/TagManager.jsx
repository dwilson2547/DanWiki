import { useState, useEffect } from 'react';
import { X, Plus, Tag as TagIcon, Bot, User as UserIcon, CheckCircle } from 'lucide-react';
import { tagsAPI } from '../services/api';
import '../styles/TagManager.css';

export default function TagManager({ wikiId, pageId, initialTags = [], readOnly = false, onTagsChange }) {
  const [tags, setTags] = useState(initialTags);
  const [availableTags, setAvailableTags] = useState([]);
  const [showTagInput, setShowTagInput] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setTags(initialTags);
  }, [initialTags]);

  useEffect(() => {
    if (!readOnly) {
      loadAvailableTags();
    }
  }, [wikiId, readOnly]);

  const loadAvailableTags = async () => {
    try {
      const response = await tagsAPI.list(wikiId);
      setAvailableTags(response.data.tags);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  };

  const handleAddExistingTag = async (tag) => {
    if (tags.find(t => t.id === tag.id)) {
      return; // Tag already added
    }

    setLoading(true);
    setError(null);
    try {
      const response = await tagsAPI.addTagToPage(wikiId, pageId, tag.id);
      const updatedTags = response.data.tags;
      setTags(updatedTags);
      if (onTagsChange) {
        onTagsChange(updatedTags);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add tag');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    setLoading(true);
    setError(null);
    try {
      // Create the tag
      const createResponse = await tagsAPI.create(wikiId, {
        name: newTagName.trim(),
        color: newTagColor
      });
      const newTag = createResponse.data.tag;

      // Add it to the page
      const addResponse = await tagsAPI.addTagToPage(wikiId, pageId, newTag.id);
      const updatedTags = addResponse.data.tags;
      setTags(updatedTags);
      
      // Refresh available tags
      await loadAvailableTags();
      
      // Reset form
      setNewTagName('');
      setNewTagColor('#3B82F6');
      setShowTagInput(false);

      if (onTagsChange) {
        onTagsChange(updatedTags);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create tag');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTag = async (tagId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await tagsAPI.removeTagFromPage(wikiId, pageId, tagId);
      const updatedTags = response.data.tags;
      setTags(updatedTags);
      if (onTagsChange) {
        onTagsChange(updatedTags);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to remove tag');
    } finally {
      setLoading(false);
    }
  };

  const getUnusedTags = () => {
    return availableTags.filter(availableTag => 
      !tags.find(pageTag => pageTag.id === availableTag.id)
    );
  };

  const generateRandomColor = () => {
    const colors = [
      '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
      '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  const getSourceIcon = (tag) => {
    if (tag.source === 'ai' || tag.auto_generated) {
      return <Bot size={10} className="tag-source-icon" title={`AI-generated${tag.model_name ? ` by ${tag.model_name}` : ''}${tag.confidence ? ` (${Math.round(tag.confidence * 100)}% confidence)` : ''}`} />;
    } else if (tag.source === 'human') {
      return <UserIcon size={10} className="tag-source-icon" title="Human-created" />;
    }
    return null;
  };

  const getVerificationBadge = (tag) => {
    if (tag.verified) {
      return <CheckCircle size={10} className="tag-verified-icon" title="Verified by human" />;
    }
    return null;
  };

  return (
    <div className="tag-manager">
      <div className="tags-container">
        {tags.length === 0 && readOnly && (
          <span className="no-tags">No tags</span>
        )}
        
        {tags.map(tag => (
          <span
            key={tag.id}
            className={`tag ${tag.auto_generated ? 'tag-ai-generated' : ''} ${tag.verified ? 'tag-verified' : ''}`}
            style={{
              backgroundColor: tag.color || '#6B7280',
              color: '#FFFFFF'
            }}
            title={
              tag.auto_generated 
                ? `AI-generated tag${tag.confidence ? ` (${Math.round(tag.confidence * 100)}% confidence)` : ''}${tag.model_name ? ` by ${tag.model_name}` : ''}${tag.verified ? ' - Verified' : ''}`
                : tag.verified ? 'Human-created - Verified' : 'Human-created'
            }
          >
            <TagIcon size={12} />
            <span>{tag.name}</span>
            <span className="tag-badges">
              {getSourceIcon(tag)}
              {getVerificationBadge(tag)}
            </span>
            {!readOnly && (
              <button
                onClick={() => handleRemoveTag(tag.id)}
                className="tag-remove-btn"
                disabled={loading}
                title="Remove tag"
              >
                <X size={12} />
              </button>
            )}
          </span>
        ))}

        {!readOnly && (
          <button
            onClick={() => setShowTagInput(!showTagInput)}
            className="add-tag-btn"
            disabled={loading}
            title="Add tag"
          >
            <Plus size={14} />
            <span>Add Tag</span>
          </button>
        )}
      </div>

      {!readOnly && showTagInput && (
        <div className="tag-input-panel">
          {error && (
            <div className="tag-error">{error}</div>
          )}

          {/* Existing tags dropdown */}
          {getUnusedTags().length > 0 && (
            <div className="existing-tags-section">
              <h4>Select existing tag:</h4>
              <div className="existing-tags-list">
                {getUnusedTags().map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => handleAddExistingTag(tag)}
                    className="existing-tag-btn"
                    style={{
                      backgroundColor: tag.color || '#6B7280',
                      color: '#FFFFFF'
                    }}
                    disabled={loading}
                  >
                    <TagIcon size={12} />
                    <span>{tag.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Create new tag form */}
          <div className="new-tag-section">
            <h4>Or create a new tag:</h4>
            <form onSubmit={handleCreateTag} className="new-tag-form">
              <div className="form-row">
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  placeholder="Tag name"
                  maxLength={50}
                  className="tag-name-input"
                  disabled={loading}
                />
                <input
                  type="color"
                  value={newTagColor}
                  onChange={(e) => setNewTagColor(e.target.value)}
                  className="tag-color-input"
                  disabled={loading}
                  title="Tag color"
                />
                <button
                  type="button"
                  onClick={() => setNewTagColor(generateRandomColor())}
                  className="random-color-btn"
                  disabled={loading}
                  title="Random color"
                >
                  🎲
                </button>
              </div>
              <div className="form-actions">
                <button
                  type="submit"
                  disabled={!newTagName.trim() || loading}
                  className="create-tag-btn"
                >
                  {loading ? 'Creating...' : 'Create & Add'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowTagInput(false);
                    setNewTagName('');
                    setError(null);
                  }}
                  className="cancel-btn"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
