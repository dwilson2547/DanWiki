# Phase 1: Core Export (Week 1)

## Overview

**Priority: HIGH - Foundation for all other features**

This phase establishes the fundamental export functionality, creating a reliable system for backing up entire wikis to archive files. The focus is on data integrity, maintaining the import-compatible structure, and ensuring all content (pages and attachments) is preserved correctly.

## Goals

- Implement core `WikiExporter` class with basic export logic
- Create `.danwiki-backup` marker file for identifying restorable backups
- Export all pages with proper YAML frontmatter
- Maintain hierarchical directory structure compatible with import
- Export all attachments to correct locations
- Support both ZIP and TAR.GZ archive formats
- Create export API endpoint with authentication
- Implement file streaming for efficient downloads

## Timeline

**Duration:** 5 days (Days 1-5 of implementation)

### Day 1-2: Backend Core
- Create `WikiExporter` base class
- Implement basic export logic
- Add `.danwiki-backup` marker file generation
- Implement page hierarchy traversal
- Write pages with frontmatter

### Day 3: Attachment Handling
- Implement attachment discovery
- Copy attachments to correct directories
- Maintain import-compatible structure

### Day 4: Archive Creation
- Implement ZIP creation
- Implement TAR.GZ creation
- Add file streaming for large archives

### Day 5: API Route
- Create export endpoint
- Add authentication/authorization
- Implement file download response

## Technical Implementation

### File Structure

```
app/
├── services/
│   └── archive_export.py          # WikiExporter class
└── routes/
    └── bulk_export.py             # Export API endpoint
```

### Core Classes

```python
# app/services/archive_export.py

@dataclass
class ExportOptions:
    """Configuration for export operation"""
    format: str = 'zip'  # 'zip' or 'tar.gz'
    include_attachments: bool = True
    profile: Optional[str] = None
    preserve_metadata: bool = True
    add_backup_marker: bool = True

@dataclass
class ExportResult:
    """Result of export operation"""
    success: bool
    archive_path: str
    page_count: int
    attachment_count: int
    size_bytes: int
    errors: List[Dict[str, str]]
    metadata: Dict[str, Any]

class WikiExporter:
    """Main exporter class"""
    
    def __init__(self, wiki_id: int, options: ExportOptions = None):
        self.wiki_id = wiki_id
        self.options = options or ExportOptions()
        
    def export(self) -> ExportResult:
        """Execute export operation"""
        # Main export logic
        
    def _add_backup_marker(self, temp_dir: Path):
        """Add .danwiki-backup marker file"""
        
    def _process_page(self, page, temp_dir: Path):
        """Process and write single page"""
        
    def _process_attachments(self, pages: List, temp_dir: Path):
        """Process and copy all attachments"""
        
    def _get_page_path(self, page) -> Path:
        """Get file path for page based on hierarchy"""
        
    def _build_frontmatter(self, page) -> str:
        """Build YAML frontmatter for page"""
        
    def _copy_attachment(self, attachment, page, temp_dir: Path):
        """Copy attachment to appropriate directory"""
        
    def _create_archive(self, temp_dir: Path) -> str:
        """Create archive from temporary directory"""
        
    def _create_zip(self, temp_dir: Path, archive_name: str) -> str:
        """Create ZIP archive"""
        
    def _create_targz(self, temp_dir: Path, archive_name: str) -> str:
        """Create TAR.GZ archive"""
```

### API Endpoint

```python
# app/routes/bulk_export.py

@bp.route('/api/wikis/<int:wiki_id>/export', methods=['POST'])
@jwt_required()
def export_wiki(wiki_id):
    """
    Export wiki to archive file
    
    Request JSON:
    {
        "format": "zip",  # or "tar.gz"
        "include_attachments": true
    }
    
    Response: Binary file download with headers:
    - Content-Type: application/zip or application/gzip
    - Content-Disposition: attachment; filename="wiki_backup_20260124.zip"
    """
    # Verify user owns wiki
    # Create exporter
    # Execute export
    # Stream file response
```

### Backup Marker Format

```json
{
  "version": "1.0",
  "created_at": "2026-01-24T10:30:00Z",
  "wiki_id": 123,
  "wiki_name": "My Wiki",
  "wiki_slug": "my-wiki",
  "export_profile": "backup",
  "format_version": "1.0",
  "page_count": 45,
  "attachment_count": 23,
  "tags_included": true,
  "metadata_preserved": true,
  "exporter_version": "1.0.0"
}
```

### Frontmatter Format

```yaml
---
title: Page Title
slug: page-slug
tags: [python, tutorial]

# Backup-specific metadata
danwiki_id: 456
parent_id: 123
created_at: '2026-01-01T00:00:00Z'
updated_at: '2026-01-24T10:30:00Z'
order: 5
---

Page content here...
```

### Directory Structure Example

```
wiki_backup_20260124.zip
├── .danwiki-backup              # Marker file
├── home.md                      # Root page
├── guide.md                     # Root page
├── guide/                       # Children of guide.md
│   ├── installation.md
│   ├── configuration.md
│   └── installation/            # Attachments for installation.md
│       ├── screenshot.png
│       └── diagram.pdf
└── tutorials/
    ├── basic.md
    └── advanced.md
```

## Security Considerations

1. **Authorization**
   - Verify user owns wiki before export
   - Check wiki permissions (respect private wikis)
   - No export of wikis user doesn't have access to

2. **Resource Limits**
   - Maximum archive size: 2GB
   - Timeout: 5 minutes for export
   - Rate limiting: 3 exports per user per hour

3. **File Safety**
   - Sanitize all filenames (remove path traversal attempts)
   - Validate file extensions
   - Prevent symlink attacks

4. **Cleanup**
   - Remove temporary directories after successful export
   - Remove temporary directories on error
   - Scheduled cleanup of abandoned temp files (older than 1 hour)

## Error Handling

```python
class ExportError(Exception):
    """Base exception for export errors"""
    pass

class ExportTimeoutError(ExportError):
    """Export took too long"""
    pass

class ExportSizeLimitError(ExportError):
    """Archive exceeds size limit"""
    pass

class ExportPermissionError(ExportError):
    """User lacks permission to export"""
    pass

# HTTP status codes
# 200: Success (file download)
# 403: Permission denied
# 408: Timeout
# 413: Archive too large
# 500: Server error
```

## Testing Requirements

### Unit Tests

```python
# tests/services/test_archive_export.py

class TestWikiExporter:
    def test_basic_export(self):
        """Test basic wiki export with single page"""
        
    def test_export_empty_wiki(self):
        """Test export of wiki with no pages"""
        
    def test_backup_marker_creation(self):
        """Verify .danwiki-backup file is created correctly"""
        
    def test_page_hierarchy_preservation(self):
        """Verify directory structure matches page hierarchy"""
        
    def test_frontmatter_generation(self):
        """Test YAML frontmatter is correct"""
        
    def test_attachment_export(self):
        """Test attachments exported to correct locations"""
        
    def test_zip_creation(self):
        """Test ZIP archive is created and valid"""
        
    def test_targz_creation(self):
        """Test TAR.GZ archive is created and valid"""
        
    def test_filename_sanitization(self):
        """Test malicious filenames are sanitized"""
        
    def test_large_wiki_export(self):
        """Test export of wiki with 100+ pages"""
```

### Integration Tests

```python
# tests/routes/test_bulk_export.py

class TestExportAPI:
    def test_export_endpoint_success(self):
        """Test successful export via API"""
        
    def test_export_unauthorized(self):
        """Test export fails without authentication"""
        
    def test_export_wrong_owner(self):
        """Test user cannot export another user's wiki"""
        
    def test_export_file_download(self):
        """Test file downloads correctly"""
        
    def test_export_format_zip(self):
        """Test ZIP format selection"""
        
    def test_export_format_targz(self):
        """Test TAR.GZ format selection"""
        
    def test_export_without_attachments(self):
        """Test export with attachments disabled"""
```

### Manual Testing

- [ ] Export empty wiki
- [ ] Export wiki with single root page
- [ ] Export wiki with nested hierarchy (3+ levels)
- [ ] Export wiki with 50+ pages
- [ ] Export wiki with various attachment types
- [ ] Export wiki with tags
- [ ] Export as ZIP format
- [ ] Export as TAR.GZ format
- [ ] Export without attachments
- [ ] Verify .danwiki-backup marker is present
- [ ] Verify frontmatter preserves all metadata
- [ ] Verify directory structure matches hierarchy
- [ ] Test download in Chrome
- [ ] Test download in Firefox
- [ ] Test download in Safari

## Success Criteria

- ✓ Can export any wiki to ZIP or TAR.GZ format
- ✓ All pages exported with correct frontmatter
- ✓ Page hierarchy preserved in directory structure
- ✓ All attachments exported to correct locations
- ✓ Backup marker file created correctly
- ✓ File downloads work in all major browsers
- ✓ Export completes in <10 seconds for wikis with <100 pages
- ✓ All unit tests pass
- ✓ All integration tests pass
- ✓ No security vulnerabilities in file handling
- ✓ Proper cleanup of temporary files

## Dependencies

- PyYAML: YAML frontmatter generation
- zipfile (stdlib): ZIP archive creation
- tarfile (stdlib): TAR.GZ archive creation
- shutil (stdlib): File operations
- tempfile (stdlib): Temporary directory management

## Blockers & Risks

**Potential Blockers:**
- Large attachment files causing memory issues
- Complex page hierarchies causing path length issues
- Special characters in filenames breaking archive

**Mitigation:**
- Stream files instead of loading into memory
- Implement path length validation
- Aggressive filename sanitization

## Deliverables

1. **Code:**
   - `app/services/archive_export.py` - Exporter implementation
   - `app/routes/bulk_export.py` - API endpoint
   
2. **Tests:**
   - Unit tests for WikiExporter
   - Integration tests for API endpoint
   
3. **Documentation:**
   - API documentation for export endpoint
   - Code comments explaining key algorithms
   
4. **Validation:**
   - Manual test report
   - Performance benchmarks

## Next Phase

After Phase 1 completion, proceed to **Phase 2: Frontend Integration** to build the user interface for triggering exports.

---

## Progress Tracking

### Feature 1: WikiExporter Core Class
- [ ] Create `app/services/archive_export.py` file
- [ ] Implement `ExportOptions` dataclass
- [ ] Implement `ExportResult` dataclass
- [ ] Create `WikiExporter` class with `__init__`
- [ ] Implement `export()` main method
- [ ] Implement `_load_wiki()` helper
- [ ] Implement `_load_pages()` helper
- [ ] Implement `_create_temp_directory()` helper
- [ ] Implement `_cleanup()` helper
- [ ] Implement `_calculate_stats()` helper
- [ ] Add error handling to export method
- [ ] Add logging throughout export process

### Feature 2: Backup Marker System
- [ ] Design `.danwiki-backup` JSON schema
- [ ] Implement `_add_backup_marker()` method
- [ ] Include wiki metadata in marker
- [ ] Include export timestamp
- [ ] Include page/attachment counts
- [ ] Test marker file creation
- [ ] Validate marker JSON structure

### Feature 3: Page Processing & Hierarchy
- [ ] Implement `_get_page_path()` method
- [ ] Implement hierarchical path building logic
- [ ] Implement filename sanitization
- [ ] Handle special characters in slugs
- [ ] Test path generation for nested pages
- [ ] Test path generation for root pages
- [ ] Validate path length limits

### Feature 4: Frontmatter Generation
- [ ] Implement `_build_frontmatter()` method
- [ ] Include title and slug in frontmatter
- [ ] Include tags in frontmatter
- [ ] Include backup metadata (ID, timestamps)
- [ ] Include parent_id when present
- [ ] Generate valid YAML syntax
- [ ] Test frontmatter with special characters
- [ ] Test frontmatter with various tag formats

### Feature 5: Page Content Export
- [ ] Implement `_process_page()` method
- [ ] Create parent directories as needed
- [ ] Write frontmatter to file
- [ ] Write page content to file
- [ ] Use UTF-8 encoding
- [ ] Test with empty pages
- [ ] Test with large pages (>1MB)
- [ ] Test with various markdown syntax

### Feature 6: Attachment Processing
- [ ] Implement `_process_attachments()` method
- [ ] Implement `_get_page_attachments()` helper
- [ ] Implement `_copy_attachment()` method
- [ ] Create attachment subdirectories
- [ ] Copy files preserving metadata
- [ ] Handle missing attachment files
- [ ] Test with various file types
- [ ] Test with large attachments (>100MB)
- [ ] Test with 0-byte files

### Feature 7: Archive Creation (ZIP)
- [ ] Implement `_create_zip()` method
- [ ] Create ZIP archive from directory
- [ ] Set appropriate compression level
- [ ] Generate filename with timestamp
- [ ] Test ZIP file validity
- [ ] Test ZIP extraction
- [ ] Test with large archives (>500MB)
- [ ] Verify file permissions preserved

### Feature 8: Archive Creation (TAR.GZ)
- [ ] Implement `_create_targz()` method
- [ ] Create TAR.GZ archive from directory
- [ ] Set appropriate compression level
- [ ] Generate filename with timestamp
- [ ] Test TAR.GZ file validity
- [ ] Test TAR.GZ extraction
- [ ] Test with large archives (>500MB)
- [ ] Verify file permissions preserved

### Feature 9: Export API Endpoint
- [ ] Create `app/routes/bulk_export.py` file
- [ ] Create Flask blueprint for export routes
- [ ] Implement POST `/api/wikis/<id>/export` endpoint
- [ ] Add JWT authentication requirement
- [ ] Parse request JSON (format, include_attachments)
- [ ] Validate request parameters
- [ ] Verify user owns wiki
- [ ] Check wiki permissions
- [ ] Create WikiExporter instance
- [ ] Execute export operation
- [ ] Handle export errors
- [ ] Return appropriate HTTP status codes

### Feature 10: File Download Response
- [ ] Implement file streaming response
- [ ] Set Content-Type header (application/zip or gzip)
- [ ] Set Content-Disposition header with filename
- [ ] Set Content-Length header
- [ ] Stream file in chunks
- [ ] Clean up file after download
- [ ] Test download in curl
- [ ] Test download in browser
- [ ] Test download interruption handling

### Feature 11: Security & Validation
- [ ] Implement authorization checks
- [ ] Implement rate limiting
- [ ] Implement maximum archive size check
- [ ] Implement export timeout
- [ ] Sanitize all user-provided filenames
- [ ] Validate file paths (no path traversal)
- [ ] Test with malicious inputs
- [ ] Security audit of file handling

### Feature 12: Error Handling
- [ ] Create `ExportError` exception class
- [ ] Create `ExportTimeoutError` exception
- [ ] Create `ExportSizeLimitError` exception
- [ ] Create `ExportPermissionError` exception
- [ ] Add try-catch blocks throughout
- [ ] Log all errors with details
- [ ] Return user-friendly error messages
- [ ] Test all error scenarios

### Feature 13: Testing
- [ ] Write unit test: test_basic_export
- [ ] Write unit test: test_export_empty_wiki
- [ ] Write unit test: test_backup_marker_creation
- [ ] Write unit test: test_page_hierarchy_preservation
- [ ] Write unit test: test_frontmatter_generation
- [ ] Write unit test: test_attachment_export
- [ ] Write unit test: test_zip_creation
- [ ] Write unit test: test_targz_creation
- [ ] Write unit test: test_filename_sanitization
- [ ] Write unit test: test_large_wiki_export
- [ ] Write integration test: test_export_endpoint_success
- [ ] Write integration test: test_export_unauthorized
- [ ] Write integration test: test_export_wrong_owner
- [ ] Write integration test: test_export_file_download
- [ ] Write integration test: test_export_format_zip
- [ ] Write integration test: test_export_format_targz
- [ ] Run all tests and verify passing
- [ ] Measure test coverage (target: >90%)

### Feature 14: Documentation
- [ ] Document WikiExporter class
- [ ] Document all public methods
- [ ] Document ExportOptions parameters
- [ ] Document ExportResult fields
- [ ] Document API endpoint in API docs
- [ ] Document backup marker format
- [ ] Document frontmatter format
- [ ] Add code examples
- [ ] Document error codes

### Feature 15: Performance & Optimization
- [ ] Benchmark small wiki export (<10 pages)
- [ ] Benchmark medium wiki export (~50 pages)
- [ ] Benchmark large wiki export (~200 pages)
- [ ] Profile memory usage
- [ ] Optimize file I/O operations
- [ ] Implement streaming where possible
- [ ] Test concurrent exports
- [ ] Monitor temporary disk usage
