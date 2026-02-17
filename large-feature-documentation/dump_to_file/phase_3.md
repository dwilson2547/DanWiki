# Phase 3: Profile System (Week 2)

## Overview

**Priority: MEDIUM - Extensibility foundation**

This phase establishes the architectural foundation for extensible export profiles, allowing different export formats and transformations. The profile system enables future support for platform-specific exports (GitHub, VS Code, Obsidian, etc.) while maintaining the backup profile as the default.

## Goals

- Create `ExportProfile` abstract base class
- Implement `BackupProfile` as reference implementation
- Implement `PlainMarkdownProfile` for simplified exports
- Create profile registry system
- Add profile selection to API endpoint
- Update frontend to support profile selection
- Design plugin attachment system for profiles
- Establish profile configuration pattern

## Timeline

**Duration:** 3 days (Days 8-10 of implementation)

### Day 8-9: Profile Architecture
- Create `ExportProfile` base class
- Implement `BackupProfile`
- Create profile registry
- Add profile selection to API

### Day 10: Plain Markdown Profile
- Implement basic transformation profile
- Strip backup-specific metadata
- Test with various markdown renderers

## Technical Implementation

### File Structure

```
app/
├── services/
│   ├── archive_export.py          # Updated WikiExporter
│   └── export_profiles/
│       ├── __init__.py            # Profile registry
│       ├── base.py                # ExportProfile base class
│       ├── backup.py              # BackupProfile
│       └── plain.py               # PlainMarkdownProfile
```

### Base Profile Class

```python
# app/services/export_profiles/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class ProfileInfo:
    """Profile metadata for API/UI"""
    name: str
    display_name: str
    description: str
    supports_attachments: bool = True
    supports_tags: bool = True
    supports_metadata: bool = True

class ExportProfile(ABC):
    """Base class for export profiles"""
    
    @abstractmethod
    def get_info(self) -> ProfileInfo:
        """Get profile metadata"""
        pass
    
    @abstractmethod
    def get_options(self) -> 'ExportOptions':
        """Get profile-specific export options"""
        pass
    
    @abstractmethod
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Transform markdown content before export"""
        pass
    
    @abstractmethod
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """Build YAML frontmatter for page (or None to skip)"""
        pass
    
    @abstractmethod
    def get_page_filename(self, page: Any) -> str:
        """Get filename for page (with extension)"""
        pass
    
    @abstractmethod
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Define custom directory structure (optional override)"""
        pass
    
    def post_process_archive(self, temp_dir: Path) -> None:
        """Optional post-processing after all files written"""
        pass
    
    def get_plugins(self) -> List['ExportPlugin']:
        """Get plugins to apply for this profile"""
        return []
```

### Backup Profile Implementation

```python
# app/services/export_profiles/backup.py

from .base import ExportProfile, ProfileInfo
from ..archive_export import ExportOptions
import yaml
from typing import Optional, Dict, Any

class BackupProfile(ExportProfile):
    """Profile for creating restorable backups with full metadata"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='backup',
            display_name='Backup (Restorable)',
            description='Full backup that can be restored without data loss. '
                       'Includes all metadata, IDs, and timestamps.',
            supports_attachments=True,
            supports_tags=True,
            supports_metadata=True
        )
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='backup',
            preserve_metadata=True,
            add_backup_marker=True
        )
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """No transformation for backups - preserve original content"""
        return content
    
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """Build complete frontmatter with all metadata"""
        metadata = {
            'title': page.title,
            'slug': page.slug,
        }
        
        # Add tags
        if hasattr(page, 'tags') and page.tags:
            metadata['tags'] = [tag.name for tag in page.tags]
        
        # Add backup-specific metadata
        metadata['danwiki_id'] = page.id
        metadata['created_at'] = page.created_at.isoformat()
        metadata['updated_at'] = page.updated_at.isoformat()
        
        if page.parent_id:
            metadata['parent_id'] = page.parent_id
        
        if hasattr(page, 'order') and page.order is not None:
            metadata['order'] = page.order
        
        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    def get_page_filename(self, page: Any) -> str:
        """Use slug with .md extension"""
        from ..archive_export import sanitize_filename
        return f"{sanitize_filename(page.slug)}.md"
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Use default hierarchical structure"""
        # Default implementation handles hierarchy
        return {}
```

### Plain Markdown Profile

```python
# app/services/export_profiles/plain.py

from .base import ExportProfile, ProfileInfo
from ..archive_export import ExportOptions
import yaml
from typing import Optional, Dict, Any
import re

class PlainMarkdownProfile(ExportProfile):
    """Profile for plain markdown export without backup metadata"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='plain',
            display_name='Plain Markdown',
            description='Clean markdown export without backup metadata. '
                       'Suitable for general use but cannot be restored with full fidelity.',
            supports_attachments=True,
            supports_tags=True,
            supports_metadata=False
        )
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='plain',
            preserve_metadata=False,
            add_backup_marker=False
        )
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Clean up any DanWiki-specific syntax if needed"""
        # Future: transform internal links, remove custom syntax, etc.
        return content
    
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """Build minimal frontmatter - title and tags only"""
        metadata = {
            'title': page.title,
        }
        
        # Add tags if present
        if hasattr(page, 'tags') and page.tags:
            metadata['tags'] = [tag.name for tag in page.tags]
        
        # Only include frontmatter if we have tags
        # Otherwise, title will be in content as H1
        if not metadata.get('tags'):
            return None
        
        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    def get_page_filename(self, page: Any) -> str:
        """Use title for filename (more readable than slug)"""
        from ..archive_export import sanitize_filename
        # Use title if it's clean enough, otherwise use slug
        safe_title = sanitize_filename(page.title)
        if len(safe_title) > 50 or not safe_title:
            safe_title = sanitize_filename(page.slug)
        return f"{safe_title}.md"
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Use default hierarchical structure"""
        return {}
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Add title as H1 if no frontmatter"""
        if not page_data.get('has_frontmatter'):
            title = page_data.get('title', 'Untitled')
            return f"# {title}\n\n{content}"
        return content
```

### Profile Registry

```python
# app/services/export_profiles/__init__.py

from typing import Dict, Optional
from .base import ExportProfile, ProfileInfo
from .backup import BackupProfile
from .plain import PlainMarkdownProfile

class ProfileRegistry:
    """Registry for export profiles"""
    
    def __init__(self):
        self._profiles: Dict[str, ExportProfile] = {}
        self._register_default_profiles()
    
    def _register_default_profiles(self):
        """Register built-in profiles"""
        self.register(BackupProfile())
        self.register(PlainMarkdownProfile())
    
    def register(self, profile: ExportProfile):
        """Register a new profile"""
        info = profile.get_info()
        self._profiles[info.name] = profile
    
    def get(self, name: str) -> Optional[ExportProfile]:
        """Get profile by name"""
        return self._profiles.get(name)
    
    def list_profiles(self) -> list[ProfileInfo]:
        """List all available profiles"""
        return [profile.get_info() for profile in self._profiles.values()]
    
    def get_default(self) -> ExportProfile:
        """Get default profile (backup)"""
        return self._profiles.get('backup')

# Global registry instance
registry = ProfileRegistry()
```

### Updated WikiExporter

```python
# app/services/archive_export.py (updated)

from .export_profiles import registry as profile_registry

class WikiExporter:
    """Main exporter class with profile support"""
    
    def __init__(self, wiki_id: int, profile_name: str = None, options: ExportOptions = None):
        self.wiki_id = wiki_id
        
        # Get profile
        if profile_name:
            self.profile = profile_registry.get(profile_name)
            if not self.profile:
                raise ValueError(f"Unknown profile: {profile_name}")
        else:
            self.profile = profile_registry.get_default()
        
        # Use profile options or override
        self.options = options or self.profile.get_options()
        self.plugins: List[ExportPlugin] = self.profile.get_plugins()
    
    def _process_page(self, page, temp_dir: Path):
        """Process and write single page using profile"""
        # Get page path
        page_path = self._get_page_path(page)
        full_path = temp_dir / page_path
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build frontmatter using profile
        frontmatter = self.profile.build_frontmatter(page)
        
        # Get content
        content = page.content or ''
        
        # Transform content using profile
        page_data = {
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'has_frontmatter': frontmatter is not None
        }
        content = self.profile.transform_content(content, page_data)
        
        # Apply plugin transformations
        for plugin in self.plugins:
            page_data = plugin.process_page(page_data)
            content = page_data.get('content', content)
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            if frontmatter:
                f.write('---\n')
                f.write(frontmatter)
                f.write('---\n\n')
            f.write(content)
    
    def _get_page_filename(self, page) -> str:
        """Get filename from profile"""
        return self.profile.get_page_filename(page)
```

### Updated API Endpoint

```python
# app/routes/bulk_export.py (updated)

from app.services.export_profiles import registry as profile_registry

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
                "description": "...",
                "supports_attachments": true,
                "supports_tags": true,
                "supports_metadata": true
            },
            ...
        ]
    }
    """
    profiles = profile_registry.list_profiles()
    return jsonify({
        'profiles': [
            {
                'name': p.name,
                'display_name': p.display_name,
                'description': p.description,
                'supports_attachments': p.supports_attachments,
                'supports_tags': p.supports_tags,
                'supports_metadata': p.supports_metadata
            }
            for p in profiles
        ]
    })

@bp.route('/api/wikis/<int:wiki_id>/export', methods=['POST'])
@jwt_required()
def export_wiki(wiki_id):
    """
    Export wiki with profile support
    
    Request JSON:
    {
        "format": "zip",
        "profile": "backup",  # or "plain", default: "backup"
        "include_attachments": true
    }
    """
    data = request.get_json() or {}
    profile_name = data.get('profile', 'backup')
    
    # Validate profile exists
    profile = profile_registry.get(profile_name)
    if not profile:
        return jsonify({'error': f'Unknown profile: {profile_name}'}), 400
    
    # Create exporter with profile
    exporter = WikiExporter(wiki_id, profile_name=profile_name)
    
    # ... rest of export logic
```

### Frontend Updates

```jsx
// frontend/src/pages/WikiSettings.jsx (updated)

function WikiSettings() {
  const [exportFormat, setExportFormat] = useState('zip');
  const [exportProfile, setExportProfile] = useState('backup');
  const [availableProfiles, setAvailableProfiles] = useState([]);
  const [includeAttachments, setIncludeAttachments] = useState(true);
  
  useEffect(() => {
    // Load available profiles
    wikisAPI.getExportProfiles().then(data => {
      setAvailableProfiles(data.profiles);
    });
  }, []);
  
  const selectedProfile = availableProfiles.find(p => p.name === exportProfile);
  
  return (
    <div className="export-options">
      <div className="form-group">
        <label htmlFor="export-profile">Export Profile</label>
        <select 
          id="export-profile"
          value={exportProfile} 
          onChange={e => setExportProfile(e.target.value)}
        >
          {availableProfiles.map(profile => (
            <option key={profile.name} value={profile.name}>
              {profile.display_name}
            </option>
          ))}
        </select>
        {selectedProfile && (
          <p className="help-text">{selectedProfile.description}</p>
        )}
      </div>
      
      {/* ... rest of form ... */}
    </div>
  );
}
```

```javascript
// frontend/src/services/api.js (updated)

export const wikisAPI = {
  // ... existing methods ...
  
  getExportProfiles: async () => {
    const response = await apiClient.get('/wikis/profiles');
    return response.data;
  },
  
  exportWiki: async (wikiId, options = {}) => {
    const response = await apiClient.post(
      `/wikis/${wikiId}/export`,
      {
        format: options.format || 'zip',
        profile: options.profile || 'backup',
        include_attachments: options.include_attachments !== false
      },
      { responseType: 'blob' }
    );
    return response.data;
  }
};
```

## Profile Development Guidelines

### Creating a New Profile

```python
# Example: GitHub profile (future)
class GitHubProfile(ExportProfile):
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='github',
            display_name='GitHub Wiki',
            description='Export formatted for GitHub Wiki with sidebar'
        )
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        # Transform internal links to GitHub format
        # [[Page Name]] -> [Page Name](Page-Name)
        return content
    
    def get_plugins(self) -> List[ExportPlugin]:
        return [SidebarGeneratorPlugin()]
```

## Testing Requirements

### Unit Tests

```python
# tests/services/test_export_profiles.py

class TestBackupProfile:
    def test_profile_info(self):
        """Test profile metadata"""
        
    def test_frontmatter_generation(self):
        """Test backup frontmatter includes all metadata"""
        
    def test_content_transformation(self):
        """Test content is not modified"""

class TestPlainMarkdownProfile:
    def test_profile_info(self):
        """Test profile metadata"""
        
    def test_minimal_frontmatter(self):
        """Test frontmatter only includes title and tags"""
        
    def test_title_injection(self):
        """Test title added as H1 when no frontmatter"""

class TestProfileRegistry:
    def test_register_profile(self):
        """Test registering new profile"""
        
    def test_get_profile(self):
        """Test retrieving profile by name"""
        
    def test_list_profiles(self):
        """Test listing all profiles"""
        
    def test_get_default(self):
        """Test getting default profile"""
```

### Integration Tests

```python
# tests/integration/test_profile_export.py

class TestProfileExport:
    def test_export_with_backup_profile(self):
        """Test export using backup profile"""
        
    def test_export_with_plain_profile(self):
        """Test export using plain profile"""
        
    def test_profile_api_endpoint(self):
        """Test profiles API endpoint"""
        
    def test_invalid_profile_rejected(self):
        """Test invalid profile name returns error"""
```

## Success Criteria

- ✓ ExportProfile base class provides clear extension pattern
- ✓ BackupProfile maintains all functionality from Phase 1
- ✓ PlainMarkdownProfile generates clean markdown
- ✓ Profile registry allows easy addition of new profiles
- ✓ API exposes available profiles
- ✓ Frontend displays profile options
- ✓ All unit tests pass
- ✓ All integration tests pass
- ✓ Documentation explains profile creation

## Next Phase

After Phase 3 completion, proceed to **Phase 4: Plugin System** to add modular post-processing capabilities.

---

## Progress Tracking

### Feature 1: ExportProfile Base Class
- [ ] Create `app/services/export_profiles/` directory
- [ ] Create `base.py` file
- [ ] Define `ProfileInfo` dataclass
- [ ] Define `ExportProfile` abstract class
- [ ] Add `get_info()` abstract method
- [ ] Add `get_options()` abstract method
- [ ] Add `transform_content()` abstract method
- [ ] Add `build_frontmatter()` abstract method
- [ ] Add `get_page_filename()` abstract method
- [ ] Add `get_directory_structure()` abstract method
- [ ] Add `post_process_archive()` optional method
- [ ] Add `get_plugins()` optional method
- [ ] Document all abstract methods
- [ ] Add type hints to all methods

### Feature 2: BackupProfile Implementation
- [ ] Create `backup.py` file
- [ ] Import ExportProfile base class
- [ ] Create BackupProfile class
- [ ] Implement `get_info()` method
- [ ] Implement `get_options()` method
- [ ] Implement `transform_content()` (no-op)
- [ ] Implement `build_frontmatter()` with full metadata
- [ ] Include danwiki_id in frontmatter
- [ ] Include timestamps in frontmatter
- [ ] Include parent_id in frontmatter
- [ ] Include order in frontmatter
- [ ] Implement `get_page_filename()` using slug
- [ ] Implement `get_directory_structure()`
- [ ] Test BackupProfile

### Feature 3: PlainMarkdownProfile Implementation
- [ ] Create `plain.py` file
- [ ] Import ExportProfile base class
- [ ] Create PlainMarkdownProfile class
- [ ] Implement `get_info()` method
- [ ] Implement `get_options()` method
- [ ] Implement `transform_content()` method
- [ ] Add title as H1 when no frontmatter
- [ ] Implement `build_frontmatter()` with minimal data
- [ ] Only include tags in frontmatter
- [ ] Return None when no tags present
- [ ] Implement `get_page_filename()` using title
- [ ] Sanitize title for filename
- [ ] Fallback to slug for long titles
- [ ] Test PlainMarkdownProfile

### Feature 4: Profile Registry
- [ ] Create `__init__.py` in export_profiles
- [ ] Create ProfileRegistry class
- [ ] Add `_profiles` dictionary
- [ ] Implement `__init__()` method
- [ ] Implement `_register_default_profiles()`
- [ ] Implement `register()` method
- [ ] Implement `get()` method
- [ ] Implement `list_profiles()` method
- [ ] Implement `get_default()` method
- [ ] Create global registry instance
- [ ] Register BackupProfile
- [ ] Register PlainMarkdownProfile
- [ ] Test registry operations

### Feature 5: Update WikiExporter for Profiles
- [ ] Import profile_registry in archive_export.py
- [ ] Update `__init__()` to accept profile_name
- [ ] Load profile from registry
- [ ] Handle invalid profile name
- [ ] Use profile.get_options() if no options provided
- [ ] Get plugins from profile
- [ ] Update `_process_page()` to use profile
- [ ] Call profile.build_frontmatter()
- [ ] Call profile.transform_content()
- [ ] Update `_get_page_filename()` to use profile
- [ ] Call profile.post_process_archive() at end
- [ ] Test exporter with different profiles

### Feature 6: Profile API Endpoint
- [ ] Add route GET `/api/wikis/profiles`
- [ ] Import profile_registry in bulk_export.py
- [ ] Call registry.list_profiles()
- [ ] Format profile info for JSON response
- [ ] Include all ProfileInfo fields
- [ ] Test endpoint returns profiles
- [ ] Test response format

### Feature 7: Update Export API for Profiles
- [ ] Accept `profile` parameter in request
- [ ] Default to 'backup' profile
- [ ] Validate profile exists
- [ ] Return 400 for invalid profile
- [ ] Pass profile_name to WikiExporter
- [ ] Update API documentation
- [ ] Test with backup profile
- [ ] Test with plain profile
- [ ] Test with invalid profile

### Feature 8: Frontend Profile Support
- [ ] Add availableProfiles state to WikiSettings
- [ ] Add exportProfile state
- [ ] Call getExportProfiles on mount
- [ ] Store profiles in state
- [ ] Add profile selector dropdown
- [ ] Populate dropdown with available profiles
- [ ] Display profile descriptions
- [ ] Handle profile selection
- [ ] Pass profile to exportWiki API call
- [ ] Test profile selection UI

### Feature 9: API Service Updates
- [ ] Add getExportProfiles() method to api.js
- [ ] Implement GET request to /wikis/profiles
- [ ] Update exportWiki() to accept profile parameter
- [ ] Include profile in POST request body
- [ ] Test API methods

### Feature 10: Profile Styling
- [ ] Style profile selector dropdown
- [ ] Style profile description text
- [ ] Ensure consistent spacing
- [ ] Add hover effects
- [ ] Test responsive layout
- [ ] Test dark mode compatibility

### Feature 11: Unit Tests - Profiles
- [ ] Write test: BackupProfile.get_info()
- [ ] Write test: BackupProfile.build_frontmatter()
- [ ] Write test: BackupProfile includes all metadata
- [ ] Write test: PlainProfile.get_info()
- [ ] Write test: PlainProfile.build_frontmatter()
- [ ] Write test: PlainProfile minimal frontmatter
- [ ] Write test: PlainProfile adds title as H1
- [ ] Write test: PlainProfile uses title for filename
- [ ] Run profile unit tests

### Feature 12: Unit Tests - Registry
- [ ] Write test: ProfileRegistry.register()
- [ ] Write test: ProfileRegistry.get()
- [ ] Write test: ProfileRegistry.list_profiles()
- [ ] Write test: ProfileRegistry.get_default()
- [ ] Write test: Registry loads default profiles
- [ ] Run registry unit tests

### Feature 13: Integration Tests
- [ ] Write test: Export with backup profile
- [ ] Write test: Export with plain profile
- [ ] Write test: Verify backup includes metadata
- [ ] Write test: Verify plain excludes metadata
- [ ] Write test: Profiles API endpoint
- [ ] Write test: Invalid profile returns 400
- [ ] Write test: Frontend profile selection
- [ ] Run integration tests

### Feature 14: Documentation
- [ ] Document ExportProfile interface
- [ ] Document how to create custom profiles
- [ ] Document BackupProfile behavior
- [ ] Document PlainMarkdownProfile behavior
- [ ] Document profile registry usage
- [ ] Add profile API documentation
- [ ] Create profile development guide
- [ ] Add code examples

### Feature 15: Manual Testing
- [ ] Test export with backup profile
- [ ] Verify backup includes all metadata
- [ ] Test export with plain profile
- [ ] Verify plain has minimal frontmatter
- [ ] Test profile selection in UI
- [ ] Test profile descriptions display
- [ ] Verify profile API endpoint
- [ ] Test invalid profile handling
