# Drag and Drop Parent Change Feature - Implementation Plan

## Overview
This feature allows users to change a page's parent by dragging and dropping it onto a new parent page in the UI. It includes a confirmation dialog with temporary muting options to prevent accidental changes while maintaining usability for power users.

## Requirements Summary
1. Enable drag-and-drop for pages in the page tree to change parent
2. Show confirmation dialog before making the change
3. Provide option to mute confirmation for 1, 5, 30, or 60 minutes, or permanently
4. Preserve existing child structure when moving parent pages
5. Add user settings to re-enable/disable confirmation prompts
6. Update `parent_id` of the moved page via API

---

## Architecture Components

### Frontend Components
- **PageTree.jsx** - Main tree navigation component (requires drag-and-drop implementation)
- **MoveConfirmationModal** - New confirmation dialog component
- **UserSettings.jsx** - Existing settings page (add move confirmation toggle)

### Backend Components
- **Page Model** (`app/models/models.py`) - Already has `parent_id` field and `move_to_parent()` method
- **Pages Routes** (`app/routes/pages.py`) - Needs new endpoint for parent change
- **User Model** (`app/models/models.py`) - Needs user preferences/settings field

### API Service
- **api.js** - Add new `movePageParent()` API method

---

## Detailed Implementation Plan

### Phase 1: Backend API Foundation

#### 1.1 Add User Settings/Preferences to User Model
**File:** `app/models/models.py`

**Changes:**
- Add `settings` field to User model as JSON column to store user preferences
  ```python
  settings = db.Column(db.JSON, default=lambda: {})
  ```
- Update `to_dict()` method to include settings when needed
- Default settings structure:
  ```json
  {
    "disable_move_confirmation": false
  }
  ```

**Migration needed:** Yes - add settings column to users table

#### 1.2 Create Parent Change API Endpoint
**File:** `app/routes/pages.py`

**New endpoint:** `POST /api/wikis/<wiki_id>/pages/<page_id>/change-parent`

**Request body:**
```json
{
  "new_parent_id": int | null  // null for moving to root
}
```

**Response:**
```json
{
  "success": true,
  "page": { /* updated page object */ }
}
```

**Implementation logic:**
1. Verify user has edit permissions on wiki
2. Verify page exists and belongs to wiki
3. If `new_parent_id` provided:
   - Verify new parent exists in same wiki
   - Use existing `page.move_to_parent()` method (already prevents circular references)
4. Update page's `parent_id`
5. Commit transaction
6. Return updated page data

**Error cases:**
- 404: Page not found, wiki not found, new parent not found
- 403: User lacks edit permission
- 400: Circular reference detected (handled by `move_to_parent()`)

#### 1.3 Update User Settings Endpoint
**File:** `app/routes/auth.py`

**Modify existing:** `PATCH /api/auth/me`

**Accept additional fields:**
```json
{
  "settings": {
    "disable_move_confirmation": boolean
  }
}
```

**Implementation:**
- Update user.settings JSON field (merge with existing settings)
- Return updated user object with settings

---

### Phase 2: Frontend API Integration

#### 2.1 Add API Service Method
**File:** `frontend/src/services/api.js`

**Add to `pagesAPI` object:**
```javascript
changeParent: (wikiId, pageId, newParentId) => 
  api.post(`/wikis/${wikiId}/pages/${pageId}/change-parent`, { 
    new_parent_id: newParentId 
  })
```

#### 2.2 Update Auth API for Settings
**File:** `frontend/src/services/api.js`

**Existing `authAPI.updateMe()` should already handle settings** - verify it accepts arbitrary fields

---

### Phase 3: Confirmation Dialog Component

#### 3.1 Create MoveConfirmationModal Component
**File:** `frontend/src/components/MoveConfirmationModal.jsx`

**Props:**
```javascript
{
  isOpen: boolean,
  onClose: () => void,
  onConfirm: () => void,
  pageTitle: string,
  newParentTitle: string | null,  // null means moving to root
  hasChildren: boolean
}
```

**State:**
```javascript
{
  muteOption: string,  // '0', '1', '5', '30', '60', 'permanent'
  loading: boolean
}
```

**UI Elements:**
1. **Header:** "Move Page?"
2. **Content:**
   - Message: "Are you sure you want to move **{pageTitle}** {hasChildren ? "and its children " : ""}to {newParentTitle || "root level"}?"
   - If hasChildren: Additional warning about child structure being preserved
3. **Mute Options:**
   - Checkbox: "Don't ask again for:"
   - Dropdown: 1 minute, 5 minutes, 30 minutes, 60 minutes, Permanently
4. **Actions:**
   - Cancel button
   - Confirm button (primary)

**Mute Logic:**
- Store mute preference in localStorage
  ```javascript
  {
    "moveMuteUntil": timestamp | "permanent",
    "disableMoveConfirmation": boolean
  }
  ```
- If "Permanently" selected:
  - Update user settings via API
  - Set localStorage flag for immediate feedback
- For time-based muting:
  - Store expiration timestamp in localStorage
  - Check on every move attempt

**Styling:**
- Reuse existing Modal component
- Add custom footer with mute checkbox and dropdown
- Style based on existing modal patterns in the app

---

### Phase 4: Drag and Drop Implementation

#### 4.1 Add Drag and Drop to PageTree Component
**File:** `frontend/src/components/PageTree.jsx`

**Dependencies:** HTML5 Drag and Drop API (no external library needed)

**Changes to PageTreeItem:**

**State:**
```javascript
const [dragOver, setDragOver] = useState(false);
```

**Drag handlers:**
```javascript
const handleDragStart = (e) => {
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('application/json', JSON.stringify({
    pageId: page.id,
    pageTitle: page.title,
    hasChildren: page.children?.length > 0
  }));
};

const handleDragOver = (e) => {
  e.preventDefault();
  e.stopPropagation();
  e.dataTransfer.dropEffect = 'move';
  setDragOver(true);
};

const handleDragLeave = (e) => {
  e.stopPropagation();
  setDragOver(false);
};

const handleDrop = async (e) => {
  e.preventDefault();
  e.stopPropagation();
  setDragOver(false);
  
  const data = JSON.parse(e.dataTransfer.getData('application/json'));
  
  // Prevent dropping on self
  if (data.pageId === page.id) return;
  
  // Trigger move with confirmation
  await handleMoveRequest(data.pageId, data.pageTitle, page.id, page.title, data.hasChildren);
};
```

**JSX attributes:**
```jsx
<li 
  className={`page-tree-item ${dragOver ? 'drag-over' : ''}`}
  draggable={true}
  onDragStart={handleDragStart}
  onDragOver={handleDragOver}
  onDragLeave={handleDragLeave}
  onDrop={handleDrop}
>
```

**Drop on root level:**
- Add drop zone to top-level `PageTree` component
- Allow dropping to change parent to null (root)

#### 4.2 Implement Move Logic with Confirmation
**File:** `frontend/src/components/PageTree.jsx`

**Add to PageTree component:**

**State:**
```javascript
const [moveConfirmation, setMoveConfirmation] = useState(null);
const [moving, setMoving] = useState(false);
```

**Check if confirmation is muted:**
```javascript
const shouldShowConfirmation = () => {
  // Check localStorage for user preference
  const settings = JSON.parse(localStorage.getItem('userSettings') || '{}');
  if (settings.disableMoveConfirmation) return false;
  
  const muteUntil = localStorage.getItem('moveMuteUntil');
  if (muteUntil === 'permanent') return false;
  if (muteUntil && new Date(muteUntil) > new Date()) return false;
  
  return true;
};
```

**Handle move request:**
```javascript
const handleMoveRequest = async (pageId, pageTitle, newParentId, newParentTitle, hasChildren) => {
  if (shouldShowConfirmation()) {
    setMoveConfirmation({
      pageId,
      pageTitle,
      newParentId,
      newParentTitle,
      hasChildren
    });
  } else {
    await executeMove(pageId, newParentId);
  }
};

const executeMove = async (pageId, newParentId) => {
  setMoving(true);
  try {
    await pagesAPI.changeParent(wikiId, pageId, newParentId);
    // Refresh page tree
    await onRefresh();
    // Show success toast/message
  } catch (error) {
    console.error('Failed to move page:', error);
    // Show error toast/message
  } finally {
    setMoving(false);
    setMoveConfirmation(null);
  }
};
```

**Render confirmation modal:**
```jsx
{moveConfirmation && (
  <MoveConfirmationModal
    isOpen={true}
    onClose={() => setMoveConfirmation(null)}
    onConfirm={() => executeMove(moveConfirmation.pageId, moveConfirmation.newParentId)}
    pageTitle={moveConfirmation.pageTitle}
    newParentTitle={moveConfirmation.newParentTitle}
    hasChildren={moveConfirmation.hasChildren}
  />
)}
```

---

### Phase 5: User Settings Integration

#### 5.1 Add Setting to UserSettings Page
**File:** `frontend/src/pages/UserSettings.jsx`

**Location:** Add new section after profile settings

**UI:**
```jsx
<section className="card settings-section">
  <h3 className="section-title">Page Management Preferences</h3>
  
  <div className="form-group">
    <label className="checkbox-label">
      <input
        type="checkbox"
        checked={settings.disableMoveConfirmation || false}
        onChange={(e) => handleSettingToggle('disableMoveConfirmation', e.target.checked)}
      />
      <span>Disable confirmation when moving pages (drag & drop)</span>
    </label>
    <p className="help-text">
      When enabled, pages can be moved by dragging and dropping without confirmation prompts
    </p>
  </div>
</section>
```

**State management:**
```javascript
const [settings, setSettings] = useState({
  disableMoveConfirmation: false
});

useEffect(() => {
  // Load from user object
  if (user?.settings) {
    setSettings(user.settings);
  }
}, [user]);

const handleSettingToggle = async (key, value) => {
  const newSettings = { ...settings, [key]: value };
  setSettings(newSettings);
  
  try {
    await authAPI.updateMe({ settings: newSettings });
    // Update localStorage for immediate effect
    const localSettings = JSON.parse(localStorage.getItem('userSettings') || '{}');
    localSettings[key] = value;
    localStorage.setItem('userSettings', JSON.stringify(localSettings));
    
    await refreshUser();
    setSuccess('Settings updated');
  } catch (error) {
    console.error('Failed to update settings:', error);
    setError('Failed to update settings');
    setSettings(settings); // Revert
  }
};
```

#### 5.2 Sync Settings on Auth
**File:** `frontend/src/context/AuthContext.jsx` (if exists) or appropriate auth handler

**On login/token refresh:**
```javascript
// Store user settings in localStorage for quick access
if (user?.settings) {
  localStorage.setItem('userSettings', JSON.stringify(user.settings));
}
```

---

### Phase 6: Styling

#### 6.1 Add Drag and Drop Styles
**File:** `frontend/src/styles/index.css`

**Add styles:**
```css
/* Drag and Drop Styles */
.page-tree-item {
  transition: background-color 0.2s ease;
  cursor: grab;
}

.page-tree-item:active {
  cursor: grabbing;
}

.page-tree-item.drag-over {
  background-color: var(--primary-lighter);
  border-left: 3px solid var(--primary);
}

.page-tree-item.dragging {
  opacity: 0.5;
}

/* Drop zone indicator */
.drop-zone {
  min-height: 40px;
  border: 2px dashed var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  margin: 8px;
  transition: all 0.2s ease;
}

.drop-zone.drag-over {
  border-color: var(--primary);
  background-color: var(--primary-lighter);
  color: var(--primary);
}

/* Confirmation Modal Specific Styles */
.move-confirmation-content {
  padding: 16px 0;
}

.move-confirmation-warning {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 12px;
  background-color: var(--warning);
  background-color: color-mix(in srgb, var(--warning) 10%, transparent);
  border-radius: 6px;
  margin-bottom: 16px;
}

.mute-options {
  border-top: 1px solid var(--border);
  padding-top: 16px;
  margin-top: 16px;
}

.mute-options-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mute-dropdown {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  min-width: 150px;
}
```

---

## Database Migration

### Migration Script
**File:** `migrations/versions/XXXX_add_user_settings.py`

```python
"""Add settings column to users table

Revision ID: XXXX
Revises: YYYY
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXXX'
down_revision = 'YYYY'  # Previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Add settings column with default empty JSON object
    op.add_column('users', sa.Column('settings', postgresql.JSON, server_default='{}', nullable=True))


def downgrade():
    op.drop_column('users', 'settings')
```

---

## Implementation Order

### Step 1: Backend Foundation (Day 1)
1. Create database migration for user settings
2. Run migration
3. Update User model with settings field
4. Create new `/change-parent` endpoint in pages routes
5. Update auth routes to accept settings in PATCH /me
6. Test endpoints with curl/Postman

### Step 2: API Integration (Day 1)
1. Add `changeParent` method to pagesAPI in api.js
2. Verify auth API already handles settings updates

### Step 3: Confirmation Modal (Day 2)
1. Create MoveConfirmationModal.jsx component
2. Implement UI with mute options
3. Add localStorage logic for temporary muting
4. Test modal in isolation

### Step 4: Drag and Drop (Day 2-3)
1. Add drag handlers to PageTreeItem
2. Add visual feedback for drag states
3. Implement drop handling logic
4. Add confirmation check before move
5. Integrate API call to change parent
6. Add page tree refresh after successful move
7. Handle errors with user feedback

### Step 5: User Settings (Day 3)
1. Add settings section to UserSettings page
2. Add checkbox for disabling move confirmation
3. Wire up to API
4. Sync settings with localStorage on auth

### Step 6: Styling (Day 3)
1. Add CSS for drag-and-drop states
2. Add CSS for confirmation modal
3. Test in light and dark themes
4. Responsive testing

### Step 7: Testing & Polish (Day 4)
1. Test moving pages with no children
2. Test moving pages with children (verify structure preserved)
3. Test moving to root level
4. Test circular reference prevention
5. Test all mute durations
6. Test permanent disable/re-enable flow
7. Test error cases (network failures, permission issues)
8. Test across browsers (Chrome, Firefox, Safari)
9. Performance testing with large page trees

---

## Edge Cases & Considerations

### 1. Circular Reference Prevention
- **Handled by:** Existing `Page.move_to_parent()` method already prevents this
- **Test:** Try to move a parent page into one of its descendants

### 2. Permission Validation
- **Backend:** Verify user has edit permission on wiki
- **Frontend:** Only enable drag for wikis where user can edit
- **Test:** Try to move page in wiki where user is viewer

### 3. Concurrent Moves
- **Scenario:** Two users move pages simultaneously
- **Solution:** Database transaction isolation handles this
- **Frontend:** Show error and refresh tree if conflict detected

### 4. Page Tree Refresh
- **After successful move:** Refetch entire page tree to show updated structure
- **Consider:** Optimistic UI update before API call completes

### 5. Move to Same Parent
- **Scenario:** User drops page on its current parent
- **Solution:** Detect in frontend and skip API call

### 6. Drag Across Different Wikis
- **Prevention:** Only allow drops within same wiki context
- **Implementation:** Store wikiId in drag data and verify on drop

### 7. Long Page Titles
- **Confirmation modal:** Truncate titles if too long
- **Drag ghost:** Consider custom drag image with truncated text

### 8. Mobile/Touch Support
- **Note:** HTML5 drag-and-drop doesn't work well on touch devices
- **Alternative:** Consider adding a "Move" button in page actions menu for mobile
- **Future enhancement:** Implement touch-friendly drag library (react-beautiful-dnd, dnd-kit)

### 9. Slow Network
- **Loading states:** Show loading indicator during move operation
- **Timeout handling:** Set reasonable timeout for API calls
- **User feedback:** Clear success/error messages

### 10. Mute Expiration
- **Check on every mount:** Verify mute timestamp hasn't expired
- **Clear expired mutes:** Clean up localStorage periodically

---

## Testing Checklist

### Backend API Tests
- [ ] Create migration and run successfully
- [ ] User settings field saves and retrieves correctly
- [ ] Change parent endpoint moves page successfully
- [ ] Change parent to null moves to root
- [ ] Circular reference is prevented
- [ ] Permission validation works
- [ ] Invalid parent ID returns 404
- [ ] Child structure preserved when moving parent page

### Frontend Unit Tests (Optional - not required per user)
- [ ] MoveConfirmationModal renders correctly
- [ ] Mute options work as expected
- [ ] Drag handlers fire appropriately
- [ ] Drop zones highlight on drag over

### Integration Tests / UAT
- [ ] Drag page and drop on new parent
- [ ] Confirmation modal appears
- [ ] Select "1 minute" mute and confirm - verify no prompt for 1 minute
- [ ] Select "permanent" mute - verify settings updated in DB
- [ ] Disable permanent mute in settings - verify confirmation returns
- [ ] Move page with children - verify children move with it
- [ ] Move page to root level
- [ ] Try to move page to its own child - verify prevention
- [ ] Test in viewer role - verify drag disabled
- [ ] Test error handling (disconnect network and try move)

---

## Future Enhancements (Out of Scope)

1. **Undo/Redo:** Allow users to undo recent moves
2. **Bulk Move:** Select multiple pages and move together
3. **Keyboard Shortcuts:** Move pages with keyboard
4. **Touch Support:** Better mobile drag-and-drop experience
5. **Drag Preview:** Custom drag ghost with page icon and title
6. **Move History:** Track page movement history for auditing
7. **Move Restrictions:** Allow wiki admins to lock certain pages from being moved
8. **Sort Order:** Automatically adjust sort_order when moving pages

---

## API Endpoint Specification

### POST /api/wikis/{wiki_id}/pages/{page_id}/change-parent

**Description:** Changes the parent of a page

**Authentication:** Required (JWT)

**Path Parameters:**
- `wiki_id` (integer): Wiki ID
- `page_id` (integer): Page ID to move

**Request Body:**
```json
{
  "new_parent_id": 123  // or null for root level
}
```

**Success Response (200):**
```json
{
  "success": true,
  "page": {
    "id": 456,
    "title": "Page Title",
    "parent_id": 123,
    "wiki_id": 1,
    "slug": "page-title",
    "children": [],
    ...
  }
}
```

**Error Responses:**
- `400 Bad Request` - Circular reference detected
  ```json
  {
    "error": "Cannot move page to its own descendant"
  }
  ```
- `403 Forbidden` - User lacks edit permission
  ```json
  {
    "error": "Permission denied"
  }
  ```
- `404 Not Found` - Page, wiki, or new parent not found
  ```json
  {
    "error": "Parent page not found"
  }
  ```

---

## File Change Summary

### New Files
1. `frontend/src/components/MoveConfirmationModal.jsx` - Confirmation dialog component
2. `migrations/versions/XXXX_add_user_settings.py` - Database migration

### Modified Files
1. `app/models/models.py` - Add settings field to User model
2. `app/routes/pages.py` - Add change-parent endpoint
3. `app/routes/auth.py` - Update to handle settings in PATCH /me
4. `frontend/src/services/api.js` - Add changeParent API method
5. `frontend/src/components/PageTree.jsx` - Add drag-and-drop functionality
6. `frontend/src/pages/UserSettings.jsx` - Add move confirmation preference
7. `frontend/src/styles/index.css` - Add drag-and-drop and modal styles
8. `frontend/src/context/AuthContext.jsx` (if exists) - Sync settings to localStorage

---

## Estimated Effort

- **Backend:** 4-6 hours
- **Frontend Core (Drag & Drop):** 6-8 hours
- **Confirmation Modal:** 3-4 hours
- **User Settings:** 2-3 hours
- **Styling:** 2-3 hours
- **Testing & Polish:** 4-6 hours

**Total:** ~20-30 hours (2.5-4 days)

---

## Notes

- No external drag-and-drop library required - HTML5 DnD API is sufficient
- User settings stored as JSON for flexibility (easy to add more preferences later)
- Temporary mute stored in localStorage (persists across page refreshes, cleared by browser)
- Permanent disable stored in database (persists across devices)
- Existing `move_to_parent()` method already handles circular reference prevention
- Page tree refresh may cause slight UI flicker - consider optimistic updates
- Consider adding toast notifications for success/error feedback
