# Phase 5: Advanced Profiles (Week 4+)

## Overview

**Priority: LOW - Nice to have**

This phase implements platform-specific export profiles that transform wiki content for optimal compatibility with various platforms. Each profile applies appropriate transformations, plugins, and formatting to ensure exported wikis work seamlessly with the target platform.

## Goals

- Implement GitHub Wiki profile
- Implement VS Code profile
- Implement Obsidian profile
- Implement Confluence profile (optional)
- Create platform-specific plugins
- Add export preview feature
- Implement scheduled/automated exports
- Add cloud upload integration

## Timeline

**Duration:** 8+ days (Days 14+ of implementation)

### Week 4: GitHub Profile
- Day 14-15: GitHub profile implementation
- Day 16: GitHub-specific plugins
- Day 17: Testing and refinement

### Week 5: VS Code Profile
- Day 18-19: VS Code profile implementation
- Day 20: VS Code workspace generation
- Day 21: Testing

### Future: Additional Profiles
- Obsidian profile
- Confluence profile
- Hugo/Jekyll static site profiles
- Custom profile builder UI

## Platform Profiles

### GitHub Wiki Profile

**Target:** GitHub's built-in wiki system

**Features:**
- Generate `_Sidebar.md` for navigation
- Generate `_Footer.md` with metadata
- Convert internal links to GitHub format
- Optimize images for GitHub
- Use GitHub-flavored markdown
- Create Home.md entry point

```python
# app/services/export_profiles/github.py

from .base import ExportProfile, ProfileInfo
from ..archive_export import ExportOptions
from ..export_plugins import registry as plugin_registry
from ..export_plugins.base import PluginConfig
import yaml
from typing import Optional, Dict, Any, List

class GitHubProfile(ExportProfile):
    """Profile for GitHub Wiki export"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='github',
            display_name='GitHub Wiki',
            description='Export optimized for GitHub Wiki with sidebar navigation, '
                       'GitHub-flavored markdown, and proper link formatting.',
            supports_attachments=True,
            supports_tags=False,  # GitHub wiki doesn't support tags
            supports_metadata=False
        )
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='github',
            preserve_metadata=False,
            add_backup_marker=False
        )
    
    def get_plugins(self) -> List:
        """GitHub-specific plugins"""
        return [
            plugin_registry.create('link_rewriter', PluginConfig(
                priority=10,
                options={
                    'github_format': True,
                    'convert_spaces': True  # "Page Name" -> "Page-Name"
                }
            )),
            plugin_registry.create('sidebar_generator', PluginConfig(
                priority=20,
                options={
                    'filename': '_Sidebar.md',
                    'style': 'github',
                    'include_home': True
                }
            )),
            plugin_registry.create('footer_generator', PluginConfig(
                priority=30,
                options={
                    'include_last_updated': True,
                    'include_page_count': True
                }
            ))
        ]
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Apply GitHub-specific transformations"""
        import re
        
        # Convert checkbox syntax to GitHub format
        content = re.sub(r'- \[ \]', '- [ ]', content)  # Ensure no extra spaces
        content = re.sub(r'- \[x\]', '- [x]', content, flags=re.IGNORECASE)
        
        # Ensure code blocks use GFM syntax
        # (already standard markdown, but validate)
        
        # Convert any custom callouts to GitHub alerts
        content = self._convert_callouts_to_alerts(content)
        
        return content
    
    def _convert_callouts_to_alerts(self, content: str) -> str:
        """Convert custom callouts to GitHub-style alerts"""
        import re
        
        # > [!NOTE] -> > **Note**
        callout_map = {
            'NOTE': 'Note',
            'TIP': 'Tip',
            'IMPORTANT': 'Important',
            'WARNING': 'Warning',
            'CAUTION': 'Caution'
        }
        
        for key, value in callout_map.items():
            content = re.sub(
                rf'> \[!{key}\]',
                f'> **{value}**',
                content,
                flags=re.IGNORECASE
            )
        
        return content
    
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """No frontmatter for GitHub wiki"""
        return None
    
    def get_page_filename(self, page: Any) -> str:
        """Use title with GitHub-style naming"""
        from ..archive_export import sanitize_filename
        
        # GitHub uses title with hyphens
        title = page.title.replace(' ', '-')
        safe_title = sanitize_filename(title)
        
        # Special case: first root page becomes Home.md
        if not page.parent_id and page.order == 0:
            return 'Home.md'
        
        return f"{safe_title}.md"
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Flat structure - GitHub wiki doesn't use subdirectories"""
        return {'flat': True}
    
    def post_process_archive(self, temp_dir: Path) -> None:
        """Final GitHub-specific processing"""
        # Ensure Home.md exists
        home_path = temp_dir / 'Home.md'
        if not home_path.exists():
            self._create_home_page(temp_dir)
        
        # Move all attachments to flat structure
        self._flatten_attachments(temp_dir)
    
    def _create_home_page(self, temp_dir: Path):
        """Create default Home.md if none exists"""
        content = """# Welcome

This wiki was exported from DanWiki.

## Navigation

Use the sidebar to navigate through pages.
"""
        home_path = temp_dir / 'Home.md'
        with open(home_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _flatten_attachments(self, temp_dir: Path):
        """Move attachments to root (GitHub wiki limitation)"""
        import shutil
        
        for subdir in temp_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('_'):
                for file in subdir.rglob('*'):
                    if file.is_file():
                        # Move to root with prefixed name
                        new_name = f"{subdir.name}_{file.name}"
                        shutil.move(str(file), temp_dir / new_name)
                
                # Remove empty directory
                if subdir.exists():
                    shutil.rmtree(subdir)
```

### GitHub-Specific Plugins

```python
# app/services/export_plugins/footer_generator.py

from .base import ExportPlugin, PluginInfo, PluginConfig
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class FooterGeneratorPlugin(ExportPlugin):
    """Generate footer file for wiki"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name='footer_generator',
            display_name='Footer Generator',
            description='Generates wiki footer (_Footer.md)',
            version='1.0.0'
        )
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        return page_data
    
    def process_archive(self, temp_dir: Path, context: Dict[str, Any]) -> None:
        """Generate footer file"""
        wiki = context['wiki']
        pages = context['pages']
        
        content = self._generate_footer_content(wiki, pages)
        
        footer_path = temp_dir / '_Footer.md'
        with open(footer_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_footer_content(self, wiki, pages) -> str:
        """Generate footer markdown"""
        lines = []
        
        if self.config.options.get('include_page_count', True):
            lines.append(f"📄 {len(pages)} pages")
        
        if self.config.options.get('include_last_updated', True):
            now = datetime.utcnow().strftime('%Y-%m-%d')
            lines.append(f"🕒 Last updated: {now}")
        
        if self.config.options.get('include_wiki_name', True):
            lines.append(f"📚 {wiki.name}")
        
        return ' | '.join(lines)
```

### VS Code Profile

**Target:** VS Code markdown preview and workspace

**Features:**
- Generate `.vscode/settings.json` with optimal settings
- Generate `.vscode/extensions.json` with recommendations
- Create workspace file
- Use VS Code compatible markdown
- Optimize image paths for preview

```python
# app/services/export_profiles/vscode.py

from .base import ExportProfile, ProfileInfo
from ..archive_export import ExportOptions
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class VSCodeProfile(ExportProfile):
    """Profile for VS Code workspace export"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='vscode',
            display_name='VS Code Workspace',
            description='Export as VS Code workspace with optimal settings, '
                       'extension recommendations, and markdown preview compatibility.',
            supports_attachments=True,
            supports_tags=True,
            supports_metadata=True
        )
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='vscode',
            preserve_metadata=False,
            add_backup_marker=False
        )
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Ensure VS Code markdown compatibility"""
        # VS Code handles standard markdown well
        return content
    
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """Minimal frontmatter for VS Code"""
        import yaml
        
        metadata = {'title': page.title}
        
        if hasattr(page, 'tags') and page.tags:
            metadata['tags'] = [tag.name for tag in page.tags]
        
        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    def get_page_filename(self, page: Any) -> str:
        from ..archive_export import sanitize_filename
        return f"{sanitize_filename(page.slug)}.md"
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Use hierarchical structure"""
        return {}
    
    def post_process_archive(self, temp_dir: Path) -> None:
        """Generate VS Code workspace files"""
        self._create_vscode_settings(temp_dir)
        self._create_vscode_extensions(temp_dir)
        self._create_workspace_file(temp_dir)
        self._create_readme(temp_dir)
    
    def _create_vscode_settings(self, temp_dir: Path):
        """Create .vscode/settings.json"""
        vscode_dir = temp_dir / '.vscode'
        vscode_dir.mkdir(exist_ok=True)
        
        settings = {
            "markdown.preview.breaks": True,
            "markdown.preview.linkify": True,
            "markdown.preview.typographer": True,
            "files.associations": {
                "*.md": "markdown"
            },
            "editor.wordWrap": "on",
            "editor.quickSuggestions": {
                "comments": "off",
                "strings": "off",
                "other": "off"
            },
            "files.exclude": {
                "**/.git": True,
                "**/.DS_Store": True,
                "**/__pycache__": True
            }
        }
        
        settings_path = vscode_dir / 'settings.json'
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    
    def _create_vscode_extensions(self, temp_dir: Path):
        """Create .vscode/extensions.json"""
        vscode_dir = temp_dir / '.vscode'
        vscode_dir.mkdir(exist_ok=True)
        
        extensions = {
            "recommendations": [
                "yzhang.markdown-all-in-one",
                "davidanson.vscode-markdownlint",
                "bierner.markdown-preview-github-styles",
                "bierner.markdown-checkbox",
                "bierner.markdown-emoji",
                "bierner.markdown-mermaid"
            ]
        }
        
        extensions_path = vscode_dir / 'extensions.json'
        with open(extensions_path, 'w', encoding='utf-8') as f:
            json.dump(extensions, f, indent=2)
    
    def _create_workspace_file(self, temp_dir: Path):
        """Create .code-workspace file"""
        workspace = {
            "folders": [
                {"path": "."}
            ],
            "settings": {
                "markdown.preview.breaks": True
            }
        }
        
        workspace_path = temp_dir / 'wiki.code-workspace'
        with open(workspace_path, 'w', encoding='utf-8') as f:
            json.dump(workspace, f, indent=2)
    
    def _create_readme(self, temp_dir: Path):
        """Create README with instructions"""
        content = """# Wiki Export for VS Code

This directory contains your wiki exported for VS Code.

## Getting Started

1. Open this folder in VS Code
2. Or open the `wiki.code-workspace` file
3. Install recommended extensions when prompted
4. Use Markdown Preview to view pages

## Navigation

Browse the directory structure to find pages. Use VS Code's file explorer and search.

## Recommended Extensions

- **Markdown All in One**: Enhanced markdown editing
- **markdownlint**: Markdown linting
- **Markdown Preview GitHub Styles**: Better preview styling

Happy editing!
"""
        
        readme_path = temp_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
```

### Obsidian Profile

**Target:** Obsidian note-taking app

**Features:**
- Use wikilink syntax `[[Page Name]]`
- Generate `.obsidian` configuration
- Support backlinks and graph view
- Obsidian-specific frontmatter

```python
# app/services/export_profiles/obsidian.py

from .base import ExportProfile, ProfileInfo
from ..archive_export import ExportOptions
from ..export_plugins import registry as plugin_registry
from ..export_plugins.base import PluginConfig
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class ObsidianProfile(ExportProfile):
    """Profile for Obsidian vault export"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='obsidian',
            display_name='Obsidian Vault',
            description='Export as Obsidian vault with wikilinks, backlinks, '
                       'and graph view support.',
            supports_attachments=True,
            supports_tags=True,
            supports_metadata=True
        )
    
    def get_options(self) -> ExportOptions:
        return ExportOptions(
            format='zip',
            include_attachments=True,
            profile='obsidian',
            preserve_metadata=False,
            add_backup_marker=False
        )
    
    def get_plugins(self) -> List:
        """Obsidian-specific plugins"""
        return [
            plugin_registry.create('link_rewriter', PluginConfig(
                priority=10,
                options={
                    'use_wikilinks': True,
                    'obsidian_format': True
                }
            ))
        ]
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """Convert to Obsidian format"""
        import re
        
        # Convert standard markdown links to wikilinks
        # [Page Title](page-slug) -> [[Page Title]]
        content = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: self._convert_to_wikilink(m.group(1), m.group(2)),
            content
        )
        
        return content
    
    def _convert_to_wikilink(self, text: str, url: str) -> str:
        """Convert markdown link to wikilink"""
        # Only convert internal links
        if url.startswith('http') or url.startswith('/'):
            return f'[{text}]({url})'
        
        # Use display text if different from link
        if text.lower() != url.replace('-', ' ').lower():
            return f'[[{url}|{text}]]'
        
        return f'[[{url}]]'
    
    def build_frontmatter(self, page: Any) -> Optional[str]:
        """Obsidian-style frontmatter"""
        import yaml
        
        metadata = {
            'title': page.title,
            'aliases': [page.slug]
        }
        
        if hasattr(page, 'tags') and page.tags:
            metadata['tags'] = [tag.name for tag in page.tags]
        
        if hasattr(page, 'created_at'):
            metadata['created'] = page.created_at.isoformat()
        
        if hasattr(page, 'updated_at'):
            metadata['modified'] = page.updated_at.isoformat()
        
        return yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    
    def get_page_filename(self, page: Any) -> str:
        """Use title for filename (Obsidian convention)"""
        from ..archive_export import sanitize_filename
        safe_title = sanitize_filename(page.title)
        return f"{safe_title}.md"
    
    def get_directory_structure(self, pages: List) -> Dict[str, Any]:
        """Hierarchical structure"""
        return {}
    
    def post_process_archive(self, temp_dir: Path) -> None:
        """Create Obsidian vault structure"""
        self._create_obsidian_config(temp_dir)
        self._create_canvas_view(temp_dir)
    
    def _create_obsidian_config(self, temp_dir: Path):
        """Create .obsidian directory with config"""
        obsidian_dir = temp_dir / '.obsidian'
        obsidian_dir.mkdir(exist_ok=True)
        
        # Main config
        config = {
            "livePreview": True,
            "spellcheck": True,
            "foldHeading": True,
            "foldIndent": True,
            "showLineNumber": False,
            "useTab": False
        }
        
        config_path = obsidian_dir / 'app.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        # Graph view config
        graph_config = {
            "collapse-filter": False,
            "search": "",
            "showTags": True,
            "showAttachments": True,
            "hideUnresolved": False
        }
        
        graph_path = obsidian_dir / 'graph.json'
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_config, f, indent=2)
    
    def _create_canvas_view(self, temp_dir: Path):
        """Create a canvas visualization (optional)"""
        pass  # Advanced feature
```

## Additional Features

### Export Preview

Allow users to preview export before downloading:

```python
# app/routes/bulk_export.py

@bp.route('/api/wikis/<int:wiki_id>/export/preview', methods=['POST'])
@jwt_required()
def preview_export(wiki_id):
    """
    Generate preview of export structure
    
    Returns tree structure and sample files
    """
    pass
```

### Scheduled Exports

Automatic periodic backups:

```python
# app/tasks/scheduled_exports.py

from celery import Celery
from app.services.archive_export import WikiExporter

@celery.task
def scheduled_wiki_backup(wiki_id):
    """Automatic backup task"""
    exporter = WikiExporter(wiki_id, profile_name='backup')
    result = exporter.export()
    
    if result.success:
        # Upload to cloud storage
        upload_to_storage(result.archive_path)
```

### Cloud Upload Integration

Direct upload to cloud storage:

```python
# app/services/cloud_storage.py

class CloudStorageUploader:
    def upload_to_s3(self, file_path, bucket_name):
        """Upload to AWS S3"""
        pass
    
    def upload_to_drive(self, file_path, folder_id):
        """Upload to Google Drive"""
        pass
    
    def upload_to_dropbox(self, file_path, path):
        """Upload to Dropbox"""
        pass
```

## Testing Requirements

- Complete profile-specific test suites
- Cross-platform compatibility testing
- Import-export roundtrip testing for each platform
- Performance benchmarking for large wikis

## Success Criteria

- ✓ GitHub profile exports work seamlessly with GitHub Wiki
- ✓ VS Code profile creates functional workspace
- ✓ Obsidian profile opens correctly in Obsidian
- ✓ Platform-specific features work correctly
- ✓ All exports maintain data integrity
- ✓ Documentation covers all profiles

---

## Progress Tracking

### Feature 1: GitHub Profile Implementation
- [ ] Create `github.py` in export_profiles
- [ ] Implement GitHubProfile class
- [ ] Implement get_info()
- [ ] Implement get_options()
- [ ] Implement get_plugins()
- [ ] Implement transform_content()
- [ ] Implement _convert_callouts_to_alerts()
- [ ] Implement build_frontmatter() (return None)
- [ ] Implement get_page_filename()
- [ ] Handle Home.md special case
- [ ] Implement get_directory_structure() (flat)
- [ ] Implement post_process_archive()
- [ ] Implement _create_home_page()
- [ ] Implement _flatten_attachments()
- [ ] Register GitHub profile
- [ ] Test GitHub export

### Feature 2: Footer Generator Plugin
- [ ] Create `footer_generator.py`
- [ ] Implement FooterGeneratorPlugin class
- [ ] Implement get_info()
- [ ] Implement process_page() (no-op)
- [ ] Implement process_archive()
- [ ] Implement _generate_footer_content()
- [ ] Include page count option
- [ ] Include last updated option
- [ ] Include wiki name option
- [ ] Write _Footer.md file
- [ ] Register plugin
- [ ] Test footer generation

### Feature 3: VS Code Profile Implementation
- [ ] Create `vscode.py` in export_profiles
- [ ] Implement VSCodeProfile class
- [ ] Implement get_info()
- [ ] Implement get_options()
- [ ] Implement transform_content()
- [ ] Implement build_frontmatter()
- [ ] Implement get_page_filename()
- [ ] Implement post_process_archive()
- [ ] Implement _create_vscode_settings()
- [ ] Implement _create_vscode_extensions()
- [ ] Implement _create_workspace_file()
- [ ] Implement _create_readme()
- [ ] Register VS Code profile
- [ ] Test VS Code export

### Feature 4: Obsidian Profile Implementation
- [ ] Create `obsidian.py` in export_profiles
- [ ] Implement ObsidianProfile class
- [ ] Implement get_info()
- [ ] Implement get_options()
- [ ] Implement get_plugins()
- [ ] Implement transform_content()
- [ ] Implement _convert_to_wikilink()
- [ ] Implement build_frontmatter()
- [ ] Include aliases in frontmatter
- [ ] Include timestamps in frontmatter
- [ ] Implement get_page_filename()
- [ ] Implement post_process_archive()
- [ ] Implement _create_obsidian_config()
- [ ] Create app.json config
- [ ] Create graph.json config
- [ ] Register Obsidian profile
- [ ] Test Obsidian export

### Feature 5: Profile Testing & Validation
- [ ] Test GitHub export with real wiki
- [ ] Verify GitHub export imports to GitHub
- [ ] Test VS Code export opens in VS Code
- [ ] Verify VS Code extensions recommended
- [ ] Test Obsidian export opens in Obsidian
- [ ] Verify Obsidian wikilinks work
- [ ] Test all profiles maintain data integrity
- [ ] Compare exports across profiles

### Feature 6: Export Preview Feature
- [ ] Design preview API endpoint
- [ ] Implement preview generation
- [ ] Return file tree structure
- [ ] Include sample file contents
- [ ] Create preview UI component
- [ ] Display preview before export
- [ ] Allow cancellation after preview
- [ ] Test preview functionality

### Feature 7: Scheduled Exports
- [ ] Set up Celery for background tasks
- [ ] Create scheduled_exports task module
- [ ] Implement automatic backup task
- [ ] Add schedule configuration
- [ ] Store backup history
- [ ] Add UI for backup schedule settings
- [ ] Test scheduled exports
- [ ] Add email notifications

### Feature 8: Cloud Upload Integration
- [ ] Create cloud_storage service module
- [ ] Implement S3 uploader
- [ ] Implement Google Drive uploader
- [ ] Implement Dropbox uploader
- [ ] Add cloud storage settings to UI
- [ ] Add upload option to export flow
- [ ] Test cloud uploads
- [ ] Handle upload errors

### Feature 9: Documentation
- [ ] Document GitHub profile usage
- [ ] Document VS Code profile usage
- [ ] Document Obsidian profile usage
- [ ] Create platform comparison guide
- [ ] Document cloud upload feature
- [ ] Document scheduled exports
- [ ] Add troubleshooting guides
- [ ] Create video tutorials

### Feature 10: Performance Optimization
- [ ] Benchmark large wiki exports (1000+ pages)
- [ ] Optimize GitHub flat structure conversion
- [ ] Optimize VS Code workspace generation
- [ ] Profile memory usage
- [ ] Implement streaming for large files
- [ ] Add export progress tracking
- [ ] Test concurrent exports
- [ ] Monitor server resources
