#!/usr/bin/env python3
"""
Wiki Application Entry Point

Run with:
    python run.py

Or for production:
    gunicorn "app:create_app()" -b 0.0.0.0:5000
"""
import os
from app import create_app, db

app = create_app()


@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables."""
    db.create_all()
    print('Database tables created.')


@app.cli.command('create-admin')
def create_admin():
    """Create an admin user."""
    from app.models import User
    
    username = input('Admin username: ')
    email = input('Admin email: ')
    password = input('Admin password: ')
    
    if User.query.filter_by(username=username).first():
        print(f'User {username} already exists.')
        return
    
    admin = User(
        username=username,
        email=email,
        display_name='Administrator',
        is_admin=True,
        is_approved=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'Admin user {username} created successfully.')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed database with demo data."""
    from app.models import User, Wiki, Page
    
    # Create demo user
    demo_user = User.query.filter_by(username='demo').first()
    if not demo_user:
        demo_user = User(
            username='demo',
            email='demo@example.com',
            display_name='Demo User',
            is_approved=True
        )
        demo_user.set_password('demo1234')
        db.session.add(demo_user)
        db.session.commit()
    
    # Create demo wiki
    demo_wiki = Wiki.query.filter_by(owner_id=demo_user.id, slug='getting-started').first()
    if not demo_wiki:
        demo_wiki = Wiki(
            name='Getting Started',
            slug='getting-started',
            description='A demo wiki to help you get started',
            is_public=True,
            owner_id=demo_user.id
        )
        db.session.add(demo_wiki)
        db.session.commit()
    
    # Create demo pages
    if not Page.query.filter_by(wiki_id=demo_wiki.id).first():
        welcome_page = Page(
            title='Welcome',
            slug='welcome',
            content='''# Welcome to your Wiki!

This is a demo page to help you get started with the wiki application.

## Features

- **Hierarchical Pages**: Create parent-child relationships between pages
- **Markdown Support**: Write content using markdown syntax
- **File Attachments**: Upload images and documents
- **Revision History**: Track changes to your pages
- **Collaboration**: Share wikis with team members

Happy writing!
''',
            summary='Welcome page for the demo wiki',
            wiki_id=demo_wiki.id,
            created_by_id=demo_user.id,
            last_modified_by_id=demo_user.id
        )
        db.session.add(welcome_page)
        db.session.commit()
        
        # Create a child page
        guide_page = Page(
            title='Markdown Guide',
            slug='markdown-guide',
            parent_id=welcome_page.id,
            content='''# Markdown Guide

This page demonstrates markdown formatting supported by the wiki.

## Headers

Use `#` for headers. More `#` means smaller headers.

## Text Formatting

- **Bold**: `**text**`
- *Italic*: `*text*`
- `Code`: backticks

## Lists

- Item 1
- Item 2
  - Nested item

## Code Blocks

Use triple backticks for code blocks with syntax highlighting.

## Links

`[Link text](url)` creates a clickable link.
''',
            summary='Guide to using markdown in the wiki',
            wiki_id=demo_wiki.id,
            created_by_id=demo_user.id,
            last_modified_by_id=demo_user.id
        )
        db.session.add(guide_page)
        db.session.commit()
    
    print('Demo data seeded successfully.')
    print('Login with: demo / demo1234')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
