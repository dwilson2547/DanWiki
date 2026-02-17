# Phase 7: Testing & Polish (Day 4)

## Overview

**Priority: CRITICAL - Quality assurance**

This final phase focuses on comprehensive testing, bug fixes, and final polish to ensure the drag-and-drop feature is production-ready. Includes unit tests, integration tests, end-to-end tests, edge case handling, and performance optimization.

## Goals

- Complete test coverage (>85%)
- All edge cases handled
- Performance optimized
- Security validated
- Documentation finalized
- User acceptance testing
- Production deployment preparation

## Timeline

**Duration:** 1 day (Day 4 full day)

### Day 4 Morning: Testing
- Write and run all tests
- Fix failing tests
- Achieve coverage goals

### Day 4 Afternoon: Polish & Deploy
- Fix bugs found during testing
- Final performance optimization
- Documentation review
- Prepare for deployment

## Technical Implementation

### Unit Tests - Backend

```python
# tests/test_change_parent_api.py

import pytest
from backend.models import db, Wiki, Page, User

def test_change_parent_success(client, auth_token, test_wiki, test_pages):
    """Test successful parent change"""
    page_id = test_pages['child1'].id
    new_parent_id = test_pages['parent2'].id
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page_id}/change-parent',
        json={'new_parent_id': new_parent_id},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.json
    assert data['message'] == 'Parent changed successfully'
    assert data['page']['parent_id'] == new_parent_id

def test_change_parent_to_root(client, auth_token, test_wiki, test_pages):
    """Test moving page to root level"""
    page_id = test_pages['child1'].id
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page_id}/change-parent',
        json={'new_parent_id': None},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.json
    assert data['page']['parent_id'] is None

def test_prevent_circular_reference(client, auth_token, test_wiki, test_pages):
    """Test circular reference prevention"""
    parent_id = test_pages['parent1'].id
    child_id = test_pages['child1'].id
    
    # Try to move parent into its own child
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{parent_id}/change-parent',
        json={'new_parent_id': child_id},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400
    assert 'circular reference' in response.json['error'].lower()

def test_page_not_found(client, auth_token, test_wiki):
    """Test with non-existent page"""
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/99999/change-parent',
        json={'new_parent_id': None},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 404

def test_unauthorized_access(client, test_wiki, test_pages):
    """Test without authentication"""
    page_id = test_pages['child1'].id
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page_id}/change-parent',
        json={'new_parent_id': None}
    )
    
    assert response.status_code == 401

def test_wrong_wiki(client, auth_token, test_wiki, test_pages, other_wiki):
    """Test with page from different wiki"""
    page_id = test_pages['child1'].id
    
    response = client.post(
        f'/api/wikis/{other_wiki.id}/pages/{page_id}/change-parent',
        json={'new_parent_id': None},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 404

def test_missing_new_parent_id(client, auth_token, test_wiki, test_pages):
    """Test with missing new_parent_id field"""
    page_id = test_pages['child1'].id
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page_id}/change-parent',
        json={},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400

def test_is_descendant_direct_child(test_pages):
    """Test is_descendant with direct child"""
    parent = test_pages['parent1']
    child = test_pages['child1']
    
    assert Page.is_descendant(child.id, parent.id) is True

def test_is_descendant_grandchild(test_pages):
    """Test is_descendant with nested child"""
    parent = test_pages['parent1']
    grandchild = test_pages['grandchild1']
    
    assert Page.is_descendant(grandchild.id, parent.id) is True

def test_is_descendant_not_related(test_pages):
    """Test is_descendant with unrelated pages"""
    page1 = test_pages['parent1']
    page2 = test_pages['parent2']
    
    assert Page.is_descendant(page2.id, page1.id) is False

def test_is_descendant_self(test_pages):
    """Test is_descendant with same page"""
    page = test_pages['parent1']
    
    assert Page.is_descendant(page.id, page.id) is True

def test_update_modified_timestamp(client, auth_token, test_wiki, test_pages):
    """Test that modified timestamp is updated"""
    page = test_pages['child1']
    original_modified = page.modified_at
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page.id}/change-parent',
        json={'new_parent_id': None},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    updated_page = Page.query.get(page.id)
    assert updated_page.modified_at > original_modified

def test_change_parent_updates_order(client, auth_token, test_wiki, test_pages):
    """Test that page is added to end of new parent's children"""
    page = test_pages['child1']
    new_parent = test_pages['parent2']
    
    # Count children before
    children_before = Page.query.filter_by(parent_id=new_parent.id).count()
    
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{page.id}/change-parent',
        json={'new_parent_id': new_parent.id},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    
    # Verify added to end
    children_after = Page.query.filter_by(parent_id=new_parent.id).all()
    assert len(children_after) == children_before + 1
    assert children_after[-1].id == page.id
```

### Unit Tests - User Settings

```python
# tests/test_user_settings.py

def test_get_empty_settings(client, auth_token):
    """Test getting settings when none exist"""
    response = client.get(
        '/api/users/me/settings',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    assert response.json['settings'] == {} or response.json['settings'] is None

def test_update_drag_drop_settings(client, auth_token):
    """Test updating drag and drop settings"""
    response = client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': True},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    settings = response.json['settings']
    assert settings['drag_and_drop']['disable_move_confirmation'] is True

def test_toggle_disable_confirmation(client, auth_token):
    """Test toggling disable confirmation on and off"""
    # Enable
    client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': True},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Verify enabled
    response = client.get(
        '/api/users/me/settings',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.json['settings']['drag_and_drop']['disable_move_confirmation'] is True
    
    # Disable
    client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': False},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Verify disabled
    response = client.get(
        '/api/users/me/settings',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.json['settings']['drag_and_drop']['disable_move_confirmation'] is False

def test_invalid_setting_type(client, auth_token):
    """Test with invalid type for disable_move_confirmation"""
    response = client.patch(
        '/api/users/me/settings/drag-and-drop',
        json={'disable_move_confirmation': 'yes'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400
```

### Component Tests - Frontend

```javascript
// tests/components/PageTreeItem.test.jsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PageTreeItem } from '../../src/components/PageTreeItem';

describe('PageTreeItem', () => {
  const mockPage = {
    id: 1,
    title: 'Test Page',
    children: []
  };
  
  const mockOnMoveRequest = jest.fn();
  
  test('renders page title', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    expect(screen.getByText('Test Page')).toBeInTheDocument();
  });
  
  test('is draggable when not loading', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} loading={false} />);
    const item = screen.getByText('Test Page').closest('li');
    expect(item).toHaveAttribute('draggable', 'true');
  });
  
  test('is not draggable when loading', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} loading={true} />);
    const item = screen.getByText('Test Page').closest('li');
    expect(item).toHaveAttribute('draggable', 'false');
  });
  
  test('drag start sets data transfer', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    const item = screen.getByText('Test Page').closest('li');
    
    const dataTransfer = {
      effectAllowed: null,
      setData: jest.fn(),
      setDragImage: jest.fn()
    };
    
    fireEvent.dragStart(item, { dataTransfer });
    
    expect(dataTransfer.effectAllowed).toBe('move');
    expect(dataTransfer.setData).toHaveBeenCalledWith(
      'application/json',
      expect.stringContaining('"pageId":1')
    );
  });
  
  test('drag over adds drag-over class', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    const item = screen.getByText('Test Page').closest('li');
    
    fireEvent.dragOver(item);
    
    expect(item).toHaveClass('drag-over');
  });
  
  test('drag leave removes drag-over class', () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    const item = screen.getByText('Test Page').closest('li');
    
    fireEvent.dragOver(item);
    expect(item).toHaveClass('drag-over');
    
    fireEvent.dragLeave(item, { currentTarget: item, target: item });
    expect(item).not.toHaveClass('drag-over');
  });
  
  test('drop calls onMoveRequest', async () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    const item = screen.getByText('Test Page').closest('li');
    
    const dragData = { pageId: 2, pageTitle: 'Dragged Page', hasChildren: false };
    const dataTransfer = {
      getData: jest.fn().mockReturnValue(JSON.stringify(dragData))
    };
    
    fireEvent.drop(item, { dataTransfer });
    
    await waitFor(() => {
      expect(mockOnMoveRequest).toHaveBeenCalledWith(dragData, mockPage);
    });
  });
  
  test('self-drop is prevented', async () => {
    render(<PageTreeItem page={mockPage} onMoveRequest={mockOnMoveRequest} />);
    const item = screen.getByText('Test Page').closest('li');
    
    const dragData = { pageId: 1, pageTitle: 'Test Page', hasChildren: false };
    const dataTransfer = {
      getData: jest.fn().mockReturnValue(JSON.stringify(dragData))
    };
    
    fireEvent.drop(item, { dataTransfer });
    
    await waitFor(() => {
      expect(mockOnMoveRequest).not.toHaveBeenCalled();
    });
  });
  
  test('renders children recursively', () => {
    const pageWithChildren = {
      ...mockPage,
      children: [
        { id: 2, title: 'Child 1', children: [] },
        { id: 3, title: 'Child 2', children: [] }
      ]
    };
    
    render(<PageTreeItem page={pageWithChildren} onMoveRequest={mockOnMoveRequest} />);
    
    expect(screen.getByText('Child 1')).toBeInTheDocument();
    expect(screen.getByText('Child 2')).toBeInTheDocument();
  });
});
```

### Component Tests - Modal

```javascript
// tests/components/MoveConfirmationModal.test.jsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MoveConfirmationModal } from '../../src/components/MoveConfirmationModal';

describe('MoveConfirmationModal', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();
  const mockOnMuteChange = jest.fn();
  
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    onMuteChange: mockOnMuteChange,
    pageTitle: 'Test Page',
    newParentTitle: 'New Parent',
    hasChildren: false
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders when open', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    expect(screen.getByText(/Move Page/)).toBeInTheDocument();
  });
  
  test('does not render when closed', () => {
    render(<MoveConfirmationModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText(/Move Page/)).not.toBeInTheDocument();
  });
  
  test('displays page and parent titles', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    expect(screen.getByText(/Test Page/)).toBeInTheDocument();
    expect(screen.getByText(/New Parent/)).toBeInTheDocument();
  });
  
  test('shows warning when page has children', () => {
    render(<MoveConfirmationModal {...defaultProps} hasChildren={true} />);
    expect(screen.getByText(/has child pages/i)).toBeInTheDocument();
  });
  
  test('confirm button calls onConfirm', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    fireEvent.click(screen.getByText(/Move/));
    expect(mockOnConfirm).toHaveBeenCalled();
  });
  
  test('cancel button calls onClose', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    fireEvent.click(screen.getByText(/Cancel/));
    expect(mockOnClose).toHaveBeenCalled();
  });
  
  test('close button calls onClose', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    fireEvent.click(screen.getByLabelText(/close/i));
    expect(mockOnClose).toHaveBeenCalled();
  });
  
  test('mute dropdown calls onMuteChange', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    const dropdown = screen.getByRole('combobox');
    
    fireEvent.change(dropdown, { target: { value: '5' } });
    
    expect(mockOnMuteChange).toHaveBeenCalledWith(5);
  });
  
  test('backdrop click calls onClose', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    fireEvent.click(screen.getByTestId('modal-backdrop'));
    expect(mockOnClose).toHaveBeenCalled();
  });
  
  test('modal content click does not close', () => {
    render(<MoveConfirmationModal {...defaultProps} />);
    fireEvent.click(screen.getByRole('dialog'));
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});
```

### Integration Tests

```javascript
// tests/integration/dragAndDrop.integration.test.jsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { WikiApp } from '../../src/App';

const server = setupServer(
  rest.get('/api/wikis/:wikiId/pages', (req, res, ctx) => {
    return res(ctx.json({
      pages: [
        { id: 1, title: 'Page 1', parent_id: null, children: [] },
        { id: 2, title: 'Page 2', parent_id: null, children: [] }
      ]
    }));
  }),
  
  rest.post('/api/wikis/:wikiId/pages/:pageId/change-parent', (req, res, ctx) => {
    return res(ctx.json({
      message: 'Parent changed successfully',
      page: { id: 1, title: 'Page 1', parent_id: 2 }
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Drag and Drop Integration', () => {
  test('complete drag and drop flow', async () => {
    render(<WikiApp wikiId="1" />);
    
    // Wait for pages to load
    await waitFor(() => {
      expect(screen.getByText('Page 1')).toBeInTheDocument();
    });
    
    // Start drag
    const page1 = screen.getByText('Page 1').closest('li');
    const page2 = screen.getByText('Page 2').closest('li');
    
    const dragData = { pageId: 1, pageTitle: 'Page 1', hasChildren: false };
    const dataTransfer = {
      effectAllowed: null,
      setData: jest.fn(),
      getData: jest.fn().mockReturnValue(JSON.stringify(dragData)),
      setDragImage: jest.fn()
    };
    
    fireEvent.dragStart(page1, { dataTransfer });
    fireEvent.dragOver(page2, { dataTransfer });
    fireEvent.drop(page2, { dataTransfer });
    
    // Modal should appear
    await waitFor(() => {
      expect(screen.getByText(/Move Page/)).toBeInTheDocument();
    });
    
    // Confirm move
    fireEvent.click(screen.getByText(/^Move$/));
    
    // Verify API called
    await waitFor(() => {
      expect(screen.getByText(/moved successfully/i)).toBeInTheDocument();
    });
  });
  
  test('drag and drop with confirmation muted', async () => {
    // Set mute in localStorage
    localStorage.setItem('move_confirmation_mute', JSON.stringify({
      expiresAt: Date.now() + 60000
    }));
    
    render(<WikiApp wikiId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText('Page 1')).toBeInTheDocument();
    });
    
    // Perform drag and drop
    const page1 = screen.getByText('Page 1').closest('li');
    const page2 = screen.getByText('Page 2').closest('li');
    
    // ... perform drag ...
    
    // Modal should NOT appear
    expect(screen.queryByText(/Move Page/)).not.toBeInTheDocument();
    
    // API should be called directly
    await waitFor(() => {
      expect(screen.getByText(/moved successfully/i)).toBeInTheDocument();
    });
  });
  
  test('API error shows error message', async () => {
    server.use(
      rest.post('/api/wikis/:wikiId/pages/:pageId/change-parent', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({
          error: 'Circular reference detected'
        }));
      })
    );
    
    render(<WikiApp wikiId="1" />);
    
    // ... perform drag and drop ...
    // ... confirm in modal ...
    
    await waitFor(() => {
      expect(screen.getByText(/Circular reference/i)).toBeInTheDocument();
    });
  });
});
```

### End-to-End Tests

```javascript
// tests/e2e/dragAndDrop.e2e.test.js

describe('Drag and Drop E2E', () => {
  beforeEach(async () => {
    await page.goto('http://localhost:3000/wiki/1');
    await page.waitForSelector('.page-tree');
  });
  
  test('drag page to new parent', async () => {
    // Find pages
    const page1 = await page.$('.page-tree-item:nth-child(1)');
    const page2 = await page.$('.page-tree-item:nth-child(2)');
    
    // Get bounding boxes
    const box1 = await page1.boundingBox();
    const box2 = await page2.boundingBox();
    
    // Perform drag and drop
    await page.mouse.move(box1.x + box1.width / 2, box1.y + box1.height / 2);
    await page.mouse.down();
    await page.mouse.move(box2.x + box2.width / 2, box2.y + box2.height / 2);
    await page.mouse.up();
    
    // Wait for modal
    await page.waitForSelector('.confirmation-modal');
    
    // Click confirm
    await page.click('.modal-button-confirm');
    
    // Wait for success message
    await page.waitForSelector('.toast-success');
    
    // Verify page moved
    const pageAfter = await page.$eval(
      '.page-tree-item:nth-child(2) .page-tree-children .page-tree-item',
      el => el.textContent
    );
    expect(pageAfter).toContain('Page 1');
  });
  
  test('drag page to root level', async () => {
    // Find nested page
    const nestedPage = await page.$('.page-tree-children .page-tree-item');
    const rootDropZone = await page.$('.root-drop-zone');
    
    // Perform drag and drop
    const nestedBox = await nestedPage.boundingBox();
    const dropBox = await rootDropZone.boundingBox();
    
    await page.mouse.move(nestedBox.x + nestedBox.width / 2, nestedBox.y + nestedBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(dropBox.x + dropBox.width / 2, dropBox.y + dropBox.height / 2);
    await page.mouse.up();
    
    // Confirm
    await page.waitForSelector('.confirmation-modal');
    await page.click('.modal-button-confirm');
    
    // Verify at root
    const rootPages = await page.$$eval('.page-tree > .page-tree-item', els => els.length);
    expect(rootPages).toBeGreaterThan(0);
  });
  
  test('mute confirmation for 5 minutes', async () => {
    // Perform drag and drop
    // ... drag operations ...
    
    // Wait for modal
    await page.waitForSelector('.confirmation-modal');
    
    // Select mute duration
    await page.select('.mute-dropdown', '5');
    
    // Confirm
    await page.click('.modal-button-confirm');
    
    // Verify localStorage
    const muteData = await page.evaluate(() => {
      return localStorage.getItem('move_confirmation_mute');
    });
    expect(muteData).toBeTruthy();
    
    // Perform another drag
    // ... drag operations ...
    
    // Modal should not appear
    await page.waitForTimeout(500);
    const modal = await page.$('.confirmation-modal');
    expect(modal).toBeNull();
  });
});
```

### Performance Tests

```javascript
// tests/performance/dragAndDrop.perf.test.js

describe('Performance Tests', () => {
  test('handles 1000 pages without lag', async () => {
    const startTime = performance.now();
    
    // Generate 1000 pages
    const pages = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      title: `Page ${i + 1}`,
      parent_id: null,
      children: []
    }));
    
    render(<PageTree wikiId="1" pages={pages} onRefresh={jest.fn()} />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    expect(renderTime).toBeLessThan(2000); // Should render in < 2 seconds
  });
  
  test('drag animation maintains 60fps', async () => {
    // Use performance.now() to measure frame times
    const frameTimes = [];
    let lastTime = performance.now();
    
    const measureFrame = () => {
      const currentTime = performance.now();
      frameTimes.push(currentTime - lastTime);
      lastTime = currentTime;
    };
    
    // Simulate drag
    // ... measure during drag ...
    
    const avgFrameTime = frameTimes.reduce((a, b) => a + b) / frameTimes.length;
    const fps = 1000 / avgFrameTime;
    
    expect(fps).toBeGreaterThan(55); // Close to 60fps
  });
});
```

### Edge Cases Checklist

- [ ] Drag page onto itself (should be prevented)
- [ ] Drag parent into its child (API rejects)
- [ ] Drag parent into its grandchild (API rejects)
- [ ] Drag page while another drag in progress (HTML5 prevents)
- [ ] Drag page to same parent (should work, but no change)
- [ ] Drag outside window (drag ends cleanly)
- [ ] Rapid successive drags (loading state prevents)
- [ ] Network failure during move (error shown, state reverted)
- [ ] Drag with expired mute (confirmation shown)
- [ ] Settings change in another tab (syncs via localStorage)
- [ ] Modal open when page unloads (cleanup)
- [ ] Very long page titles (truncated with ellipsis)
- [ ] Page with 100+ children (warning shown)
- [ ] Empty wiki (drop zone works)
- [ ] Single page (can move to root)

### Security Testing

```python
# tests/test_security.py

def test_unauthorized_user_cannot_move_pages(client, test_wiki, test_pages):
    """Test that unauthenticated users cannot move pages"""
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/{test_pages["child1"].id}/change-parent',
        json={'new_parent_id': None}
    )
    assert response.status_code == 401

def test_user_cannot_move_pages_in_other_users_wiki(client, auth_token, other_user_wiki, test_pages):
    """Test that users cannot modify other users' wikis"""
    response = client.post(
        f'/api/wikis/{other_user_wiki.id}/pages/{test_pages["child1"].id}/change-parent',
        json={'new_parent_id': None},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 403

def test_sql_injection_prevention(client, auth_token, test_wiki):
    """Test that SQL injection attempts are prevented"""
    response = client.post(
        f'/api/wikis/{test_wiki.id}/pages/1/change-parent',
        json={'new_parent_id': "1; DROP TABLE pages; --"},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    # Should fail validation, not execute SQL
    assert response.status_code == 400

def test_xss_prevention_in_page_title(client, auth_token, test_wiki, test_pages):
    """Test that XSS in page titles is prevented"""
    page = test_pages['child1']
    page.title = '<script>alert("xss")</script>'
    db.session.commit()
    
    response = client.get(
        f'/api/wikis/{test_wiki.id}/pages',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Title should be escaped or sanitized
    assert '<script>' not in response.text
```

## Production Readiness Checklist

### Code Quality
- [ ] All linting errors fixed
- [ ] Code formatted consistently
- [ ] No console.log statements in production code
- [ ] No commented-out code
- [ ] All TODO comments addressed
- [ ] Code reviewed

### Testing
- [ ] Unit tests: >85% coverage
- [ ] Integration tests: All critical paths
- [ ] E2E tests: All user flows
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Cross-browser tests pass

### Documentation
- [ ] API endpoints documented
- [ ] Component props documented
- [ ] User guide written
- [ ] Developer documentation complete
- [ ] CHANGELOG updated
- [ ] README updated

### Deployment
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Rollback plan prepared
- [ ] Monitoring/logging configured
- [ ] Error tracking configured
- [ ] Performance monitoring configured

### Final Validation
- [ ] Staging deployment successful
- [ ] User acceptance testing complete
- [ ] Stakeholder sign-off obtained
- [ ] Production deployment plan reviewed

## Success Criteria

- ✓ Test coverage >85%
- ✓ All edge cases handled
- ✓ Performance meets requirements
- ✓ Security validated
- ✓ Documentation complete
- ✓ Production ready

---

## Progress Tracking

### Feature 1: Backend Unit Tests - Change Parent API
- [ ] Create tests/test_change_parent_api.py
- [ ] Write test: successful parent change
- [ ] Write test: move to root level
- [ ] Write test: prevent circular reference
- [ ] Write test: page not found
- [ ] Write test: unauthorized access
- [ ] Write test: wrong wiki
- [ ] Write test: missing new_parent_id
- [ ] Run tests and verify pass

### Feature 2: Backend Unit Tests - is_descendant Helper
- [ ] Write test: direct child
- [ ] Write test: grandchild (nested)
- [ ] Write test: unrelated pages
- [ ] Write test: self reference
- [ ] Test with complex hierarchies
- [ ] Run tests and verify pass

### Feature 3: Backend Unit Tests - Additional Coverage
- [ ] Write test: modified timestamp updated
- [ ] Write test: page order updated
- [ ] Write test: database transaction rollback
- [ ] Write test: concurrent updates
- [ ] Run tests and verify pass

### Feature 4: Backend Unit Tests - User Settings
- [ ] Create tests/test_user_settings.py
- [ ] Write test: get empty settings
- [ ] Write test: update drag-drop settings
- [ ] Write test: toggle disable confirmation
- [ ] Write test: invalid setting type
- [ ] Write test: settings persistence
- [ ] Run tests and verify pass

### Feature 5: Frontend Component Tests - PageTreeItem
- [ ] Create tests/components/PageTreeItem.test.jsx
- [ ] Write test: renders page title
- [ ] Write test: draggable when not loading
- [ ] Write test: not draggable when loading
- [ ] Write test: drag start sets data transfer
- [ ] Write test: drag over adds class
- [ ] Write test: drag leave removes class
- [ ] Write test: drop calls onMoveRequest
- [ ] Write test: self-drop prevented
- [ ] Write test: renders children recursively
- [ ] Run tests and verify pass

### Feature 6: Frontend Component Tests - MoveConfirmationModal
- [ ] Create tests/components/MoveConfirmationModal.test.jsx
- [ ] Write test: renders when open
- [ ] Write test: does not render when closed
- [ ] Write test: displays titles
- [ ] Write test: shows warning with children
- [ ] Write test: confirm button calls onConfirm
- [ ] Write test: cancel button calls onClose
- [ ] Write test: close button calls onClose
- [ ] Write test: mute dropdown calls onMuteChange
- [ ] Write test: backdrop click closes
- [ ] Write test: modal content click doesn't close
- [ ] Run tests and verify pass

### Feature 7: Frontend Component Tests - PageTree
- [ ] Write test: renders page list
- [ ] Write test: handleMoveRequest logic
- [ ] Write test: executeMove logic
- [ ] Write test: confirmation shown when not muted
- [ ] Write test: confirmation skipped when muted
- [ ] Write test: tree refreshes after move
- [ ] Run tests and verify pass

### Feature 8: Frontend Component Tests - RootDropZone
- [ ] Write test: renders drop zone
- [ ] Write test: drag over adds class
- [ ] Write test: drag leave removes class
- [ ] Write test: drop calls onDrop
- [ ] Write test: parses drag data
- [ ] Run tests and verify pass

### Feature 9: Integration Tests
- [ ] Create tests/integration/dragAndDrop.integration.test.jsx
- [ ] Set up MSW server
- [ ] Write test: complete drag and drop flow
- [ ] Write test: with confirmation muted
- [ ] Write test: API error handling
- [ ] Write test: tree refresh after success
- [ ] Write test: loading state during operation
- [ ] Run tests and verify pass

### Feature 10: End-to-End Tests
- [ ] Create tests/e2e/dragAndDrop.e2e.test.js
- [ ] Set up Puppeteer/Playwright
- [ ] Write test: drag page to new parent
- [ ] Write test: drag page to root level
- [ ] Write test: mute confirmation
- [ ] Write test: settings persistence
- [ ] Write test: multi-tab sync
- [ ] Run tests and verify pass

### Feature 11: Performance Tests
- [ ] Create tests/performance/dragAndDrop.perf.test.js
- [ ] Write test: render 1000 pages
- [ ] Write test: drag animation FPS
- [ ] Write test: memory usage
- [ ] Write test: API response time
- [ ] Run tests and verify pass

### Feature 12: Security Tests
- [ ] Create tests/test_security.py
- [ ] Write test: unauthorized access
- [ ] Write test: cross-user wiki access
- [ ] Write test: SQL injection prevention
- [ ] Write test: XSS prevention
- [ ] Write test: CSRF protection
- [ ] Run tests and verify pass

### Feature 13: Edge Case Testing
- [ ] Test: drag onto self
- [ ] Test: circular reference
- [ ] Test: nested circular reference
- [ ] Test: drag outside window
- [ ] Test: rapid successive drags
- [ ] Test: network failure during move
- [ ] Test: expired mute
- [ ] Test: very long titles
- [ ] Test: page with many children
- [ ] Test: empty wiki
- [ ] Document all edge cases

### Feature 14: Cross-Browser Testing
- [ ] Test in Chrome (latest)
- [ ] Test in Firefox (latest)
- [ ] Test in Safari (latest)
- [ ] Test in Edge (latest)
- [ ] Test in Mobile Safari
- [ ] Test in Chrome Android
- [ ] Document browser issues

### Feature 15: Accessibility Testing
- [ ] Run axe accessibility checker
- [ ] Test keyboard navigation
- [ ] Test with screen reader
- [ ] Test focus management
- [ ] Test ARIA labels
- [ ] Fix any violations
- [ ] Document accessibility features

### Feature 16: Code Coverage
- [ ] Run coverage report
- [ ] Identify uncovered lines
- [ ] Write tests for uncovered code
- [ ] Achieve >85% coverage
- [ ] Generate coverage badge
- [ ] Add to README

### Feature 17: Bug Fixes
- [ ] Review all test failures
- [ ] Fix failing tests
- [ ] Re-run test suite
- [ ] Verify all tests pass
- [ ] Test fixes manually

### Feature 18: Performance Optimization
- [ ] Profile drag operations
- [ ] Optimize re-renders
- [ ] Lazy load nested pages
- [ ] Debounce drag events if needed
- [ ] Measure improvements
- [ ] Document optimizations

### Feature 19: Code Quality
- [ ] Run linter on all files
- [ ] Fix linting errors
- [ ] Format code consistently
- [ ] Remove console.logs
- [ ] Remove commented code
- [ ] Address TODO comments
- [ ] Run code review

### Feature 20: Documentation - API
- [ ] Document change-parent endpoint
- [ ] Document user settings endpoints
- [ ] Add request/response examples
- [ ] Document error codes
- [ ] Add authentication requirements
- [ ] Update API reference

### Feature 21: Documentation - Components
- [ ] Document PageTree props
- [ ] Document PageTreeItem props
- [ ] Document MoveConfirmationModal props
- [ ] Document RootDropZone props
- [ ] Add usage examples
- [ ] Document hooks

### Feature 22: Documentation - User Guide
- [ ] Write drag and drop guide
- [ ] Add screenshots/GIFs
- [ ] Document mute feature
- [ ] Document settings toggle
- [ ] Add troubleshooting section
- [ ] Review for clarity

### Feature 23: Documentation - Developer Guide
- [ ] Document architecture
- [ ] Document testing approach
- [ ] Document deployment steps
- [ ] Add contribution guide
- [ ] Update CHANGELOG
- [ ] Update README

### Feature 24: Staging Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Verify all features work
- [ ] Check error logging
- [ ] Monitor performance
- [ ] Get stakeholder approval

### Feature 25: Production Preparation
- [ ] Review environment variables
- [ ] Test database migrations
- [ ] Prepare rollback plan
- [ ] Configure monitoring
- [ ] Configure error tracking
- [ ] Schedule deployment window

### Feature 26: User Acceptance Testing
- [ ] Invite test users
- [ ] Provide testing instructions
- [ ] Collect feedback
- [ ] Address critical issues
- [ ] Get sign-off
- [ ] Document feedback

### Feature 27: Final Validation
- [ ] All tests pass
- [ ] Coverage goals met
- [ ] Documentation complete
- [ ] Stakeholders approve
- [ ] Deployment plan ready
- [ ] Go/no-go decision

### Feature 28: Production Deployment
- [ ] Execute deployment plan
- [ ] Run database migrations
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Verify health checks
- [ ] Monitor errors
- [ ] Announce release
