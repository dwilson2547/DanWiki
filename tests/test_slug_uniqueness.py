#!/usr/bin/env python3
"""
Quick test to verify slug uniqueness query logic.
"""
import sys
from app import create_app
from app.models import db, Wiki, Page, User
from slugify import slugify

def test_slug_queries():
    """Test the slug uniqueness query logic."""
    app = create_app()
    
    with app.app_context():
        # Clean up any existing test data first
        existing_wiki = Wiki.query.filter_by(name='Test Wiki for Slug Testing').first()
        if existing_wiki:
            db.session.delete(existing_wiki)
            db.session.commit()
            print("✓ Cleaned up existing test wiki")
        
        # Find or create a test user
        user = User.query.filter_by(username='test_user').first()
        if not user:
            user = User(username='test_user', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        
        # Create a test wiki
        test_wiki = Wiki(
            name='Test Wiki for Slug Testing',
            description='Testing slug uniqueness',
            owner_id=user.id
        )
        db.session.add(test_wiki)
        db.session.commit()
        
        wiki_id = test_wiki.id
        print(f"✓ Created test wiki ID: {wiki_id}")
        
        # Test 1: Create first page with slug '3d-scanner'
        page1 = Page(
            title='3D Scanner',
            slug='3d-scanner',
            content='First page',
            wiki_id=wiki_id,
            created_by_id=user.id,
            last_modified_by_id=user.id
        )
        db.session.add(page1)
        db.session.commit()
        print(f"✓ Created page1: slug='{page1.slug}', parent_id={page1.parent_id}")
        
        # Test 2: Check if '3d-scanner' exists at root level
        query = Page.query.filter_by(wiki_id=wiki_id, slug='3d-scanner', parent_id=None)
        existing = query.first()
        print(f"✓ Query for slug='3d-scanner', parent_id=None: Found={existing is not None}")
        assert existing is not None, "Should find page1"
        
        # Test 3: Check if '3d-scanner-1' exists at root level (should not)
        query = Page.query.filter_by(wiki_id=wiki_id, slug='3d-scanner-1', parent_id=None)
        existing = query.first()
        print(f"✓ Query for slug='3d-scanner-1', parent_id=None: Found={existing is not None}")
        assert existing is None, "Should not find any page"
        
        # Test 4: Create a parent page
        parent = Page(
            title='Parent',
            slug='parent',
            content='Parent page',
            wiki_id=wiki_id,
            created_by_id=user.id,
            last_modified_by_id=user.id
        )
        db.session.add(parent)
        db.session.commit()
        print(f"✓ Created parent: slug='{parent.slug}', id={parent.id}")
        
        # Test 5: Try to create child page with same slug under parent
        # This SHOULD FAIL because slugs are unique per wiki, not per parent
        print("\n--- Testing slug uniqueness constraint ---")
        print("The constraint is on (wiki_id, slug), NOT (wiki_id, slug, parent_id)")
        print("So 'installation' at /tools/installation and /guide/installation would conflict")
        
        # Test 6: Verify both pages exist with same slug but different parents is NOT allowed
        # Instead, test that unique slug generation works
        
        # Test 7: Test the unique slug generation logic (wiki-level uniqueness)
        def generate_unique_slug(base_title: str, parent_id=None):
            base_slug = slugify(base_title)
            slug = base_slug
            counter = 1
            
            # Check wiki-level uniqueness (not parent-level)
            while Page.query.filter_by(wiki_id=wiki_id, slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            return slug
        
        # Should return '3d-scanner-1' because '3d-scanner' exists in the wiki
        new_slug = generate_unique_slug('3D Scanner', parent_id=None)
        print(f"✓ generate_unique_slug('3D Scanner', parent_id=None): '{new_slug}'")
        assert new_slug == '3d-scanner-1', f"Expected '3d-scanner-1', got '{new_slug}'"
        
        # Should STILL return '3d-scanner-1' even with different parent because slug is wiki-wide unique
        new_slug = generate_unique_slug('3D Scanner', parent_id=parent.id)
        print(f"✓ generate_unique_slug('3D Scanner', parent_id={parent.id}): '{new_slug}'")
        assert new_slug == '3d-scanner-1', f"Expected '3d-scanner-1', got '{new_slug}'"
        
        # Should return 'unique-slug' because it doesn't exist
        new_slug = generate_unique_slug('Unique Slug', parent_id=None)
        print(f"✓ generate_unique_slug('Unique Slug', parent_id=None): '{new_slug}'")
        assert new_slug == 'unique-slug', f"Expected 'unique-slug', got '{new_slug}'"
        
        # Cleanup
        db.session.delete(test_wiki)  # Cascade will delete pages
        db.session.commit()
        print(f"✓ Cleaned up test wiki")
        
        print("\n✅ All tests passed!")

if __name__ == '__main__':
    try:
        test_slug_queries()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
