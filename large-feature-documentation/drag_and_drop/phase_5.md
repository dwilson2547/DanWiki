# Phase 5: User Settings Integration (Day 3)

## Overview

**Priority: HIGH - Permanent disable functionality**

This phase adds a permanent disable option for the move confirmation modal to the user settings page. Users who find the confirmation annoying can disable it permanently, while still having the option to re-enable it later.

## Goals

- Add "Disable Move Confirmations" toggle to WikiSettings page
- Update user settings in database
- Integrate with confirmation check logic
- Add settings sync between tabs/windows
- Ensure settings persist across sessions
- Provide clear UI feedback
- Add help text explaining the feature

## Timeline

**Duration:** 0.5 days (Day 3 afternoon)

### Day 3 Afternoon: Settings Integration
- Add toggle to settings page
- Wire up API calls
- Test settings persistence
- Update documentation

## Technical Implementation

### Database Schema (Already Created in Phase 1)

```sql
-- User settings column already exists from Phase 1
-- Structure: user.settings JSONB column
{
  "drag_and_drop": {
    "disable_move_confirmation": false
  }
}
```

### User Settings API

```python
# backend/api/users.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db, User
from backend.utils.validation import validate_settings_update

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/users/me/settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    """Get current user's settings"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Return settings or default empty object
    settings = user.settings or {}
    
    return jsonify({
        'settings': settings
    }), 200

@users_bp.route('/api/users/me/settings', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user_settings():
    """Update user settings (full replace or partial merge)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or 'settings' not in data:
        return jsonify({'error': 'settings field required'}), 400
    
    new_settings = data['settings']
    
    # Validate settings structure
    validation_error = validate_settings_update(new_settings)
    if validation_error:
        return jsonify({'error': validation_error}), 400
    
    # PUT replaces entirely, PATCH merges
    if request.method == 'PUT':
        user.settings = new_settings
    else:  # PATCH
        current_settings = user.settings or {}
        current_settings.update(new_settings)
        user.settings = current_settings
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': user.settings
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/me/settings/drag-and-drop', methods=['PATCH'])
@jwt_required()
def update_drag_drop_settings():
    """Update only drag-and-drop settings"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if 'disable_move_confirmation' not in data:
        return jsonify({'error': 'disable_move_confirmation field required'}), 400
    
    disable = bool(data['disable_move_confirmation'])
    
    # Initialize settings if None
    if user.settings is None:
        user.settings = {}
    
    # Update nested setting
    if 'drag_and_drop' not in user.settings:
        user.settings['drag_and_drop'] = {}
    
    user.settings['drag_and_drop']['disable_move_confirmation'] = disable
    
    # Mark JSONB column as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(user, 'settings')
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Drag and drop settings updated',
            'settings': user.settings
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
```

### Settings Validation Utility

```python
# backend/utils/validation.py

def validate_settings_update(settings):
    """Validate user settings structure"""
    if not isinstance(settings, dict):
        return 'Settings must be a JSON object'
    
    # Validate drag_and_drop section if present
    if 'drag_and_drop' in settings:
        dd_settings = settings['drag_and_drop']
        if not isinstance(dd_settings, dict):
            return 'drag_and_drop must be an object'
        
        if 'disable_move_confirmation' in dd_settings:
            if not isinstance(dd_settings['disable_move_confirmation'], bool):
                return 'disable_move_confirmation must be a boolean'
    
    # Add more validation as needed
    return None
```

### Frontend Settings API

```javascript
// frontend/src/api/users.js

import api from './api';

export const usersAPI = {
  /**
   * Get current user's settings
   */
  async getSettings() {
    const response = await api.get('/users/me/settings');
    return response.data.settings;
  },
  
  /**
   * Update user settings (full replace)
   */
  async updateSettings(settings) {
    const response = await api.put('/users/me/settings', { settings });
    return response.data;
  },
  
  /**
   * Patch user settings (partial update)
   */
  async patchSettings(settingsPartial) {
    const response = await api.patch('/users/me/settings', {
      settings: settingsPartial
    });
    return response.data;
  },
  
  /**
   * Update drag and drop settings specifically
   */
  async updateDragDropSettings(disableMoveConfirmation) {
    const response = await api.patch('/users/me/settings/drag-and-drop', {
      disable_move_confirmation: disableMoveConfirmation
    });
    return response.data;
  }
};
```

### Settings Context

```javascript
// frontend/src/contexts/SettingsContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { usersAPI } from '../api/users';
import { showError } from '../utils/toast';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadSettings();
    
    // Listen for settings changes from other tabs
    const handleStorageChange = (e) => {
      if (e.key === 'user_settings_updated') {
        loadSettings();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);
  
  const loadSettings = async () => {
    try {
      const userSettings = await usersAPI.getSettings();
      setSettings(userSettings);
    } catch (error) {
      console.error('Failed to load settings:', error);
      showError('Failed to load user settings');
    } finally {
      setLoading(false);
    }
  };
  
  const updateDragDropSettings = async (disableConfirmation) => {
    try {
      await usersAPI.updateDragDropSettings(disableConfirmation);
      
      // Update local state
      setSettings(prev => ({
        ...prev,
        drag_and_drop: {
          ...prev?.drag_and_drop,
          disable_move_confirmation: disableConfirmation
        }
      }));
      
      // Notify other tabs
      localStorage.setItem('user_settings_updated', Date.now().toString());
      
      return true;
    } catch (error) {
      showError('Failed to update settings');
      throw error;
    }
  };
  
  const getDragDropSettings = () => {
    return settings?.drag_and_drop || {
      disable_move_confirmation: false
    };
  };
  
  return (
    <SettingsContext.Provider value={{
      settings,
      loading,
      updateDragDropSettings,
      getDragDropSettings,
      refreshSettings: loadSettings
    }}>
      {children}
    </SettingsContext.Provider>
  );
};
```

### Updated shouldShowMoveConfirmation

```javascript
// frontend/src/utils/muteHelper.js

import { MUTE_KEY } from './constants';

/**
 * Check if move confirmation should be shown
 * @param {Object} userSettings - User settings from SettingsContext
 * @returns {boolean} true if confirmation should be shown
 */
export const shouldShowMoveConfirmation = (userSettings) => {
  // Check permanent disable first
  if (userSettings?.drag_and_drop?.disable_move_confirmation) {
    return false;
  }
  
  // Check temporary mute
  const muteData = getMuteData();
  if (muteData && muteData.expiresAt > Date.now()) {
    return false;
  }
  
  return true;
};

export const getMuteData = () => {
  try {
    const data = localStorage.getItem(MUTE_KEY);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
};

export const setMuteData = (minutes) => {
  const expiresAt = Date.now() + (minutes * 60 * 1000);
  localStorage.setItem(MUTE_KEY, JSON.stringify({ expiresAt }));
};

export const clearMuteData = () => {
  localStorage.removeItem(MUTE_KEY);
};
```

### WikiSettings Page Component

```jsx
// frontend/src/pages/WikiSettings.jsx (add section)

import React, { useState } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { showSuccess, showError } from '../utils/toast';
import './WikiSettings.css';

export const WikiSettings = () => {
  const { getDragDropSettings, updateDragDropSettings } = useSettings();
  const [saving, setSaving] = useState(false);
  
  const dragDropSettings = getDragDropSettings();
  const [disableConfirmation, setDisableConfirmation] = useState(
    dragDropSettings.disable_move_confirmation || false
  );
  
  const handleToggleChange = async (e) => {
    const newValue = e.target.checked;
    setDisableConfirmation(newValue);
    setSaving(true);
    
    try {
      await updateDragDropSettings(newValue);
      showSuccess('Settings saved');
    } catch (error) {
      // Revert on error
      setDisableConfirmation(!newValue);
      showError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <div className="wiki-settings">
      <h1>Wiki Settings</h1>
      
      {/* Other settings sections... */}
      
      <section className="settings-section">
        <h2>Page Organization</h2>
        
        <div className="setting-item">
          <div className="setting-header">
            <label htmlFor="disable-move-confirmation">
              Disable Move Confirmations
            </label>
            <input
              id="disable-move-confirmation"
              type="checkbox"
              checked={disableConfirmation}
              onChange={handleToggleChange}
              disabled={saving}
              className="toggle-switch"
            />
          </div>
          
          <p className="setting-description">
            When enabled, page moves via drag-and-drop will not show a confirmation dialog.
            You can still temporarily mute confirmations for 1-60 minutes when they appear.
          </p>
          
          {disableConfirmation && (
            <div className="setting-warning">
              <span className="warning-icon">⚠️</span>
              <span>
                Be careful when dragging pages - changes will be applied immediately without confirmation.
              </span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
```

### WikiSettings Styles

```css
/* frontend/src/pages/WikiSettings.css */

.wiki-settings {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.settings-section {
  margin-bottom: 32px;
  padding: 20px;
  background: var(--card-bg, white);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h2 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 20px;
  color: var(--text-primary);
}

.setting-item {
  margin-bottom: 16px;
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.setting-header label {
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
}

.setting-description {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 8px 0;
}

.setting-warning {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: var(--warning-bg, #fef3c7);
  border: 1px solid var(--warning-border, #fcd34d);
  border-radius: 6px;
  font-size: 14px;
  color: var(--warning-text, #92400e);
  margin-top: 8px;
}

.warning-icon {
  font-size: 18px;
  flex-shrink: 0;
}

/* Toggle switch */
.toggle-switch {
  position: relative;
  width: 48px;
  height: 24px;
  appearance: none;
  background: var(--toggle-off, #d1d5db);
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.3s;
  outline: none;
}

.toggle-switch:checked {
  background: var(--primary, #3b82f6);
}

.toggle-switch::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 10px;
  top: 2px;
  left: 2px;
  background: white;
  transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch:checked::before {
  transform: translateX(24px);
}

.toggle-switch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-switch:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .settings-section {
    background: var(--card-bg-dark, #1f2937);
  }
  
  .toggle-switch {
    background: var(--toggle-off-dark, #4b5563);
  }
  
  .setting-warning {
    background: rgba(252, 211, 77, 0.1);
    border-color: rgba(252, 211, 77, 0.3);
    color: #fcd34d;
  }
}
```

### Update PageTree to Use Settings

```jsx
// frontend/src/components/PageTree.jsx

import { useSettings } from '../contexts/SettingsContext';

export const PageTree = ({ wikiId, pages, onRefresh }) => {
  const { getDragDropSettings } = useSettings();
  const dragDropSettings = getDragDropSettings();
  
  const handleMoveRequest = async (dragData, targetPage) => {
    if (dragData.pageId === targetPage?.id) {
      return;
    }
    
    // Pass settings to check function
    if (shouldShowMoveConfirmation(dragDropSettings)) {
      setMoveConfirmation({...});
    } else {
      await executeMove(dragData.pageId, targetPage?.id || null);
    }
  };
  
  // ... rest of component
};
```

## Testing Requirements

### API Tests

```python
# tests/test_user_settings_api.py

def test_get_user_settings(client, auth_token):
    """Test getting user settings"""
    response = client.get(
        '/api/users/me/settings',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert 'settings' in response.json

def test_update_drag_drop_settings(client, auth_token):
    """Test updating drag and drop settings"""
    response = client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': True},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    # Verify persisted
    response = client.get(
        '/api/users/me/settings',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    settings = response.json['settings']
    assert settings['drag_and_drop']['disable_move_confirmation'] is True

def test_settings_validation(client, auth_token):
    """Test settings validation"""
    response = client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': 'not a boolean'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 400
```

### Component Tests

```javascript
// tests/pages/WikiSettings.test.jsx

describe('WikiSettings drag-and-drop section', () => {
  test('renders toggle', () => {
    render(<WikiSettings />);
    expect(screen.getByLabelText('Disable Move Confirmations')).toBeInTheDocument();
  });
  
  test('toggle reflects current setting', () => {
    // Mock settings with disable=true
    render(<WikiSettings />);
    const toggle = screen.getByRole('checkbox');
    expect(toggle).toBeChecked();
  });
  
  test('changing toggle updates settings', async () => {
    render(<WikiSettings />);
    const toggle = screen.getByRole('checkbox');
    
    fireEvent.click(toggle);
    
    await waitFor(() => {
      expect(mockUpdateSettings).toHaveBeenCalledWith(true);
    });
  });
  
  test('shows warning when disabled', () => {
    // Mock with disable=true
    render(<WikiSettings />);
    expect(screen.getByText(/Be careful when dragging/)).toBeInTheDocument();
  });
});
```

### Integration Tests

```javascript
// tests/integration/settingsPersistence.test.jsx

describe('Settings persistence', () => {
  test('settings persist across page reloads', async () => {
    // Enable disable confirmation
    await usersAPI.updateDragDropSettings(true);
    
    // Reload page
    window.location.reload();
    
    // Verify still disabled
    const settings = await usersAPI.getSettings();
    expect(settings.drag_and_drop.disable_move_confirmation).toBe(true);
  });
  
  test('settings sync across tabs', async () => {
    // Update in tab 1
    await updateDragDropSettings(true);
    
    // Simulate storage event in tab 2
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'user_settings_updated'
    }));
    
    // Verify tab 2 sees update
    await waitFor(() => {
      expect(getDragDropSettings().disable_move_confirmation).toBe(true);
    });
  });
});
```

## Success Criteria

- ✓ Toggle appears in WikiSettings page
- ✓ Toggle updates database
- ✓ Settings persist across sessions
- ✓ Settings sync across tabs
- ✓ shouldShowMoveConfirmation respects permanent disable
- ✓ Warning message shown when enabled
- ✓ Help text is clear
- ✓ All tests pass
- ✓ API validates settings properly

## Next Phase

After Phase 5 completion, proceed to **Phase 6: Styling** to refine the visual design and ensure consistency across the feature.

---

## Progress Tracking

### Feature 1: Backend - User Settings API
- [ ] Open backend/api/users.py
- [ ] Create users Blueprint
- [ ] Add GET /api/users/me/settings endpoint
- [ ] Return user.settings or empty object
- [ ] Add PUT /api/users/me/settings (full replace)
- [ ] Add PATCH /api/users/me/settings (merge)
- [ ] Add PATCH /api/users/me/settings/drag-and-drop
- [ ] Test all endpoints with Postman/curl

### Feature 2: Settings Validation
- [ ] Create backend/utils/validation.py
- [ ] Implement validate_settings_update function
- [ ] Validate settings is dict
- [ ] Validate drag_and_drop section structure
- [ ] Validate disable_move_confirmation is boolean
- [ ] Add error messages
- [ ] Test validation with invalid data
- [ ] Test validation with valid data

### Feature 3: JSONB Column Modification
- [ ] Import flag_modified from SQLAlchemy
- [ ] Call flag_modified after nested update
- [ ] Test that updates persist correctly
- [ ] Verify JSON structure in database
- [ ] Test with multiple updates

### Feature 4: Frontend - Users API Module
- [ ] Create frontend/src/api/users.js
- [ ] Add getSettings method
- [ ] Add updateSettings method (PUT)
- [ ] Add patchSettings method (PATCH)
- [ ] Add updateDragDropSettings helper
- [ ] Test API methods
- [ ] Add error handling

### Feature 5: Settings Context
- [ ] Create frontend/src/contexts/SettingsContext.jsx
- [ ] Create SettingsContext
- [ ] Create SettingsProvider component
- [ ] Add settings state
- [ ] Add loading state
- [ ] Implement loadSettings function
- [ ] Call API to fetch settings
- [ ] Store in state

### Feature 6: Settings Context - Update Method
- [ ] Implement updateDragDropSettings
- [ ] Call API to update settings
- [ ] Update local state optimistically
- [ ] Handle errors and revert
- [ ] Show success/error toasts
- [ ] Test update flow

### Feature 7: Settings Context - Helper Methods
- [ ] Implement getDragDropSettings
- [ ] Return default if not set
- [ ] Add refreshSettings method
- [ ] Export useSettings hook
- [ ] Test hook usage

### Feature 8: Cross-Tab Sync
- [ ] Listen for storage events
- [ ] Reload settings on storage change
- [ ] Emit storage event after update
- [ ] Use 'user_settings_updated' key
- [ ] Test multi-tab scenario
- [ ] Verify sync works

### Feature 9: Update shouldShowMoveConfirmation
- [ ] Open frontend/src/utils/muteHelper.js
- [ ] Add userSettings parameter
- [ ] Check permanent disable first
- [ ] Return false if permanently disabled
- [ ] Fall back to temporary mute check
- [ ] Update function JSDoc
- [ ] Test with different settings

### Feature 10: WikiSettings Page - Toggle UI
- [ ] Open frontend/src/pages/WikiSettings.jsx
- [ ] Import useSettings hook
- [ ] Get getDragDropSettings
- [ ] Add local state for checkbox
- [ ] Initialize from settings
- [ ] Render Page Organization section
- [ ] Add toggle input
- [ ] Add label

### Feature 11: WikiSettings Page - Toggle Handler
- [ ] Implement handleToggleChange
- [ ] Get new value from event
- [ ] Set saving state
- [ ] Call updateDragDropSettings
- [ ] Show success toast
- [ ] Handle errors and revert
- [ ] Clear saving state
- [ ] Disable toggle while saving

### Feature 12: WikiSettings Page - Description
- [ ] Add setting-description paragraph
- [ ] Explain what toggle does
- [ ] Mention temporary mute option
- [ ] Keep text concise
- [ ] Test readability

### Feature 13: WikiSettings Page - Warning
- [ ] Conditionally render warning
- [ ] Show only when disabled
- [ ] Add warning icon
- [ ] Explain consequences
- [ ] Style appropriately
- [ ] Test visibility

### Feature 14: WikiSettings Styles
- [ ] Create/update WikiSettings.css
- [ ] Style settings-section
- [ ] Style setting-item
- [ ] Style setting-header layout
- [ ] Style setting-description
- [ ] Style setting-warning
- [ ] Add card background and shadow

### Feature 15: Toggle Switch Styles
- [ ] Style .toggle-switch
- [ ] Remove default checkbox appearance
- [ ] Add background and border-radius
- [ ] Style ::before pseudo-element (circle)
- [ ] Add checked state styles
- [ ] Add transition animations
- [ ] Style disabled state
- [ ] Add focus state

### Feature 16: Dark Mode Styles
- [ ] Add dark mode media query
- [ ] Adjust card background
- [ ] Adjust toggle colors
- [ ] Adjust warning colors
- [ ] Test in dark mode
- [ ] Verify contrast

### Feature 17: Update PageTree Component
- [ ] Open frontend/src/components/PageTree.jsx
- [ ] Import useSettings
- [ ] Call getDragDropSettings
- [ ] Pass settings to shouldShowMoveConfirmation
- [ ] Remove hardcoded settings checks
- [ ] Test with different settings

### Feature 18: Provider Integration
- [ ] Wrap app in SettingsProvider
- [ ] Place above PageTree in tree
- [ ] Test provider accessible
- [ ] Verify no prop drilling needed

### Feature 19: API Tests
- [ ] Write test: get user settings
- [ ] Write test: update drag-and-drop settings
- [ ] Write test: settings validation
- [ ] Write test: invalid boolean type
- [ ] Write test: unauthorized access
- [ ] Write test: PUT vs PATCH behavior
- [ ] Run all API tests

### Feature 20: Component Tests
- [ ] Write test: toggle renders
- [ ] Write test: toggle reflects setting
- [ ] Write test: changing toggle calls API
- [ ] Write test: warning shows when disabled
- [ ] Write test: saving state disables toggle
- [ ] Write test: error reverts toggle
- [ ] Run component tests

### Feature 21: Integration Tests
- [ ] Write test: settings persist across reload
- [ ] Write test: settings sync across tabs
- [ ] Write test: disabled setting prevents confirmation
- [ ] Write test: enabled setting shows confirmation
- [ ] Run integration tests

### Feature 22: Manual Testing
- [ ] Open WikiSettings page
- [ ] Toggle disable confirmation
- [ ] Verify saves successfully
- [ ] Refresh page, verify persists
- [ ] Drag and drop page
- [ ] Verify no confirmation shown
- [ ] Toggle back on
- [ ] Verify confirmation shown again
- [ ] Test in multiple tabs
- [ ] Verify sync works

### Feature 23: Documentation
- [ ] Document settings API endpoints
- [ ] Add usage examples
- [ ] Document SettingsContext
- [ ] Document useSettings hook
- [ ] Add user guide for toggle
- [ ] Update README
