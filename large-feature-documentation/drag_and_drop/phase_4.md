# Phase 4: Drag and Drop Implementation (Day 2-3)

## Overview

**Priority: HIGH - Core drag-and-drop functionality**

This phase implements the actual drag-and-drop functionality in the page tree, integrating with the confirmation modal and API. This is the core feature that enables users to visually reorganize their wiki structure.

## Goals

- Add HTML5 drag-and-drop handlers to PageTree component
- Implement visual feedback during drag operations
- Integrate confirmation modal with drag-drop flow
- Connect to API for parent change
- Add page tree refresh after successful move
- Handle all edge cases (self-drop, circular references, etc.)
- Implement root-level drop zone

## Timeline

**Duration:** 1.5 days (Days 2-3 of implementation)

### Day 2 Afternoon: Basic Drag Handlers
- Add drag event handlers
- Implement visual feedback
- Test drag states

### Day 3 Morning: Drop Logic
- Implement drop handling
- Integrate confirmation modal
- Connect to API

### Day 3 Afternoon: Polish & Edge Cases
- Add root drop zone
- Handle edge cases
- Refine UX

## Technical Implementation

### PageTree Component Updates

```jsx
// frontend/src/components/PageTree.jsx

import React, { useState } from 'react';
import { usePageOperations } from '../hooks/usePageOperations';
import { shouldShowMoveConfirmation } from '../utils/muteHelper';
import { MoveConfirmationModal } from './MoveConfirmationModal';
import { showSuccess, showError } from '../utils/toast';
import './PageTree.css';

export const PageTree = ({ wikiId, pages, onRefresh }) => {
  const [moveConfirmation, setMoveConfirmation] = useState(null);
  const { changeParent, loading } = usePageOperations(wikiId, onRefresh);
  
  const handleMoveRequest = async (dragData, targetPage) => {
    // Prevent dropping on self
    if (dragData.pageId === targetPage?.id) {
      return;
    }
    
    // Check if confirmation should be shown
    if (shouldShowMoveConfirmation()) {
      setMoveConfirmation({
        pageId: dragData.pageId,
        pageTitle: dragData.pageTitle,
        newParentId: targetPage?.id || null,
        newParentTitle: targetPage?.title || null,
        hasChildren: dragData.hasChildren
      });
    } else {
      // Skip confirmation, move directly
      await executeMove(dragData.pageId, targetPage?.id || null);
    }
  };
  
  const executeMove = async (pageId, newParentId) => {
    try {
      await changeParent(pageId, newParentId);
      showSuccess('Page moved successfully');
      await onRefresh(); // Refresh page tree
    } catch (error) {
      showError(error.message || 'Failed to move page');
    } finally {
      setMoveConfirmation(null);
    }
  };
  
  return (
    <div className="page-tree">
      <RootDropZone onDrop={(dragData) => handleMoveRequest(dragData, null)} />
      
      {pages.map(page => (
        <PageTreeItem
          key={page.id}
          page={page}
          onMoveRequest={handleMoveRequest}
          loading={loading}
        />
      ))}
      
      {moveConfirmation && (
        <MoveConfirmationModal
          isOpen={true}
          onClose={() => setMoveConfirmation(null)}
          onConfirm={() => executeMove(
            moveConfirmation.pageId,
            moveConfirmation.newParentId
          )}
          pageTitle={moveConfirmation.pageTitle}
          newParentTitle={moveConfirmation.newParentTitle}
          hasChildren={moveConfirmation.hasChildren}
          onMuteChange={handleMuteChange}
        />
      )}
    </div>
  );
};
```

### PageTreeItem Component

```jsx
// frontend/src/components/PageTreeItem.jsx

import React, { useState } from 'react';

export const PageTreeItem = ({ page, onMoveRequest, loading }) => {
  const [dragOver, setDragOver] = useState(false);
  const [dragging, setDragging] = useState(false);
  
  const handleDragStart = (e) => {
    setDragging(true);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('application/json', JSON.stringify({
      pageId: page.id,
      pageTitle: page.title,
      hasChildren: page.children && page.children.length > 0
    }));
    
    // Optional: Set custom drag image
    if (e.dataTransfer.setDragImage) {
      const dragImage = createDragImage(page.title);
      e.dataTransfer.setDragImage(dragImage, 0, 0);
    }
  };
  
  const handleDragEnd = (e) => {
    setDragging(false);
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = 'move';
    setDragOver(true);
  };
  
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };
  
  const handleDragLeave = (e) => {
    e.stopPropagation();
    // Only clear if leaving the element itself, not children
    if (e.currentTarget === e.target) {
      setDragOver(false);
    }
  };
  
  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    
    try {
      const data = JSON.parse(e.dataTransfer.getData('application/json'));
      
      // Prevent dropping on self
      if (data.pageId === page.id) {
        return;
      }
      
      // Trigger move request
      await onMoveRequest(data, page);
    } catch (error) {
      console.error('Drop handling error:', error);
    }
  };
  
  return (
    <li
      className={`page-tree-item ${dragOver ? 'drag-over' : ''} ${dragging ? 'dragging' : ''}`}
      draggable={!loading}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="page-item-content">
        <span className="page-icon">📄</span>
        <span className="page-title">{page.title}</span>
      </div>
      
      {page.children && page.children.length > 0 && (
        <ul className="page-tree-children">
          {page.children.map(child => (
            <PageTreeItem
              key={child.id}
              page={child}
              onMoveRequest={onMoveRequest}
              loading={loading}
            />
          ))}
        </ul>
      )}
    </li>
  );
};

// Helper function to create custom drag image
const createDragImage = (title) => {
  const dragImage = document.createElement('div');
  dragImage.className = 'drag-image';
  dragImage.textContent = `📄 ${title}`;
  dragImage.style.position = 'absolute';
  dragImage.style.top = '-1000px';
  dragImage.style.padding = '8px 12px';
  dragImage.style.background = 'var(--primary)';
  dragImage.style.color = 'white';
  dragImage.style.borderRadius = '4px';
  dragImage.style.fontSize = '14px';
  dragImage.style.maxWidth = '200px';
  dragImage.style.overflow = 'hidden';
  dragImage.style.textOverflow = 'ellipsis';
  dragImage.style.whiteSpace = 'nowrap';
  document.body.appendChild(dragImage);
  
  // Clean up after drag
  setTimeout(() => {
    document.body.removeChild(dragImage);
  }, 0);
  
  return dragImage;
};
```

### RootDropZone Component

```jsx
// frontend/src/components/RootDropZone.jsx

import React, { useState } from 'react';

export const RootDropZone = ({ onDrop }) => {
  const [dragOver, setDragOver] = useState(false);
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOver(true);
  };
  
  const handleDragLeave = (e) => {
    setDragOver(false);
  };
  
  const handleDrop = async (e) => {
    e.preventDefault();
    setDragOver(false);
    
    try {
      const data = JSON.parse(e.dataTransfer.getData('application/json'));
      await onDrop(data);
    } catch (error) {
      console.error('Root drop error:', error);
    }
  };
  
  return (
    <div
      className={`drop-zone root-drop-zone ${dragOver ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {dragOver ? 'Drop here to move to root level' : 'Drop pages here to move to root'}
    </div>
  );
};
```

### Drag and Drop Styles

```css
/* frontend/src/components/PageTree.css */

.page-tree {
  list-style: none;
  padding: 0;
  margin: 0;
}

.page-tree-item {
  padding: 8px;
  margin: 4px 0;
  border-radius: 4px;
  transition: all 0.2s ease;
  cursor: grab;
  user-select: none;
}

.page-tree-item:active {
  cursor: grabbing;
}

.page-tree-item.dragging {
  opacity: 0.4;
  transform: scale(0.95);
}

.page-tree-item.drag-over {
  background-color: var(--primary-lighter, rgba(59, 130, 246, 0.1));
  border-left: 3px solid var(--primary, #3b82f6);
  padding-left: 13px; /* 8px + 3px border + 2px adjustment */
}

.page-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
}

.page-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.page-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.page-tree-children {
  list-style: none;
  padding-left: 20px;
  margin: 4px 0 0 0;
}

/* Root drop zone */
.drop-zone {
  min-height: 50px;
  border: 2px dashed var(--border, #e5e7eb);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, #6b7280);
  margin: 8px 0;
  padding: 12px;
  transition: all 0.2s ease;
  font-size: 14px;
}

.drop-zone.drag-over {
  border-color: var(--primary, #3b82f6);
  background-color: var(--primary-lighter, rgba(59, 130, 246, 0.05));
  color: var(--primary, #3b82f6);
  border-width: 3px;
}

/* Drag image */
.drag-image {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Loading state */
.page-tree-item[draggable="false"] {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Hover effect when not dragging */
.page-tree-item:hover:not(.dragging) {
  background-color: var(--hover-bg, rgba(0, 0, 0, 0.05));
}

/* Focus state for accessibility */
.page-tree-item:focus {
  outline: 2px solid var(--primary, #3b82f6);
  outline-offset: 2px;
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .page-tree-item:hover:not(.dragging) {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  .drop-zone {
    border-color: #4b5563;
  }
}
```

## Edge Cases & Handling

### 1. Self-Drop Prevention
```javascript
// Already handled in handleDrop
if (data.pageId === page.id) {
  return; // Silently ignore
}
```

### 2. Circular Reference
```javascript
// Handled by backend API
// Frontend shows error from API response
```

### 3. Drag Leave on Child Elements
```javascript
// Use currentTarget === target check
if (e.currentTarget === e.target) {
  setDragOver(false);
}
```

### 4. Multiple Simultaneous Drags
```javascript
// HTML5 DnD only allows one drag at a time
// No special handling needed
```

### 5. Drag Outside Window
```javascript
// handleDragEnd always fires
// Cleanup in dragEnd handler
```

## Testing Requirements

### Component Tests

```javascript
// tests/components/PageTreeItem.test.jsx

describe('PageTreeItem drag and drop', () => {
  test('draggable attribute set correctly', () => {
    // Verify draggable when not loading
    // Verify not draggable when loading
  });
  
  test('drag start sets data transfer', () => {
    // Mock DataTransfer
    // Trigger dragStart
    // Verify setData called with correct JSON
  });
  
  test('drag over adds drag-over class', () => {
    // Trigger dragOver
    // Verify className includes 'drag-over'
  });
  
  test('drop calls onMoveRequest', async () => {
    // Mock drop event
    // Verify onMoveRequest called
  });
  
  test('self-drop is prevented', () => {
    // Drop page on itself
    // Verify onMoveRequest not called
  });
});
```

### Integration Tests

```javascript
// tests/integration/dragAndDrop.test.jsx

describe('Drag and drop integration', () => {
  test('complete drag and drop flow', async () => {
    // Render PageTree
    // Drag page A
    // Drop on page B
    // Verify confirmation modal appears
    // Click confirm
    // Verify API called
    // Verify tree refreshed
  });
  
  test('drag to root level', async () => {
    // Drag page
    // Drop on root zone
    // Verify new_parent_id is null
  });
  
  test('skips confirmation when muted', async () => {
    // Set mute in localStorage
    // Drag and drop
    // Verify no modal shown
    // Verify API called directly
  });
});
```

### Manual Testing Checklist

- [ ] Drag page and see visual feedback
- [ ] Drop page on another page
- [ ] Confirmation modal appears
- [ ] Move is executed after confirmation
- [ ] Tree refreshes showing new structure
- [ ] Drag page to root drop zone
- [ ] Page moves to root level
- [ ] Try to drop page on itself (should be prevented)
- [ ] Try to move parent into its child (API should reject)
- [ ] Drag with temporary mute active (no confirmation)
- [ ] Drag with permanent disable (no confirmation)
- [ ] Test in different browsers
- [ ] Test with nested page hierarchies

## Success Criteria

- ✓ Pages are draggable
- ✓ Visual feedback during drag is clear
- ✓ Drop targets highlight appropriately
- ✓ Confirmation modal integrates smoothly
- ✓ API calls execute correctly
- ✓ Page tree refreshes after move
- ✓ Edge cases handled properly
- ✓ Root drop zone works
- ✓ Performance is smooth with large trees
- ✓ All tests pass

## Next Phase

After Phase 4 completion, proceed to **Phase 5: User Settings Integration** to add the permanent disable option in user settings.

---

## Progress Tracking

### Feature 1: PageTree Component Setup
- [ ] Open PageTree.jsx file
- [ ] Import required hooks and components
- [ ] Import MoveConfirmationModal
- [ ] Import usePageOperations hook
- [ ] Import shouldShowMoveConfirmation
- [ ] Import toast utilities
- [ ] Add moveConfirmation state
- [ ] Get changeParent and loading from hook

### Feature 2: Move Request Handler
- [ ] Implement handleMoveRequest function
- [ ] Add self-drop prevention check
- [ ] Call shouldShowMoveConfirmation
- [ ] Set moveConfirmation state if showing
- [ ] Call executeMove directly if not showing
- [ ] Test with and without confirmation

### Feature 3: Execute Move Function
- [ ] Implement executeMove function
- [ ] Call changeParent API
- [ ] Show success toast on completion
- [ ] Call onRefresh to update tree
- [ ] Show error toast on failure
- [ ] Clear moveConfirmation state
- [ ] Test error handling

### Feature 4: RootDropZone Component
- [ ] Create RootDropZone.jsx file
- [ ] Add dragOver state
- [ ] Implement handleDragOver
- [ ] Implement handleDragLeave
- [ ] Implement handleDrop
- [ ] Parse drag data
- [ ] Call onDrop prop
- [ ] Add visual feedback
- [ ] Test root zone drops

### Feature 5: PageTreeItem Drag Start
- [ ] Create PageTreeItem.jsx file
- [ ] Add dragging state
- [ ] Add dragOver state
- [ ] Implement handleDragStart
- [ ] Set effectAllowed to 'move'
- [ ] Set drag data (pageId, title, hasChildren)
- [ ] Set dragging state to true
- [ ] Add custom drag image (optional)
- [ ] Test drag start

### Feature 6: PageTreeItem Drag End
- [ ] Implement handleDragEnd
- [ ] Set dragging state to false
- [ ] Clean up any drag artifacts
- [ ] Test drag end fires

### Feature 7: PageTreeItem Drag Over
- [ ] Implement handleDragOver
- [ ] Prevent default behavior
- [ ] Stop propagation
- [ ] Set dropEffect to 'move'
- [ ] Set dragOver state to true
- [ ] Test drag over highlighting

### Feature 8: PageTreeItem Drag Enter
- [ ] Implement handleDragEnter
- [ ] Prevent default
- [ ] Stop propagation
- [ ] Set dragOver to true
- [ ] Test drag enter

### Feature 9: PageTreeItem Drag Leave
- [ ] Implement handleDragLeave
- [ ] Stop propagation
- [ ] Check currentTarget === target
- [ ] Set dragOver to false only for self
- [ ] Test drag leave (avoid flickering on children)

### Feature 10: PageTreeItem Drop Handler
- [ ] Implement handleDrop
- [ ] Prevent default
- [ ] Stop propagation
- [ ] Set dragOver to false
- [ ] Parse drag data from dataTransfer
- [ ] Prevent self-drop
- [ ] Call onMoveRequest
- [ ] Handle errors
- [ ] Test drop handling

### Feature 11: Custom Drag Image
- [ ] Implement createDragImage function
- [ ] Create DOM element for drag image
- [ ] Style drag image
- [ ] Add page icon and truncated title
- [ ] Position off-screen
- [ ] Use setDragImage API
- [ ] Clean up element after drag
- [ ] Test custom drag image

### Feature 12: Draggable Attribute
- [ ] Set draggable based on loading state
- [ ] draggable={!loading}
- [ ] Test dragging disabled when loading
- [ ] Test dragging enabled when not loading

### Feature 13: CSS Styling - Drag States
- [ ] Create/update PageTree.css
- [ ] Style .page-tree-item
- [ ] Add cursor: grab
- [ ] Style .page-tree-item:active (grabbing)
- [ ] Style .dragging class (opacity, scale)
- [ ] Style .drag-over class (background, border)
- [ ] Add transition animations
- [ ] Test visual feedback

### Feature 14: CSS Styling - Drop Zone
- [ ] Style .drop-zone
- [ ] Add dashed border
- [ ] Center content
- [ ] Style .drag-over state
- [ ] Change border color on drag over
- [ ] Add background color
- [ ] Add padding and min-height
- [ ] Test drop zone appearance

### Feature 15: CSS Styling - Tree Structure
- [ ] Style .page-item-content
- [ ] Style .page-icon
- [ ] Style .page-title with ellipsis
- [ ] Style .page-tree-children
- [ ] Add proper indentation
- [ ] Add hover effects
- [ ] Add focus styles
- [ ] Test nested appearance

### Feature 16: Confirmation Modal Integration
- [ ] Render MoveConfirmationModal conditionally
- [ ] Pass moveConfirmation data as props
- [ ] Wire onClose to clear state
- [ ] Wire onConfirm to executeMove
- [ ] Pass onMuteChange handler
- [ ] Test modal appears on drop
- [ ] Test modal closes after action

### Feature 17: Error Handling
- [ ] Wrap API calls in try-catch
- [ ] Show error toast on failure
- [ ] Log errors to console
- [ ] Clear loading state on error
- [ ] Provide user-friendly messages
- [ ] Test with network disconnected
- [ ] Test with API errors

### Feature 18: Page Tree Refresh
- [ ] Call onRefresh after successful move
- [ ] Ensure new structure displayed
- [ ] Test tree updates correctly
- [ ] Handle refresh errors
- [ ] Add loading indicator during refresh

### Feature 19: Self-Drop Prevention
- [ ] Check pageId === targetPageId
- [ ] Return early if same
- [ ] Add visual indication (optional)
- [ ] Test dropping page on itself
- [ ] Verify no API call made

### Feature 20: Component Tests
- [ ] Write test: draggable attribute
- [ ] Write test: drag start sets data
- [ ] Write test: drag over adds class
- [ ] Write test: drag leave removes class
- [ ] Write test: drop calls onMoveRequest
- [ ] Write test: self-drop prevented
- [ ] Write test: custom drag image created
- [ ] Run all component tests

### Feature 21: Integration Tests
- [ ] Write test: complete drag and drop flow
- [ ] Write test: confirmation modal flow
- [ ] Write test: muted confirmation skipped
- [ ] Write test: drag to root level
- [ ] Write test: API error handling
- [ ] Write test: tree refresh after move
- [ ] Run integration tests

### Feature 22: Manual Testing
- [ ] Test drag and drop in Chrome
- [ ] Test drag and drop in Firefox
- [ ] Test drag and drop in Safari
- [ ] Test drag and drop in Edge
- [ ] Test with large page tree (100+ pages)
- [ ] Test with deeply nested pages (5+ levels)
- [ ] Test with slow network
- [ ] Test all edge cases
- [ ] Verify performance is smooth

### Feature 23: Accessibility
- [ ] Test keyboard navigation
- [ ] Add ARIA labels for drag/drop
- [ ] Test with screen reader
- [ ] Ensure focus indicators visible
- [ ] Test Tab key navigation
- [ ] Document accessibility features

### Feature 24: Performance Optimization
- [ ] Profile drag operations
- [ ] Optimize re-renders
- [ ] Use React.memo if needed
- [ ] Debounce drag events if needed
- [ ] Test with 500+ pages
- [ ] Monitor memory usage

### Feature 25: Documentation
- [ ] Document drag and drop feature
- [ ] Add code comments
- [ ] Document component props
- [ ] Create user guide
- [ ] Add troubleshooting section
- [ ] Document browser compatibility
