#!/usr/bin/env python3
"""
Script to create database migration for tags and bulk import feature.
Run this after setting up the environment.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app import create_app
from app.models import db

def create_migration():
    """Create a migration for the new Tag model and page_tags table."""
    app = create_app()
    
    with app.app_context():
        print("Creating migration for tags and bulk import...")
        os.system('flask db migrate -m "Add Tag model and page_tags association table for bulk import"')
        print("\nMigration created! Run 'flask db upgrade' to apply it.")

if __name__ == '__main__':
    create_migration()
