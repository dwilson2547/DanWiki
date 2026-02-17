# Wiki Export & Backup Feature - Implementation Plan

## Overview

The export feature enables backing up entire wikis to archive files (.zip or .tar.gz) that can be reimported without data loss or link breakage. This feature is designed with extensibility in mind to support future export profiles for different platforms (GitHub, VS Code, etc.).

## Core Requirements

### Phase 1: Basic Export (MVP)
- Export wiki to archive maintaining import-compatible structure
- Include metadata marker indicating backup vs. fresh export
- Export all pages with frontmatter preservation
- Export all attachments in correct directory structure
- Add export button to wiki settings page
- Support .zip and .tar.gz formats

### Phase 2: Advanced Features (Future)
- Export profiles (GitHub, VS Code, Obsidian, etc.)
- Link and attachment path rewriting
- Wiki restructuring options
- Markdown flavor transformations
- Plugin system for custom export operations
- Selective export (specific pages/branches)

## Architecture Design

### Class Structure

```python
# app/services/archive_export.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class ExportOptions:
    """Configuration for export operation"""
    format: str = 'zip'  # 'zip' or 'tar.gz'
    include_attachments: bool = True
    profile: Optional[str] = None  # None, 'github', 'vscode', etc.
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

class ExportPlugin(ABC):
    """Base class for export plugins"""
    
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier"""
        pass
    
    @abstractmethod
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform page data before export"""
        pass
    
    @abstractmethod
    def process_archive(self, archive_path: Path) -> None:
        """Post-process entire archive"""
        pass

class ExportProfile(ABC):
    """Base class for export profiles"""
    
    @abstractmethod
    def name(self) -> str:
        """Profile identifier"""
        pass
    
    @abstractmethod
    def get_options(self) -> ExportOptions:
        """Get profile-specific options"""
        pass
    
    @abstractmethod
    def get_plugins(self) -> List[ExportPlugin]:
        """Get plugins to apply for this profile"""
        pass
    
    @abstractmethod
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Transform markdown content"""
        pass
    
    @abstractmethod
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Define custom directory structure"""
        pass

class BackupProfile(ExportProfile):
    """Profile for creating restorable backups"""
    
    def name(self) -> str:
        return "backup"
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='backup',
            preserve_metadata=True,
            add_backup_marker=True
        )
    
    def get_plugins(self) -> List[ExportPlugin]:
        return []  # No transformations for backups
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        return content  # No changes for backups
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        # Use standard import-compatible structure
        return self._build_hierarchy(pages)

class WikiExporter:
    """Main exporter class"""
    
    def __init__(self, wiki_id: int, options: ExportOptions = None):
        self.wiki_id = wiki_id
        self.options = options or ExportOptions()
        self.profile: Optional[ExportProfile] = None
        self.plugins: List[ExportPlugin] = []
        
    def set_profile(self, profile: ExportProfile):
        """Set export profile"""
        self.profile = profile
        self.options = profile.get_options()
        self.plugins = profile.get_plugins()
        
    def add_plugin(self, plugin: ExportPlugin):
        """Add custom plugin"""
        self.plugins.append(plugin)
        
    def export(self) -> ExportResult:
        """Execute export operation"""
        try:
            # Load wiki and pages
            wiki = self._load_wiki()
            pages = self._load_pages()
            
            # Create temporary directory
            temp_dir = self._create_temp_directory()
            
            # Add backup marker if requested
            if self.options.add_backup_marker:
                self._add_backup_marker(temp_dir)
            
            # Process pages
            for page in pages:
                self._process_page(page, temp_dir)
            
            # Process attachments
            if self.options.include_attachments:
                self._process_attachments(pages, temp_dir)
            
            # Apply plugins
            for plugin in self.plugins:
                plugin.process_archive(temp_dir)
            
            # Create archive
            archive_path = self._create_archive(temp_dir)
            
            # Calculate stats
            stats = self._calculate_stats(archive_path, pages)
            
            # Cleanup
            self._cleanup(temp_dir)
            
            return ExportResult(
                success=True,
                archive_path=archive_path,
                page_count=stats['pages'],
                attachment_count=stats['attachments'],
                size_bytes=stats['size'],
                errors=[],
                metadata=self._build_metadata(wiki)
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                archive_path='',
                page_count=0,
                attachment_count=0,
                size_bytes=0,
                errors=[{'error': str(e)}],
                metadata={}
            )
    
    def _add_backup_marker(self, temp_dir: Path):
        """Add .danwiki-backup marker file"""
        marker_path = temp_dir / '.danwiki-backup'
        metadata = {
            'version': '1.0',
            'created_at': datetime.utcnow().isoformat(),
            'wiki_id': self.wiki_id,
            'export_profile': self.options.profile or 'backup',
            'format_version': '1.0'
        }
        with open(marker_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _process_page(self, page, temp_dir: Path):
        """Process and write single page"""
        # Get page path based on hierarchy
        page_path = self._get_page_path(page)
        full_path = temp_dir / page_path
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build frontmatter
        frontmatter = self._build_frontmatter(page)
        
        # Get content
        content = page.content or ''
        
        # Apply profile transformations
        if self.profile:
            content = self.profile.transform_content(content, self._page_to_dict(page))
        
        # Apply plugin transformations
        for plugin in self.plugins:
            page_data = self._page_to_dict(page)
            page_data = plugin.process_page(page_data)
            content = page_data.get('content', content)
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            if frontmatter:
                f.write('---\n')
                f.write(frontmatter)
                f.write('---\n\n')
            f.write(content)
    
    def _process_attachments(self, pages: List, temp_dir: Path):
        """Process and copy all attachments"""
        for page in pages:
            attachments = self._get_page_attachments(page)
            for attachment in attachments:
                self._copy_attachment(attachment, page, temp_dir)
    
    def _get_page_path(self, page) -> Path:
        """Get file path for page based on hierarchy"""
        # Build path from root to current page
        path_parts = []
        current = page
        
        while current:
            # Sanitize slug for filesystem
            safe_slug = self._sanitize_filename(current.slug)
            path_parts.insert(0, safe_slug)
            current = current.parent
        
        # Last part gets .md extension
        if path_parts:
            path_parts[-1] = f"{path_parts[-1]}.md"
        
        return Path(*path_parts)
    
    def _build_frontmatter(self, page) -> str:
        """Build YAML frontmatter for page"""
        metadata = {
            'title': page.title,
            'slug': page.slug,
        }
        
        # Add tags if present
        if hasattr(page, 'tags') and page.tags:
            metadata['tags'] = [tag.name for tag in page.tags]
        
        # Add backup-specific metadata if in backup mode
        if self.options.add_backup_marker:
            metadata['danwiki_id'] = page.id
            metadata['created_at'] = page.created_at.isoformat()
            metadata['updated_at'] = page.updated_at.isoformat()
            if page.parent_id:
                metadata['parent_id'] = page.parent_id
        
        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    def _copy_attachment(self, attachment, page, temp_dir: Path):
        """Copy attachment to appropriate directory"""
        # Get page directory (without .md extension)
        page_path = self._get_page_path(page)
        page_dir = page_path.parent / page_path.stem
        
        # Create attachment directory
        attachment_dir = temp_dir / page_dir
        attachment_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        src_path = Path(attachment.file_path)
        dst_path = attachment_dir / attachment.filename
        
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
    
    def _create_archive(self, temp_dir: Path) -> str:
        """Create archive from temporary directory"""
        # Generate archive filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        wiki_slug = self._get_wiki_slug()
        
        if self.options.format == 'zip':
            archive_name = f"{wiki_slug}_backup_{timestamp}.zip"
            archive_path = self._create_zip(temp_dir, archive_name)
        else:
            archive_name = f"{wiki_slug}_backup_{timestamp}.tar.gz"
            archive_path = self._create_targz(temp_dir, archive_name)
        
        return archive_path
```

## API Design

### Export Endpoint

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
        "profile": "backup",  # or null for default
        "include_attachments": true,
        "options": {}  # Profile-specific options
    }
    
    Response: Binary file download
    """
    
@bp.route('/api/wikis/<int:wiki_id>/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(wiki_id, task_id):
    """
    Check status of ongoing export (for large wikis)
    
    Response:
    {
        "status": "processing|completed|failed",
        "progress": 0-100,
        "message": "Processing page 45 of 100",
        "download_url": "/api/download/<token>"  # When completed
    }
    """

@bp.route('/api/wikis/profiles', methods=['GET'])
def get_export_profiles():
    """
    Get available export profiles
    
    Response:
    {
        "profiles": [
            {
                "name": "backup",
                "display_name": "Backup (Restorable)",
                "description": "Full backup that can be restored without data loss",
                "supports_attachments": true,
                "supports_tags": true
            },
            {
                "name": "github",
                "display_name": "GitHub Wiki",
                "description": "Export formatted for GitHub Wiki",
                "supports_attachments": true,
                "supports_tags": false
            }
        ]
    }
    """
```

## Database Considerations

### No Schema Changes Required
The export feature is read-only and doesn't require database modifications. However, we may want to add:

```python
# Optional: Track export history
class ExportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey('wiki.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile = db.Column(db.String(50))
    format = db.Column(db.String(10))
    size_bytes = db.Column(db.Integer)
    page_count = db.Column(db.Integer)
    attachment_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))  # 'completed', 'failed'
```

## Frontend Integration

### Wiki Settings Page Updates

```jsx
// frontend/src/pages/WikiSettings.jsx

function WikiSettings() {
  const [exportFormat, setExportFormat] = useState('zip');
  const [exportProfile, setExportProfile] = useState('backup');
  const [includeAttachments, setIncludeAttachments] = useState(true);
  const [exportProgress, setExportProgress] = useState(null);
  
  const handleExport = async () => {
    try {
      setExportProgress({ status: 'preparing', progress: 0 });
      
      const response = await wikisAPI.exportWiki(wikiId, {
        format: exportFormat,
        profile: exportProfile,
        include_attachments: includeAttachments
      });
      
      // For small wikis: direct download
      if (response.type === 'blob') {
        downloadFile(response, `${wikiSlug}_backup.${exportFormat}`);
        setExportProgress({ status: 'completed', progress: 100 });
      }
      
      // For large wikis: poll for status
      if (response.task_id) {
        pollExportStatus(response.task_id);
      }
      
    } catch (error) {
      setExportProgress({ status: 'failed', error: error.message });
    }
  };
  
  return (
    <div className="wiki-settings">
      {/* ... existing settings ... */}
      
      <section className="export-section">
        <h2>Export & Backup</h2>
        
        <div className="export-options">
          <div className="form-group">
            <label>Export Format</label>
            <select value={exportFormat} onChange={e => setExportFormat(e.target.value)}>
              <option value="zip">ZIP Archive</option>
              <option value="tar.gz">TAR.GZ Archive</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Export Profile</label>
            <select value={exportProfile} onChange={e => setExportProfile(e.target.value)}>
              <option value="backup">Backup (Restorable)</option>
              <option value="plain">Plain Markdown</option>
              {/* Future: GitHub, VS Code, etc. */}
            </select>
            <p className="help-text">
              Backup profile preserves all metadata for perfect restoration
            </p>
          </div>
          
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={includeAttachments}
                onChange={e => setIncludeAttachments(e.target.checked)}
              />
              Include Attachments
            </label>
          </div>
          
          <button 
            onClick={handleExport}
            disabled={exportProgress?.status === 'preparing'}
            className="btn-primary"
          >
            {exportProgress?.status === 'preparing' ? 'Exporting...' : 'Export Wiki'}
          </button>
          
          {exportProgress && (
            <ExportProgress progress={exportProgress} />
          )}
        </div>
      </section>
    </div>
  );
}
```

### API Service

```javascript
// frontend/src/services/api.js

export const wikisAPI = {
  // ... existing methods ...
  
  exportWiki: async (wikiId, options) => {
    const response = await apiClient.post(
      `/wikis/${wikiId}/export`,
      options,
      { responseType: 'blob' }  // For file download
    );
    return response.data;
  },
  
  getExportStatus: async (wikiId, taskId) => {
    const response = await apiClient.get(
      `/wikis/${wikiId}/export/status/${taskId}`
    );
    return response.data;
  },
  
  getExportProfiles: async () => {
    const response = await apiClient.get('/wikis/profiles');
    return response.data;
  }
};
```

## File Structure

```
app/
├── services/
│   ├── archive_export.py          # Main exporter classes
│   ├── export_profiles/
│   │   ├── __init__.py
│   │   ├── backup.py              # Backup profile
│   │   ├── plain.py               # Plain markdown profile
│   │   └── github.py              # GitHub profile (future)
│   └── export_plugins/
│       ├── __init__.py
│       ├── sidebar_generator.py   # Sidebar plugin
│       └── link_rewriter.py       # Link rewriting plugin
├── routes/
│   └── bulk_export.py             # Export API routes
└── models/
    └── export_history.py          # Export tracking (optional)

frontend/
├── src/
│   ├── pages/
│   │   └── WikiSettings.jsx       # Updated with export UI
│   ├── components/
│   │   ├── ExportProgress.jsx     # Progress indicator
│   │   └── ExportOptionsModal.jsx # Advanced options
│   └── services/
│       └── api.js                 # Export API calls
```

## Implementation Phases

### Phase 1: Core Export (Week 1)
**Priority: HIGH - Foundation for all other features**

1. **Day 1-2: Backend Core**
   - Create `WikiExporter` base class
   - Implement basic export logic
   - Add `.danwiki-backup` marker file generation
   - Implement page hierarchy traversal
   - Write pages with frontmatter

2. **Day 3: Attachment Handling**
   - Implement attachment discovery
   - Copy attachments to correct directories
   - Maintain import-compatible structure

3. **Day 4: Archive Creation**
   - Implement ZIP creation
   - Implement TAR.GZ creation
   - Add file streaming for large archives

4. **Day 5: API Route**
   - Create export endpoint
   - Add authentication/authorization
   - Implement file download response

### Phase 2: Frontend Integration (Week 1-2)
**Priority: HIGH - User-facing functionality**

5. **Day 6: Settings UI**
   - Add export section to WikiSettings
   - Create format selector
   - Add export button
   - Implement file download

6. **Day 7: Progress & Error Handling**
   - Add progress indicator
   - Implement error display
   - Add success notifications

### Phase 3: Profile System (Week 2)
**Priority: MEDIUM - Extensibility foundation**

7. **Day 8-9: Profile Architecture**
   - Create `ExportProfile` base class
   - Implement `BackupProfile`
   - Create profile registry
   - Add profile selection to API

8. **Day 10: Plain Markdown Profile**
   - Implement basic transformation profile
   - Strip backup-specific metadata
   - Test with various markdown renderers

### Phase 4: Plugin System (Week 3)
**Priority: MEDIUM - Advanced features**

9. **Day 11-12: Plugin Framework**
   - Create `ExportPlugin` base class
   - Implement plugin loading system
   - Add plugin execution pipeline
   - Create plugin configuration system

10. **Day 13: Sample Plugins**
    - Create sidebar generator plugin
    - Create link rewriter plugin
    - Document plugin development

### Phase 5: Advanced Profiles (Week 4+)
**Priority: LOW - Nice to have**

11. **Future: GitHub Profile**
    - GitHub-flavored markdown
    - Sidebar generation
    - Image optimization
    - Wiki-specific formatting

12. **Future: VS Code Profile**
    - VS Code markdown preview compatible
    - Workspace settings generation
    - Extension recommendations

## Testing Strategy

### Unit Tests

```python
# tests/test_export.py

class TestWikiExporter:
    def test_basic_export(self):
        """Test basic wiki export"""
        
    def test_backup_marker_creation(self):
        """Test .danwiki-backup file creation"""
        
    def test_page_hierarchy_preservation(self):
        """Test directory structure matches hierarchy"""
        
    def test_attachment_export(self):
        """Test attachments exported to correct locations"""
        
    def test_frontmatter_generation(self):
        """Test YAML frontmatter correctness"""
        
    def test_zip_creation(self):
        """Test ZIP archive creation"""
        
    def test_targz_creation(self):
        """Test TAR.GZ archive creation"""

class TestExportProfiles:
    def test_backup_profile(self):
        """Test backup profile preserves all data"""
        
    def test_plain_profile(self):
        """Test plain profile strips metadata"""

class TestExportPlugins:
    def test_plugin_execution_order(self):
        """Test plugins execute in correct order"""
        
    def test_sidebar_generator(self):
        """Test sidebar generation plugin"""
```

### Integration Tests

```python
class TestExportAPI:
    def test_export_endpoint(self):
        """Test export API endpoint"""
        
    def test_export_authorization(self):
        """Test user can only export their wikis"""
        
    def test_export_download(self):
        """Test file download works"""
        
    def test_roundtrip_export_import(self):
        """Test export then import preserves data"""
```

### Manual Testing Checklist

- [ ] Export empty wiki
- [ ] Export wiki with single page
- [ ] Export wiki with nested hierarchy
- [ ] Export wiki with attachments
- [ ] Export wiki with tags
- [ ] Export large wiki (>100 pages)
- [ ] Export then import (verify data integrity)
- [ ] Export with different formats (zip, tar.gz)
- [ ] Export with different profiles
- [ ] Test file download in browser
- [ ] Test with slow network
- [ ] Test concurrent exports

## Backup Marker Format

### .danwiki-backup File

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

### Enhanced Frontmatter for Backups

```yaml
---
title: Page Title
slug: page-slug
tags: [python, tutorial]

# Backup-specific metadata (only in backup profile)
danwiki_id: 456
parent_id: 123
created_at: '2026-01-01T00:00:00Z'
updated_at: '2026-01-24T10:30:00Z'
order: 5
---

Page content here...
```

## Security Considerations

1. **Authorization**
   - Verify user owns wiki before export
   - Check wiki permissions (private wikis)
   - Rate limit export requests

2. **Resource Limits**
   - Maximum archive size (e.g., 2GB)
   - Timeout for large exports
   - Concurrent export limit per user

3. **File Safety**
   - Sanitize filenames
   - Prevent path traversal
   - Validate file types

4. **Temporary File Cleanup**
   - Automatic cleanup on success
   - Cleanup on error
   - Scheduled cleanup of old temp files

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

# Usage in exporter
try:
    result = exporter.export()
except ExportSizeLimitError:
    return {'error': 'Wiki too large to export'}, 413
except ExportTimeoutError:
    return {'error': 'Export timed out, try with fewer pages'}, 408
except ExportPermissionError:
    return {'error': 'Permission denied'}, 403
except ExportError as e:
    return {'error': str(e)}, 500
```

## Performance Optimization

1. **Streaming**
   - Stream archive creation (don't load entire archive in memory)
   - Use generators for page iteration

2. **Caching**
   - Cache page hierarchy queries
   - Batch load attachments

3. **Async Processing**
   - Queue large exports for background processing
   - Send email notification when complete

4. **Compression**
   - Use optimal compression level (balance speed vs size)
   - Consider parallel compression for multi-file archives

## Future Enhancements

### Export Profiles

**GitHub Profile**
- Generate `_Sidebar.md` with page hierarchy
- Convert internal links to GitHub wiki format
- Optimize images for GitHub
- Add `_Footer.md` with navigation

**VS Code Profile**
- Generate workspace settings
- Create task definitions for common operations
- Include recommended extensions list
- Format for VS Code markdown preview

**Obsidian Profile**
- Use wikilink syntax `[[Page Name]]`
- Generate graph view metadata
- Create folder structure for vaults
- Add Obsidian-specific frontmatter

**Confluence Profile**
- Convert to Confluence storage format
- Map page hierarchy to spaces/pages
- Transform markdown to Confluence syntax

### Export Plugins

**Link Rewriter Plugin**
- Convert internal page links
- Update attachment references
- Handle broken links

**Image Optimizer Plugin**
- Compress images
- Convert formats
- Generate thumbnails

**Table of Contents Plugin**
- Generate TOC for each page
- Create index page

**Search Index Plugin**
- Generate search index file
- Create sitemap

### Advanced Options

- **Selective Export**: Export specific page branches
- **Date Range**: Export pages modified in date range
- **Filtering**: Export by tags, author, etc.
- **Preview**: Preview export before download
- **Scheduling**: Schedule automatic backups
- **Cloud Upload**: Export directly to S3, Drive, etc.

## Documentation

### User Documentation
- How to export a wiki
- Understanding export profiles
- Restoring from backup
- Troubleshooting export issues

### Developer Documentation
- Creating custom profiles
- Writing export plugins
- Profile API reference
- Plugin API reference
- Testing export features

## Success Metrics

1. **Reliability**
   - Export success rate > 99%
   - Round-trip data integrity: 100%
   - Zero data loss on export

2. **Performance**
   - Small wiki (<10 pages): < 2 seconds
   - Medium wiki (<100 pages): < 10 seconds
   - Large wiki (<1000 pages): < 60 seconds

3. **Usability**
   - Export button clearly visible
   - Progress feedback for long exports
   - Clear error messages

## Rollout Plan

1. **Development**: Weeks 1-3
2. **Internal Testing**: Week 4
3. **Beta Release**: Week 5 (select users)
4. **Public Release**: Week 6
5. **Advanced Features**: Weeks 7-12

## Risk Mitigation

**Risk: Data loss during export**
- Mitigation: Extensive testing, transaction safety, backup verification

**Risk: Performance issues with large wikis**
- Mitigation: Background processing, streaming, pagination

**Risk: Security vulnerabilities**
- Mitigation: Input validation, authorization checks, security audit

**Risk: Format compatibility issues**
- Mitigation: Format versioning, backward compatibility, extensive testing

## Conclusion

This implementation plan provides a solid foundation for wiki export functionality while maintaining extensibility for future enhancements. The profile and plugin architecture allows for gradual addition of advanced features without disrupting the core export system.

Key priorities:
1. Reliability and data integrity (Phase 1)
2. User experience (Phase 2)
3. Extensibility (Phase 3-4)
4. Advanced features (Phase 5+)

The backup profile ensures users can safely export and restore their wikis, while the plugin system provides a path for sophisticated export transformations in the future.
