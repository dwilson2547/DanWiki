#!/usr/bin/env python3
"""
Script to create a sample wiki archive for testing the bulk import feature.
Creates a sample directory structure with markdown files and other assets.
"""
import os
import tempfile
import zipfile
from pathlib import Path

def create_sample_archive():
    """Create a sample wiki archive for testing."""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir) / 'sample_wiki'
        base_path.mkdir()
        
        # Create home.md at root
        home_md = base_path / 'home.md'
        home_md.write_text("""---
title: Welcome to My Wiki
tags: [welcome, introduction]
---

# Welcome to My Wiki

This is the home page of my wiki created from an archive import.

## Features

- Markdown support
- Hierarchical pages
- File attachments
- Tag support
""")
        
        # Create programming.md at root
        programming_md = base_path / 'programming.md'
        programming_md.write_text("""---
title: Programming Guide
tags: [programming, development]
---

# Programming Guide

This page contains programming resources and guides.

## Languages Covered

- Python
- JavaScript
- Go
""")
        
        # Create programming directory with child pages
        programming_dir = base_path / 'programming'
        programming_dir.mkdir()
        
        # Python page
        python_md = programming_dir / 'python.md'
        python_md.write_text("""# Python Programming

Python is a high-level, interpreted programming language.

## Getting Started

```python
print("Hello, World!")
```

## Popular Libraries

- NumPy
- Pandas
- Django
- Flask
""")
        
        # JavaScript page
        javascript_md = programming_dir / 'javascript.md'
        javascript_md.write_text("""# JavaScript Programming

JavaScript is the language of the web.

## Basic Example

```javascript
console.log("Hello, World!");
```

## Frameworks

- React
- Vue
- Angular
""")
        
        # Create a directory without matching .md file (should create blank page)
        resources_dir = base_path / 'resources'
        resources_dir.mkdir()
        
        # Add some files to resources (will become attachments)
        readme_txt = resources_dir / 'readme.txt'
        readme_txt.write_text('This is a sample text file that will become an attachment.')
        
        notes_md = resources_dir / 'notes.md'
        notes_md.write_text("""# Resource Notes

Some important notes and links.

- [Python Docs](https://docs.python.org)
- [MDN Web Docs](https://developer.mozilla.org)
""")
        
        # Create nested structure
        tutorials_dir = programming_dir / 'tutorials'
        tutorials_dir.mkdir()
        
        beginners_md = tutorials_dir / 'beginners.md'
        beginners_md.write_text("""---
title: Beginner's Tutorial
tags: [tutorial, beginner]
---

# Beginner's Programming Tutorial

Start your programming journey here!

## Step 1: Choose a Language

Pick a language that interests you.

## Step 2: Write Your First Program

The classic "Hello, World!" program.

## Step 3: Practice

Consistency is key to learning programming.
""")
        
        # Create the zip archive
        output_path = Path.cwd() / 'sample_wiki.zip'
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in base_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(base_path.parent)
                    zipf.write(file_path, arcname)
        
        print(f"Sample wiki archive created: {output_path}")
        print("\nArchive structure:")
        print("sample_wiki/")
        print("  ├── home.md (with frontmatter)")
        print("  ├── programming.md (with frontmatter)")
        print("  ├── programming/")
        print("  │   ├── python.md")
        print("  │   ├── javascript.md")
        print("  │   └── tutorials/")
        print("  │       └── beginners.md (with frontmatter)")
        print("  └── resources/ (directory without .md)")
        print("      ├── readme.txt (will be attachment)")
        print("      └── notes.md")
        print("\nExpected page hierarchy after import:")
        print("  ├── Welcome to My Wiki (home.md)")
        print("  ├── Programming Guide (programming.md)")
        print("  │   ├── Python Programming (python.md)")
        print("  │   ├── JavaScript Programming (javascript.md)")
        print("  │   └── Tutorials (blank page for directory)")
        print("  │       └── Beginner's Tutorial (beginners.md)")
        print("  └── Resources (blank page for directory)")
        print("      └── Resource Notes (notes.md)")
        print("\nAttachments:")
        print("  └── readme.txt (attached to Resources page)")

if __name__ == '__main__':
    create_sample_archive()
