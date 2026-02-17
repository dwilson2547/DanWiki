# Phase 1: Backend API Foundation (Day 1)

## Overview

**Priority: HIGH - Foundation for drag and drop functionality**

This phase establishes the backend infrastructure for the drag-and-drop parent change feature. It includes database schema changes, API endpoints, and user preference management. The focus is on creating a robust API that handles parent changes, circular reference prevention, and permission validation.

## Goals

- Add user settings column to database for storing preferences
- Create API endpoint for changing page parent
- Update user settings API to handle move confirmation preferences
- Implement proper error handling and validation
- Ensure circular reference prevention works correctly
- Set up permission checks for page moves

## Timeline

**Duration:** 1 day (Day 1 of implementation)

### Morning: Database & Models
- Create database migration for user settings
- Update User model with settings field
- Test settings persistence

### Afternoon: API Endpoints
- Create change-parent endpoint
- Update auth endpoint for settings
- Test with curl/Postman

## Technical Implementation

### Database Schema

```sql
-- Migration: Add settings column to users table
ALTER TABLE users 
ADD COLUMN settings JSONB DEFAULT '{}';
```

### User Model Update

```python
# app/models/models.py

class User(db.Model):
    # ... existing fields ...
    
    settings = db.Column(db.JSON, default=lambda: {})
    
    def to_dict(self, include_settings=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            # ... other fields ...
        }
        
        if include_settings:
            data['settings'] = self.settings or {}
        
        return data
```

### Change Parent API Endpoint

```python
# app/routes/pages.py

@bp.route('/api/wikis/<int:wiki_id>/pages/<int:page_id>/change-parent', methods=['POST'])
@jwt_required()
def change_page_parent(wiki_id, page_id):
    """
    Change the parent of a page
    
    Request body:
    {
        "new_parent_id": int | null
    }
    """
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    
    # Get page and verify it exists in this wiki
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    # Verify user has edit permission on wiki
    wiki = Wiki.query.get(wiki_id)
    if not wiki or wiki.owner_id != user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get new parent ID from request
    data = request.get_json()
    new_parent_id = data.get('new_parent_id')
    
    # If moving to a new parent (not root)
    if new_parent_id is not None:
        new_parent = Page.query.filter_by(id=new_parent_id, wiki_id=wiki_id).first()
        if not new_parent:
            return jsonify({'error': 'Parent page not found'}), 404
        
        # Check for circular reference using existing method
        try:
            page.move_to_parent(new_parent_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    else:
        # Moving to root
        page.parent_id = None
    
    # Save changes
    db.session.commit()
    
    return jsonify({
        'success': True,
        'page': page.to_dict()
    }), 200
```

### Update Auth Endpoint

```python
# app/routes/auth.py

@bp.route('/api/auth/me', methods=['PATCH'])
@jwt_required()
def update_current_user():
    """Update current user's profile and settings"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update basic fields
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    
    # Update settings (merge with existing)
    if 'settings' in data:
        current_settings = user.settings or {}
        current_settings.update(data['settings'])
        user.settings = current_settings
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict(include_settings=True)
    }), 200
```

## Migration Script

```python
# migrations/versions/XXXX_add_user_settings.py

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
    op.add_column(
        'users', 
        sa.Column('settings', postgresql.JSON, server_default='{}', nullable=True)
    )


def downgrade():
    op.drop_column('users', 'settings')
```

## Testing Requirements

### Unit Tests

```python
# tests/test_pages_routes.py

class TestChangeParent:
    def test_change_parent_success(self):
        """Test successfully changing page parent"""
        
    def test_change_parent_to_root(self):
        """Test moving page to root level (null parent)"""
        
    def test_change_parent_circular_reference(self):
        """Test circular reference is prevented"""
        
    def test_change_parent_permission_denied(self):
        """Test user without permission cannot move page"""
        
    def test_change_parent_page_not_found(self):
        """Test 404 when page doesn't exist"""
        
    def test_change_parent_new_parent_not_found(self):
        """Test 404 when new parent doesn't exist"""
        
    def test_change_parent_preserves_children(self):
        """Test moving page with children preserves structure"""
        
    def test_change_parent_different_wiki(self):
        """Test cannot move page to parent in different wiki"""
```

```python
# tests/test_auth_routes.py

class TestUserSettings:
    def test_update_user_settings(self):
        """Test updating user settings via PATCH /me"""
        
    def test_settings_merge(self):
        """Test settings are merged, not replaced"""
        
    def test_settings_persist(self):
        """Test settings persist after logout/login"""
```

### Manual Testing with curl

```bash
# Test change parent endpoint
curl -X POST http://localhost:5000/api/wikis/1/pages/5/change-parent \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": 3}'

# Test move to root
curl -X POST http://localhost:5000/api/wikis/1/pages/5/change-parent \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": null}'

# Test update user settings
curl -X PATCH http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"settings": {"disable_move_confirmation": true}}'

# Test circular reference prevention
# (Try to move parent page into its own child - should return 400)
curl -X POST http://localhost:5000/api/wikis/1/pages/2/change-parent \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": 5}'  # where 5 is child of 2
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful parent change
- `400 Bad Request`: Circular reference detected, invalid data
- `403 Forbidden`: User lacks permission to edit wiki
- `404 Not Found`: Page, wiki, or new parent not found
- `500 Internal Server Error`: Unexpected server error

### Error Response Format

```json
{
  "error": "Descriptive error message"
}
```

### Common Errors

1. **Circular Reference**
   ```json
   {"error": "Cannot move page to its own descendant"}
   ```

2. **Permission Denied**
   ```json
   {"error": "Permission denied"}
   ```

3. **Page Not Found**
   ```json
   {"error": "Page not found"}
   ```

4. **Parent Not Found**
   ```json
   {"error": "Parent page not found"}
   ```

## Security Considerations

1. **Permission Validation**
   - Always verify user owns the wiki before allowing page moves
   - Check wiki ownership, not just page ownership
   
2. **Data Validation**
   - Validate page and parent belong to same wiki
   - Prevent moving pages across wikis
   
3. **SQL Injection Prevention**
   - Use SQLAlchemy ORM (already prevents SQL injection)
   - Validate all input data types
   
4. **Rate Limiting**
   - Consider rate limiting move operations (future enhancement)

## Success Criteria

- ✓ Database migration runs successfully
- ✓ User settings field stores and retrieves data correctly
- ✓ Change parent endpoint successfully moves pages
- ✓ Change parent endpoint prevents circular references
- ✓ Permission validation works correctly
- ✓ Settings API updates user preferences
- ✓ All error cases return appropriate status codes
- ✓ All unit tests pass
- ✓ Manual testing with curl succeeds

## Dependencies

- Flask-SQLAlchemy: Database ORM
- Flask-JWT-Extended: Authentication
- Alembic: Database migrations
- PostgreSQL/MySQL: Database with JSON support

## Next Phase

After Phase 1 completion, proceed to **Phase 2: Frontend API Integration** to connect the frontend to the new API endpoints.

---

## Progress Tracking

### Feature 1: Database Migration
- [ ] Create migration file `XXXX_add_user_settings.py`
- [ ] Write upgrade() function to add settings column
- [ ] Write downgrade() function to remove settings column
- [ ] Set default value to empty JSON object
- [ ] Test migration on development database
- [ ] Verify settings column exists in database
- [ ] Verify default value is set correctly
- [ ] Run migration on test database
- [ ] Document migration in changelog

### Feature 2: User Model Update
- [ ] Add settings column to User model
- [ ] Set default value as lambda function
- [ ] Update to_dict() method signature
- [ ] Add include_settings parameter
- [ ] Include settings in dict when requested
- [ ] Test settings save and retrieve
- [ ] Test settings default value
- [ ] Verify settings is JSON serializable

### Feature 3: Change Parent API Endpoint
- [ ] Create change-parent route in pages.py
- [ ] Add @jwt_required() decorator
- [ ] Extract current user from JWT
- [ ] Get page by ID and wiki ID
- [ ] Return 404 if page not found
- [ ] Get wiki and verify it exists
- [ ] Check user is wiki owner
- [ ] Return 403 if permission denied
- [ ] Parse request JSON for new_parent_id
- [ ] Handle new_parent_id = null (root move)
- [ ] Query for new parent page
- [ ] Return 404 if new parent not found
- [ ] Verify new parent is in same wiki
- [ ] Call page.move_to_parent() method
- [ ] Catch ValueError for circular reference
- [ ] Return 400 on circular reference
- [ ] Commit database transaction
- [ ] Return success response with updated page
- [ ] Add error logging
- [ ] Test endpoint with valid data

### Feature 4: Circular Reference Prevention
- [ ] Review existing move_to_parent() method
- [ ] Verify it checks for circular references
- [ ] Test moving parent to its child
- [ ] Test moving parent to grandchild
- [ ] Verify ValueError is raised
- [ ] Verify error message is descriptive
- [ ] Test moving to sibling (should work)
- [ ] Document circular reference logic

### Feature 5: Permission Validation
- [ ] Check user is wiki owner
- [ ] Test with wiki owner
- [ ] Test with non-owner user
- [ ] Test with public wiki
- [ ] Test with private wiki
- [ ] Verify 403 returned for unauthorized users
- [ ] Add permission check for collaborators (if supported)
- [ ] Document permission requirements

### Feature 6: Cross-Wiki Prevention
- [ ] Verify page and new parent in same wiki
- [ ] Test moving page to parent in different wiki
- [ ] Verify appropriate error returned
- [ ] Add validation in endpoint
- [ ] Test with multiple wikis

### Feature 7: Update Auth Endpoint
- [ ] Locate existing PATCH /auth/me endpoint
- [ ] Add settings parameter handling
- [ ] Get current user settings
- [ ] Merge new settings with existing
- [ ] Save updated settings
- [ ] Commit transaction
- [ ] Return updated user with settings
- [ ] Test settings update
- [ ] Test settings merge (not replace)
- [ ] Verify old settings preserved

### Feature 8: API Error Handling
- [ ] Define error response format
- [ ] Implement 400 error handler
- [ ] Implement 403 error handler
- [ ] Implement 404 error handler
- [ ] Implement 500 error handler
- [ ] Add descriptive error messages
- [ ] Log errors server-side
- [ ] Test all error scenarios

### Feature 9: Request Validation
- [ ] Validate request has JSON body
- [ ] Validate new_parent_id type
- [ ] Handle missing new_parent_id
- [ ] Handle invalid JSON
- [ ] Return 400 for invalid requests
- [ ] Add input sanitization
- [ ] Test with malformed requests

### Feature 10: Response Format
- [ ] Define success response structure
- [ ] Include success: true field
- [ ] Include updated page object
- [ ] Use consistent JSON format
- [ ] Test response structure
- [ ] Document API response

### Feature 11: Unit Tests - Change Parent
- [ ] Write test_change_parent_success
- [ ] Write test_change_parent_to_root
- [ ] Write test_change_parent_circular_reference
- [ ] Write test_change_parent_permission_denied
- [ ] Write test_change_parent_page_not_found
- [ ] Write test_change_parent_new_parent_not_found
- [ ] Write test_change_parent_preserves_children
- [ ] Write test_change_parent_different_wiki
- [ ] Set up test fixtures
- [ ] Mock authentication
- [ ] Run all tests
- [ ] Verify 100% test coverage

### Feature 12: Unit Tests - User Settings
- [ ] Write test_update_user_settings
- [ ] Write test_settings_merge
- [ ] Write test_settings_persist
- [ ] Write test_settings_default_value
- [ ] Write test_invalid_settings_format
- [ ] Run settings tests
- [ ] Verify test coverage

### Feature 13: Manual Testing - curl
- [ ] Test successful parent change
- [ ] Test move to root
- [ ] Test circular reference prevention
- [ ] Test permission denied
- [ ] Test page not found
- [ ] Test parent not found
- [ ] Test settings update
- [ ] Test settings merge
- [ ] Document curl commands

### Feature 14: Integration Testing
- [ ] Test with real database
- [ ] Test transaction rollback on error
- [ ] Test concurrent move operations
- [ ] Test with large page hierarchies
- [ ] Test database constraints
- [ ] Verify data integrity

### Feature 15: Documentation
- [ ] Document change-parent API endpoint
- [ ] Document request format
- [ ] Document response format
- [ ] Document error codes
- [ ] Document settings structure
- [ ] Add API examples
- [ ] Update API documentation
- [ ] Create developer guide

### Feature 16: Performance Testing
- [ ] Benchmark parent change operation
- [ ] Test with deep page hierarchies
- [ ] Test with many siblings
- [ ] Verify query performance
- [ ] Check for N+1 queries
- [ ] Optimize if needed

### Feature 17: Edge Cases
- [ ] Test moving page with many children
- [ ] Test moving page with nested children
- [ ] Test with empty wiki
- [ ] Test with single page
- [ ] Test same parent move (no-op)
- [ ] Document edge case handling
