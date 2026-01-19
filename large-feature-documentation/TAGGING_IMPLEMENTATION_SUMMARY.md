# Bulk Import Implementation Summary

## Overview
Implemented a comprehensive bulk import feature that allows users to create entire wiki structures from .zip or .tar.gz archive files. The feature supports both creating new wikis from archives and importing archives into existing wikis.

## Changes Made

### 1. Backend - Database Models (`app/models/models.py`)

**Added:**
- `Tag` model for organizing pages with tags
- `page_tags` association table for many-to-many relationship between pages and tags
- Added `tags` relationship to `Page` model
- Updated `Page.to_dict()` to include tags in serialization

**Tag Model Features:**
- Unique tag names per wiki
- Optional color field for tag styling
- Automatic creation from frontmatter

### 2. Backend - Archive Import Service (`app/services/archive_import.py`)

**New service that handles:**
- Archive extraction (zip, tar, tar.gz, tgz)
- Directory structure traversal and mapping to page hierarchy
- YAML frontmatter parsing for metadata (title, tags)
- H1 heading extraction as fallback title
- Automatic blank page creation for directories without matching .md files
- Non-markdown files imported as attachments
- Comprehensive error handling with partial success support
- File size validation (500MB max)
- UTF-8 and latin-1 encoding support

**Key Classes:**
- `ImportResult`: Tracks success/failure counts and details
- `ArchiveImporter`: Main import orchestration logic

### 3. Backend - API Routes (`app/routes/bulk_import.py`)

**New endpoints:**
- `POST /api/wikis/import` - Create new wiki from archive
- `POST /api/wikis/:id/import` - Import archive into existing wiki
- `GET /api/wikis/:id/pages/tree` - Get hierarchical page structure

**Features:**
- File upload with progress tracking
- Automatic wiki cleanup on complete failure
- Detailed import results with success/error breakdown
- Parent page selection for targeted imports

### 4. Backend - Configuration Updates

**Modified files:**
- `app/config.py`: Increased MAX_CONTENT_LENGTH to 500MB
- `app/__init__.py`: Registered bulk_import blueprint
- `app/routes/__init__.py`: Exported bulk_import_bp
- `requirements.txt`: Added PyYAML for frontmatter parsing

### 5. Frontend - API Client (`frontend/src/services/api.js`)

**Added methods:**
- `wikisAPI.importArchive()` - Create wiki from archive with upload progress
- `wikisAPI.importToExisting()` - Import to existing wiki
- `wikisAPI.getPageTree()` - Get hierarchical page tree

### 6. Frontend - Dashboard (`frontend/src/pages/Dashboard.jsx`)

**New features:**
- Import mode toggle (Create Empty vs Import Archive)
- Archive file upload with drag-and-drop support
- File type and size validation (500MB max)
- Upload progress bar
- Detailed import result display with success/error counts
- Error log viewer for failed imports

**UI Components:**
- Mode selector buttons
- File input with format validation
- Progress indicator during upload
- Results modal with expandable error details

### 7. Frontend - Wiki Settings (`frontend/src/pages/WikiSettings.jsx`)

**New features:**
- Import section for existing wikis
- Parent page selector (dropdown with tree structure)
- Archive upload modal
- Import progress tracking
- Detailed result display

**UI Components:**
- Import trigger button in settings
- Parent page tree dropdown
- Upload progress bar
- Import result modal with statistics

### 8. Documentation

**Created:**
- `BULK_IMPORT.md` - Comprehensive feature documentation including:
  - Feature overview and use cases
  - API endpoint details with examples
  - Archive structure examples
  - Frontend integration guide
  - Error handling documentation
  - Best practices and troubleshooting
  - Future enhancement ideas

**Updated:**
- `README.md` - Added bulk import to features, quick start, API endpoints, and project structure

**Created helper scripts:**
- `create_sample_archive.py` - Generates sample wiki archive for testing
- `create_migration.py` - Helper for creating database migration

## Feature Highlights

### Smart Page Creation
1. **Title Priority:**
   - YAML frontmatter `title` field (highest priority)
   - First H1 heading in content
   - Filename without extension (fallback)

2. **Hierarchy Mapping:**
   - Directory structure → Page hierarchy
   - `page1.md` + `page1/` directory → parent-child relationship
   - Directory without .md → blank page created automatically

3. **Tag Support:**
   - Parse tags from YAML frontmatter
   - Support list format: `[tag1, tag2]`
   - Support string format: `"tag1, tag2"`
   - Automatic tag creation per wiki

### Error Handling
- **Partial Success**: Continue processing even if some files fail
- **Detailed Reporting**: Track exactly which items succeeded/failed
- **Automatic Cleanup**: Delete wiki if all imports fail (new wiki creation)
- **User Feedback**: Show detailed error messages for each failed item

### Frontend UX
- **Progress Tracking**: Real-time upload progress indicator
- **Validation**: Client-side file type and size validation
- **Results Display**: Clear success/failure statistics
- **Error Details**: Expandable error log for troubleshooting

## File Structure Impact

```
wiki-app/
├── app/
│   ├── models/
│   │   └── models.py (modified - added Tag model, page_tags table)
│   ├── routes/
│   │   ├── __init__.py (modified - registered bulk_import_bp)
│   │   └── bulk_import.py (NEW)
│   ├── services/
│   │   └── archive_import.py (NEW)
│   ├── __init__.py (modified - registered blueprint)
│   └── config.py (modified - increased file size limit)
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx (modified - added import mode)
│   │   │   └── WikiSettings.jsx (modified - added import section)
│   │   └── services/
│   │       └── api.js (modified - added import methods)
├── requirements.txt (modified - added PyYAML)
├── create_sample_archive.py (NEW)
├── create_migration.py (NEW)
├── BULK_IMPORT.md (NEW)
└── README.md (modified - documented feature)
```

## Database Changes Required

Run migration to create:
- `tags` table with columns: id, name, wiki_id, color, created_at
- `page_tags` association table with columns: page_id, tag_id, created_at
- Unique constraint on (wiki_id, name) for tags
- Foreign key relationships

```bash
flask db migrate -m "Add Tag model and page_tags for bulk import"
flask db upgrade
```

## Testing Recommendations

1. **Create Sample Archive:**
   ```bash
   python create_sample_archive.py
   ```

2. **Test New Wiki Creation:**
   - Use Dashboard UI to upload sample_wiki.zip
   - Verify all pages created with correct hierarchy
   - Check tags are assigned
   - Verify attachments are linked

3. **Test Existing Wiki Import:**
   - Use Wiki Settings to import archive
   - Test with and without parent page selection
   - Verify pages nested correctly

4. **Test Error Handling:**
   - Upload invalid file format
   - Upload file > 500MB
   - Upload archive with invalid markdown
   - Verify partial success reporting

5. **Test API Directly:**
   ```bash
   curl -X POST http://localhost:5000/api/wikis/import \
     -H "Authorization: Bearer TOKEN" \
     -F "archive=@sample_wiki.zip" \
     -F "name=Test Wiki"
   ```

## Migration Path for Existing Deployments

1. **Backup database**
2. **Pull code changes**
3. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run database migration:**
   ```bash
   flask db migrate -m "Add tags and bulk import support"
   flask db upgrade
   ```
5. **Rebuild frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```
6. **Restart services**
7. **Test with sample archive**

## Performance Considerations

- **Large Archives**: 500MB limit prevents memory issues
- **Progress Tracking**: Provides user feedback during long uploads
- **Atomic Operations**: Database rollback on complete failure
- **Background Processing**: Could be added for very large archives (future enhancement)

## Security Considerations

- **File Validation**: Strict file type checking
- **Size Limits**: 500MB max to prevent DoS
- **Path Traversal**: Archive extraction contained to temp directory
- **Authentication**: All endpoints require JWT token
- **Authorization**: Edit permissions checked for existing wiki imports

## Future Enhancements

As documented in BULK_IMPORT.md:
- Export wiki to archive (reverse operation)
- Support for more archive formats
- Preview before import
- Markdown link rewriting
- Import from Git repositories
- Import from other wiki platforms
