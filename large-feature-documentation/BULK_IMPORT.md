# Bulk Wiki Import Feature

## Overview

The bulk import feature allows you to create entire wiki structures from archive files (.zip or .tar.gz). This is perfect for:

- Migrating existing documentation
- Importing personal wikis from other systems
- Bulk creation of structured content
- Setting up wikis with predefined hierarchies

## Features

### Archive Processing
- **Supported Formats**: .zip, .tar, .tar.gz, .tgz
- **Maximum Size**: 500MB
- **Directory Structure Preservation**: The folder hierarchy in your archive becomes the page hierarchy

### Smart Page Creation
- **Markdown Files**: .md and .markdown files become wiki pages
- **Title Detection**: 
  1. Uses `title` from YAML frontmatter if present
  2. Falls back to first H1 heading in the content
  3. Uses filename as last resort
- **Frontmatter Support**: Parse YAML metadata for title and tags

### Hierarchical Structure
- **Directory Matching**: Files in `page1/` directory become children of `page1.md`
- **Auto-Generated Pages**: Directories without matching .md files get blank placeholder pages
- **Nested Hierarchies**: Full support for deeply nested directory structures

### File Attachments
- Non-markdown files automatically become attachments to their parent page
- Supported file types: images, PDFs, documents, code files, etc.

### Tagging System
- **Tag Model**: New Tag model with many-to-many relationship to pages
- **Frontmatter Tags**: Tags from YAML frontmatter automatically created and assigned
- **Tag Format**: Supports both list format (`[tag1, tag2]`) and comma-separated strings

## API Endpoints

### Create New Wiki from Archive

**POST** `/api/wikis/import`

Import archive and create a new wiki in one step.

**Form Data:**
- `archive`: The zip or tar.gz file (required)
- `name`: Wiki name (required)
- `description`: Wiki description (optional)
- `is_public`: "true" or "false" (optional, default: false)

**Response:**
```json
{
  "message": "Wiki created and import completed",
  "wiki": {
    "id": 1,
    "name": "My Wiki",
    "slug": "my-wiki",
    "description": "Imported from archive",
    "is_public": false,
    "owner": {...},
    "created_at": "2026-01-18T...",
    "updated_at": "2026-01-18T..."
  },
  "import_result": {
    "success_count": 10,
    "failure_count": 0,
    "pages_created": [
      {"title": "Home", "id": 1},
      {"title": "Getting Started", "id": 2},
      ...
    ],
    "attachments_created": [
      {"filename": "diagram.png", "id": 1},
      ...
    ],
    "errors": [],
    "total_processed": 10
  }
}
```

### Import into Existing Wiki

**POST** `/api/wikis/:wiki_id/import`

Import archive into an existing wiki.

**Form Data:**
- `archive`: The zip or tar.gz file (required)
- `parent_page_id`: ID of parent page to import under (optional, omit for root level)

**Response:**
```json
{
  "message": "Import completed",
  "import_result": {
    "success_count": 5,
    "failure_count": 1,
    "pages_created": [...],
    "attachments_created": [...],
    "errors": [
      {"item": "broken.md", "error": "Invalid encoding"}
    ],
    "total_processed": 6
  }
}
```

### Get Page Tree

**GET** `/api/wikis/:wiki_id/pages/tree`

Get hierarchical tree of all pages (useful for selecting parent page).

**Response:**
```json
{
  "wiki_id": 1,
  "wiki_name": "My Wiki",
  "pages": [
    {
      "id": 1,
      "title": "Home",
      "slug": "home",
      "children": [
        {
          "id": 2,
          "title": "Getting Started",
          "slug": "getting-started",
          "children": []
        }
      ]
    }
  ]
}
```

## Archive Structure Examples

### Example 1: Simple Hierarchy

```
my-wiki.zip
├── home.md
├── guide.md
└── guide/
    ├── installation.md
    └── configuration.md
```

**Result:**
- Home (root)
- Guide (root)
  - Installation (child of Guide)
  - Configuration (child of Guide)

### Example 2: Directory Without Markdown File

```
my-wiki.zip
├── README.md
└── tutorials/
    ├── basic.md
    └── advanced.md
```

**Result:**
- README (root)
- Tutorials (blank page created automatically)
  - Basic (child of Tutorials)
  - Advanced (child of Tutorials)

### Example 3: With Attachments

```
my-wiki.zip
├── documentation.md
└── documentation/
    ├── diagram.png
    ├── spec.pdf
    └── examples.md
```

**Result:**
- Documentation (root)
  - diagram.png (attachment)
  - spec.pdf (attachment)
  - Examples (child page)

### Example 4: With Frontmatter and Tags

```yaml
---
title: Custom Page Title
tags: [python, tutorial, beginner]
---

# First Heading

Content here...
```

**Result:**
- Page title: "Custom Page Title" (from frontmatter)
- Tags: python, tutorial, beginner
- Content: Everything after the frontmatter

## Frontend Integration

### Creating New Wiki from Archive

The Dashboard now includes a toggle between "Create Empty" and "Import Archive":

```jsx
// User selects "Import Archive" mode
// Uploads a .zip file
// Fills in wiki name and description
// Clicks "Import Wiki"
// Progress bar shows upload progress
// Results displayed with success/error details
```

### Importing to Existing Wiki

Wiki Settings page includes an "Import Pages from Archive" section:

```jsx
// User clicks "Import Archive" button
// Selects archive file
// Optionally selects parent page from tree
// Clicks "Import"
// Results displayed with detailed import report
```

## Error Handling

### Partial Success
If some files fail to import, the operation continues and reports:
- Number of successful imports
- Number of failures
- Detailed error log for each failed item

### Complete Failure
If all files fail during new wiki creation:
- Wiki is automatically deleted
- Error details returned to user
- No partial wiki left in database

### Common Errors
- **File too large**: Archive exceeds 500MB limit
- **Invalid format**: Not a .zip or .tar.gz file
- **Encoding issues**: Files not in UTF-8 (falls back to latin-1)
- **Invalid markdown**: Syntax errors in frontmatter YAML

## Implementation Details

### Backend Components

**Archive Import Service** (`app/services/archive_import.py`):
- `ArchiveImporter` class handles all import logic
- `ImportResult` tracks success/failure counts and details
- Supports zip and tar.gz extraction
- Recursive directory processing
- Frontmatter parsing with PyYAML
- H1 heading extraction
- Tag creation and assignment

**API Routes** (`app/routes/bulk_import.py`):
- `/api/wikis/import` - Create wiki from archive
- `/api/wikis/:id/import` - Import to existing wiki
- `/api/wikis/:id/pages/tree` - Get page hierarchy

**Models** (`app/models/models.py`):
- `Tag` model with wiki_id and name
- `page_tags` association table
- Many-to-many relationship between Page and Tag

### Frontend Components

**Dashboard** (`frontend/src/pages/Dashboard.jsx`):
- Import mode toggle
- Archive file upload with validation
- Upload progress indicator
- Import result display

**Wiki Settings** (`frontend/src/pages/WikiSettings.jsx`):
- Import section with archive upload
- Parent page selector (tree dropdown)
- Detailed import result modal

**API Service** (`frontend/src/services/api.js`):
- `wikisAPI.importArchive()` - Create new wiki
- `wikisAPI.importToExisting()` - Import to existing
- `wikisAPI.getPageTree()` - Get page hierarchy

## Database Migration

Run the migration to create Tag table and page_tags association:

```bash
flask db migrate -m "Add Tag model and page_tags for bulk import"
flask db upgrade
```

## Testing

### Create Sample Archive

```bash
python create_sample_archive.py
```

This creates `sample_wiki.zip` with:
- Multiple pages with frontmatter
- Nested directory structure
- Sample attachments
- Tag examples

### Test Import via API

```bash
# Create new wiki from archive
curl -X POST http://localhost:5000/api/wikis/import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "archive=@sample_wiki.zip" \
  -F "name=Test Wiki" \
  -F "description=Imported from sample archive" \
  -F "is_public=false"

# Import to existing wiki
curl -X POST http://localhost:5000/api/wikis/1/import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "archive=@sample_wiki.zip" \
  -F "parent_page_id=5"
```

### Test Import via UI

1. Go to Dashboard
2. Click "New Wiki"
3. Select "Import Archive" mode
4. Upload `sample_wiki.zip`
5. Fill in wiki name
6. Click "Import Wiki"
7. Review import results

## Best Practices

### Archive Preparation
- Use clear, descriptive filenames
- Organize content logically in directories
- Include frontmatter for important metadata
- Use UTF-8 encoding for all text files
- Keep archive size under 500MB

### Frontmatter Format
```yaml
---
title: Your Page Title
tags: [tag1, tag2, tag3]
---
```

### Directory Naming
- Use lowercase with hyphens: `getting-started/`
- Avoid special characters
- Match directory names to .md files for parent-child relationships

### Large Imports
- Split very large wikis into multiple archives
- Import incrementally using parent_page_id
- Test with small sample first

## Troubleshooting

**Upload fails with 413 error**
- Archive exceeds 500MB limit
- Solution: Split into smaller archives or compress more aggressively

**Pages missing after import**
- Check import result errors array
- Common cause: Invalid UTF-8 encoding
- Solution: Convert files to UTF-8

**Wrong page hierarchy**
- Directory names don't match .md filenames
- Solution: Ensure `page1.md` exists for `page1/` directory

**Tags not appearing**
- Frontmatter YAML syntax errors
- Solution: Validate YAML format

**Attachments not imported**
- Files in root directory (no parent page)
- Solution: Move attachments into page-specific directories

## Future Enhancements

- [ ] Support for more archive formats (.7z, .rar)
- [ ] Automatic image optimization during import
- [ ] Markdown link rewriting for internal references
- [ ] Export wiki to archive (reverse operation)
- [ ] Preview mode before final import
- [ ] Duplicate detection and merging options
- [ ] Custom import rules/transformations
- [ ] Background import for very large archives
- [ ] Import from Git repositories
- [ ] Import from other wiki platforms (MediaWiki, Confluence, etc.)
