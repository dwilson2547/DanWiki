# Phase 3: Confirmation Modal Component (Day 2)

## Overview

**Priority: HIGH - User confirmation interface**

This phase creates the confirmation dialog that appears when users drag and drop pages. The modal includes options to temporarily or permanently mute the confirmation, providing flexibility for both cautious and power users.

## Goals

- Create MoveConfirmationModal component
- Implement mute duration options (1, 5, 30, 60 minutes, permanent)
- Add localStorage logic for temporary muting
- Integrate with user settings for permanent disable
- Style modal consistently with app design
- Implement accessibility features

## Timeline

**Duration:** 1 day (Day 2 of implementation)

### Morning: Modal Component
- Create component structure
- Implement UI layout
- Add mute options

### Afternoon: Logic & Styling
- Implement mute logic
- Add localStorage handling
- Style and test

## Technical Implementation

### Component Structure

```jsx
// frontend/src/components/MoveConfirmationModal.jsx

import React, { useState } from 'react';
import './MoveConfirmationModal.css';

export const MoveConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  pageTitle,
  newParentTitle,
  hasChildren,
  onMuteChange
}) => {
  const [muteOption, setMuteOption] = useState('0');
  const [applyMute, setApplyMute] = useState(false);
  const [loading, setLoading] = useState(false);
  
  if (!isOpen) return null;
  
  const handleConfirm = async () => {
    setLoading(true);
    
    try {
      // Apply mute setting if checked
      if (applyMute && muteOption !== '0') {
        await handleMute(muteOption);
      }
      
      // Execute move
      await onConfirm();
      
      // Close modal
      onClose();
    } catch (error) {
      console.error('Failed to move page:', error);
      // Error handled by parent
    } finally {
      setLoading(false);
    }
  };
  
  const handleMute = async (duration) => {
    if (duration === 'permanent') {
      // Update user settings via API
      if (onMuteChange) {
        await onMuteChange('permanent');
      }
      // Also set localStorage for immediate effect
      localStorage.setItem('moveMuteUntil', 'permanent');
    } else {
      // Set temporary mute in localStorage
      const minutes = parseInt(duration, 10);
      const expiresAt = new Date(Date.now() + minutes * 60 * 1000);
      localStorage.setItem('moveMuteUntil', expiresAt.toISOString());
    }
  };
  
  const destinationText = newParentTitle 
    ? `under "${newParentTitle}"`
    : 'to root level';
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content move-confirmation-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Move Page?</h2>
          <button 
            className="modal-close" 
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        
        <div className="modal-body">
          <p className="confirmation-message">
            Are you sure you want to move <strong>{pageTitle}</strong>
            {hasChildren && ' and its children'} {destinationText}?
          </p>
          
          {hasChildren && (
            <div className="move-confirmation-warning">
              <svg className="warning-icon" width="20" height="20" viewBox="0 0 20 20">
                <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm1 15H9v-2h2v2zm0-4H9V5h2v6z"/>
              </svg>
              <span>This page has children. The entire structure will be moved together.</span>
            </div>
          )}
          
          <div className="mute-options">
            <label className="mute-checkbox">
              <input
                type="checkbox"
                checked={applyMute}
                onChange={e => setApplyMute(e.target.checked)}
              />
              <span>Don't ask again for:</span>
            </label>
            
            {applyMute && (
              <select 
                className="mute-dropdown"
                value={muteOption}
                onChange={e => setMuteOption(e.target.value)}
              >
                <option value="1">1 minute</option>
                <option value="5">5 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">60 minutes</option>
                <option value="permanent">Permanently</option>
              </select>
            )}
          </div>
        </div>
        
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? 'Moving...' : 'Move Page'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

### Styling

```css
/* frontend/src/components/MoveConfirmationModal.css */

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--background);
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: auto;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background-color: var(--hover-bg);
}

.modal-body {
  padding: 20px;
}

.confirmation-message {
  margin: 0 0 16px 0;
  color: var(--text-primary);
  line-height: 1.5;
}

.confirmation-message strong {
  color: var(--primary);
}

.move-confirmation-warning {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background-color: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #ffc107;
  border-radius: 4px;
  margin-bottom: 16px;
}

.warning-icon {
  flex-shrink: 0;
  fill: #ffc107;
  margin-top: 2px;
}

.move-confirmation-warning span {
  color: var(--text-primary);
  font-size: 0.9rem;
  line-height: 1.4;
}

.mute-options {
  border-top: 1px solid var(--border);
  padding-top: 16px;
  margin-top: 16px;
}

.mute-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-bottom: 12px;
}

.mute-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.mute-checkbox span {
  color: var(--text-primary);
  font-size: 0.95rem;
}

.mute-dropdown {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-primary);
  font-size: 0.95rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.mute-dropdown:focus {
  outline: none;
  border-color: var(--primary);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--surface);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--hover-bg);
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .modal-overlay {
    background-color: rgba(0, 0, 0, 0.7);
  }
  
  .move-confirmation-warning {
    background-color: rgba(255, 193, 7, 0.15);
  }
}

/* Mobile responsive */
@media (max-width: 600px) {
  .modal-content {
    width: 95%;
    margin: 0 10px;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px;
  }
  
  .modal-footer {
    flex-direction: column-reverse;
  }
  
  .modal-footer .btn {
    width: 100%;
  }
}
```

### localStorage Helper

```javascript
// frontend/src/utils/muteHelper.js

/**
 * Check if move confirmation should be shown
 * @returns {boolean} True if confirmation should be shown
 */
export const shouldShowMoveConfirmation = () => {
  // Check user settings from localStorage
  const userSettings = JSON.parse(localStorage.getItem('userSettings') || '{}');
  if (userSettings.disable_move_confirmation === true) {
    return false;
  }
  
  // Check temporary mute
  const muteUntil = localStorage.getItem('moveMuteUntil');
  
  if (muteUntil === 'permanent') {
    return false;
  }
  
  if (muteUntil) {
    const expiresAt = new Date(muteUntil);
    if (expiresAt > new Date()) {
      return false; // Still muted
    } else {
      // Mute expired, clear it
      localStorage.removeItem('moveMuteUntil');
    }
  }
  
  return true;
};

/**
 * Set temporary move confirmation mute
 * @param {number} minutes - Number of minutes to mute
 */
export const setTemporaryMute = (minutes) => {
  const expiresAt = new Date(Date.now() + minutes * 60 * 1000);
  localStorage.setItem('moveMuteUntil', expiresAt.toISOString());
};

/**
 * Set permanent move confirmation mute
 */
export const setPermanentMute = () => {
  localStorage.setItem('moveMuteUntil', 'permanent');
};

/**
 * Clear move confirmation mute
 */
export const clearMute = () => {
  localStorage.removeItem('moveMuteUntil');
};

/**
 * Get time remaining on temporary mute
 * @returns {number|null} Minutes remaining, or null if not muted or permanent
 */
export const getMuteTimeRemaining = () => {
  const muteUntil = localStorage.getItem('moveMuteUntil');
  
  if (!muteUntil || muteUntil === 'permanent') {
    return null;
  }
  
  const expiresAt = new Date(muteUntil);
  const now = new Date();
  
  if (expiresAt <= now) {
    localStorage.removeItem('moveMuteUntil');
    return null;
  }
  
  const msRemaining = expiresAt - now;
  return Math.ceil(msRemaining / 60000); // Convert to minutes
};
```

## Testing Requirements

### Component Tests

```javascript
// tests/components/MoveConfirmationModal.test.jsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MoveConfirmationModal } from '../MoveConfirmationModal';

describe('MoveConfirmationModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    pageTitle: 'Test Page',
    newParentTitle: 'Parent Page',
    hasChildren: false,
    onMuteChange: jest.fn()
  };
  
  test('renders when open', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    expect(screen.getByText('Move Page?')).toBeInTheDocument();
  });
  
  test('does not render when closed', () => {
    render(<MoveConfirmationModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Move Page?')).not.toBeInTheDocument();
  });
  
  test('displays correct confirmation message', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    expect(screen.getByText(/Test Page/)).toBeInTheDocument();
    expect(screen.getByText(/under "Parent Page"/)).toBeInTheDocument();
  });
  
  test('shows warning for pages with children', () => {
    render(<MoveConfirmationModal {...defaultProps} hasChildren={true} />);
    expect(screen.getByText(/entire structure will be moved/)).toBeInTheDocument();
  });
  
  test('shows mute dropdown when checkbox checked', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });
  
  test('calls onConfirm when Move Page clicked', async () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    const confirmButton = screen.getByText('Move Page');
    fireEvent.click(confirmButton);
    await waitFor(() => {
      expect(defaultProps.onConfirm).toHaveBeenCalled();
    });
  });
  
  test('calls onClose when Cancel clicked', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });
  
  test('calls onMuteChange when permanent selected', async () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    
    // Check mute checkbox
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);
    
    // Select permanent
    const dropdown = screen.getByRole('combobox');
    fireEvent.change(dropdown, { target: { value: 'permanent' } });
    
    // Confirm
    const confirmButton = screen.getByText('Move Page');
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(defaultProps.onMuteChange).toHaveBeenCalledWith('permanent');
    });
  });
});
```

### localStorage Tests

```javascript
// tests/utils/muteHelper.test.js

import {
  shouldShowMoveConfirmation,
  setTemporaryMute,
  setPermanentMute,
  clearMute,
  getMuteTimeRemaining
} from '../utils/muteHelper';

describe('muteHelper', () => {
  beforeEach(() => {
    localStorage.clear();
  });
  
  test('shouldShowMoveConfirmation returns true by default', () => {
    expect(shouldShowMoveConfirmation()).toBe(true);
  });
  
  test('shouldShowMoveConfirmation returns false when permanently muted', () => {
    setPermanentMute();
    expect(shouldShowMoveConfirmation()).toBe(false);
  });
  
  test('shouldShowMoveConfirmation returns false during temporary mute', () => {
    setTemporaryMute(5);
    expect(shouldShowMoveConfirmation()).toBe(false);
  });
  
  test('shouldShowMoveConfirmation returns true after mute expires', () => {
    // Set mute that expires immediately
    const past = new Date(Date.now() - 1000).toISOString();
    localStorage.setItem('moveMuteUntil', past);
    expect(shouldShowMoveConfirmation()).toBe(true);
  });
  
  test('getMuteTimeRemaining returns correct minutes', () => {
    setTemporaryMute(5);
    const remaining = getMuteTimeRemaining();
    expect(remaining).toBeGreaterThan(4);
    expect(remaining).toBeLessThanOrEqual(5);
  });
  
  test('clearMute removes localStorage item', () => {
    setPermanentMute();
    clearMute();
    expect(localStorage.getItem('moveMuteUntil')).toBeNull();
  });
});
```

## Success Criteria

- ✓ Modal renders correctly when open
- ✓ Modal doesn't render when closed
- ✓ Correct confirmation message displayed
- ✓ Warning shown for pages with children
- ✓ Mute options work correctly
- ✓ localStorage mute logic functions properly
- ✓ Permanent mute updates user settings
- ✓ Responsive design works on mobile
- ✓ Accessible with keyboard navigation
- ✓ All component tests pass

## Next Phase

After Phase 3 completion, proceed to **Phase 4: Drag and Drop Implementation** to add the actual drag-and-drop functionality to the page tree.

---

## Progress Tracking

### Feature 1: Component Structure
- [ ] Create MoveConfirmationModal.jsx file
- [ ] Import React and hooks
- [ ] Define component props
- [ ] Add prop types/TypeScript types
- [ ] Create component function
- [ ] Add isOpen guard (return null if closed)
- [ ] Export component

### Feature 2: Component State
- [ ] Add muteOption state (default '0')
- [ ] Add applyMute state (default false)
- [ ] Add loading state (default false)
- [ ] Test state initialization

### Feature 3: Modal Overlay
- [ ] Create modal-overlay div
- [ ] Add onClick handler to close
- [ ] Add z-index for layering
- [ ] Test click-outside to close

### Feature 4: Modal Content
- [ ] Create modal-content div
- [ ] Stop propagation on click
- [ ] Add click-inside behavior
- [ ] Test modal stays open on content click

### Feature 5: Modal Header
- [ ] Add modal-header div
- [ ] Add h2 title "Move Page?"
- [ ] Add close button (×)
- [ ] Wire close button to onClose
- [ ] Add aria-label for accessibility

### Feature 6: Confirmation Message
- [ ] Add confirmation-message paragraph
- [ ] Display page title in bold
- [ ] Handle hasChildren condition
- [ ] Format destination text
- [ ] Handle null parent (root move)
- [ ] Test with various inputs

### Feature 7: Children Warning
- [ ] Add conditional warning div
- [ ] Only show if hasChildren is true
- [ ] Add warning icon SVG
- [ ] Add warning message
- [ ] Style with yellow/warning color
- [ ] Test visibility toggle

### Feature 8: Mute Options Checkbox
- [ ] Add mute-options section
- [ ] Add checkbox label
- [ ] Add checkbox input
- [ ] Wire to applyMute state
- [ ] Add "Don't ask again for:" text
- [ ] Test checkbox toggle

### Feature 9: Mute Duration Dropdown
- [ ] Add conditional dropdown
- [ ] Only show when applyMute is true
- [ ] Add duration options (1, 5, 30, 60, permanent)
- [ ] Wire to muteOption state
- [ ] Style dropdown
- [ ] Test dropdown values

### Feature 10: Modal Footer
- [ ] Add modal-footer div
- [ ] Add Cancel button
- [ ] Wire Cancel to onClose
- [ ] Add Move Page button
- [ ] Wire Move Page to handleConfirm
- [ ] Show loading state on button
- [ ] Disable buttons when loading

### Feature 11: Confirm Logic
- [ ] Implement handleConfirm function
- [ ] Set loading to true
- [ ] Check if mute should be applied
- [ ] Call handleMute if needed
- [ ] Call onConfirm prop
- [ ] Call onClose on success
- [ ] Handle errors
- [ ] Set loading to false in finally

### Feature 12: Mute Logic
- [ ] Implement handleMute function
- [ ] Check if duration is 'permanent'
- [ ] Call onMuteChange for permanent
- [ ] Set localStorage for permanent
- [ ] Calculate expiration for temporary mute
- [ ] Set localStorage with expiration
- [ ] Test with each duration option

### Feature 13: CSS Styling
- [ ] Create MoveConfirmationModal.css file
- [ ] Style modal-overlay
- [ ] Add fade-in animation
- [ ] Style modal-content
- [ ] Add slide-up animation
- [ ] Style modal-header
- [ ] Style close button
- [ ] Style modal-body
- [ ] Style confirmation-message
- [ ] Style warning section
- [ ] Style mute-options
- [ ] Style checkbox and label
- [ ] Style dropdown
- [ ] Style modal-footer
- [ ] Style buttons
- [ ] Add hover effects

### Feature 14: Dark Mode Support
- [ ] Use CSS variables for colors
- [ ] Test in light mode
- [ ] Test in dark mode
- [ ] Adjust contrast if needed
- [ ] Verify warning colors work

### Feature 15: Responsive Design
- [ ] Test on mobile (320px)
- [ ] Test on tablet (768px)
- [ ] Test on desktop (1920px)
- [ ] Add mobile-specific styles
- [ ] Stack footer buttons on mobile
- [ ] Adjust padding for small screens
- [ ] Test touch interactions

### Feature 16: Accessibility
- [ ] Add proper ARIA labels
- [ ] Test keyboard navigation
- [ ] Test Tab key navigation
- [ ] Test Enter key to confirm
- [ ] Test Escape key to close
- [ ] Test with screen reader
- [ ] Verify color contrast
- [ ] Add focus indicators

### Feature 17: muteHelper Utility
- [ ] Create utils/muteHelper.js file
- [ ] Implement shouldShowMoveConfirmation
- [ ] Check userSettings from localStorage
- [ ] Check moveMuteUntil from localStorage
- [ ] Handle permanent mute
- [ ] Handle temporary mute expiration
- [ ] Implement setTemporaryMute
- [ ] Implement setPermanentMute
- [ ] Implement clearMute
- [ ] Implement getMuteTimeRemaining
- [ ] Export all functions

### Feature 18: Component Testing
- [ ] Set up testing environment
- [ ] Write test: renders when open
- [ ] Write test: doesn't render when closed
- [ ] Write test: displays correct message
- [ ] Write test: shows children warning
- [ ] Write test: shows mute dropdown
- [ ] Write test: calls onConfirm
- [ ] Write test: calls onClose
- [ ] Write test: calls onMuteChange
- [ ] Run all component tests
- [ ] Verify test coverage >80%

### Feature 19: Utility Testing
- [ ] Write test: shouldShowMoveConfirmation default
- [ ] Write test: permanent mute behavior
- [ ] Write test: temporary mute behavior
- [ ] Write test: expired mute behavior
- [ ] Write test: getMuteTimeRemaining
- [ ] Write test: clearMute
- [ ] Run utility tests
- [ ] Verify test coverage

### Feature 20: Integration Testing
- [ ] Test modal with parent component
- [ ] Test mute flow end-to-end
- [ ] Test permanent disable flow
- [ ] Test temporary mute expiration
- [ ] Test with actual API calls
- [ ] Test error scenarios
- [ ] Verify localStorage persistence
