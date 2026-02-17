# Phase 4: Plugin System (Week 3)

## Overview

**Priority: MEDIUM - Advanced features**

This phase implements a flexible plugin system that allows modular post-processing operations during export. Plugins can transform content, generate additional files, rewrite links, optimize assets, and perform other custom operations. This establishes the foundation for sophisticated export workflows.

## Goals

- Create `ExportPlugin` abstract base class
- Implement plugin execution pipeline
- Create sample plugins (sidebar generator, link rewriter)
- Add plugin configuration system
- Enable profiles to specify their plugins
- Implement plugin ordering/priority
- Add plugin error handling
- Document plugin development

## Timeline

**Duration:** 3 days (Days 11-13 of implementation)

### Day 11-12: Plugin Framework
- Create `ExportPlugin` base class
- Implement plugin loading system
- Add plugin execution pipeline
- Create plugin configuration system

### Day 13: Sample Plugins
- Create sidebar generator plugin
- Create link rewriter plugin
- Document plugin development

## Technical Implementation

### File Structure

```
app/
├── services/
│   ├── archive_export.py          # Updated with plugin support
│   ├── export_profiles/
│   │   └── ...
│   └── export_plugins/
│       ├── __init__.py            # Plugin registry
│       ├── base.py                # ExportPlugin base class
│       ├── sidebar_generator.py   # Sidebar plugin
│       └── link_rewriter.py       # Link rewriting plugin
```

### Base Plugin Class

```python
# app/services/export_plugins/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

@dataclass
class PluginConfig:
    """Configuration for a plugin"""
    enabled: bool = True
    priority: int = 50  # Lower runs first (0-100)
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}

@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    display_name: str
    description: str
    version: str
    author: str = "DanWiki"
    requires_attachments: bool = False

class ExportPlugin(ABC):
    """Base class for export plugins"""
    
    def __init__(self, config: PluginConfig = None):
        self.config = config or PluginConfig()
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin metadata"""
        pass
    
    @abstractmethod
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process page data before writing to file
        
        Args:
            page_data: Dictionary with keys:
                - id: Page ID
                - title: Page title
                - slug: Page slug
                - content: Markdown content
                - parent_id: Parent page ID (or None)
                - path: Relative path where file will be written
                - attachments: List of attachment dicts
                
        Returns:
            Modified page_data dictionary
        """
        pass
    
    def process_archive(self, temp_dir: Path, context: Dict[str, Any]) -> None:
        """
        Process entire archive after all pages written
        
        Args:
            temp_dir: Path to temporary export directory
            context: Dictionary with:
                - wiki: Wiki object
                - pages: List of all page objects
                - page_map: Dict mapping page IDs to paths
                - attachments: List of all attachments
        """
        pass
    
    def validate_config(self) -> List[str]:
        """
        Validate plugin configuration
        
        Returns:
            List of error messages (empty if valid)
        """
        return []
```

### Sidebar Generator Plugin

```python
# app/services/export_plugins/sidebar_generator.py

from .base import ExportPlugin, PluginInfo, PluginConfig
from pathlib import Path
from typing import Dict, Any, List

class SidebarGeneratorPlugin(ExportPlugin):
    """Generate sidebar navigation file"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name='sidebar_generator',
            display_name='Sidebar Generator',
            description='Generates navigation sidebar file (_Sidebar.md)',
            version='1.0.0'
        )
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """No per-page processing needed"""
        return page_data
    
    def process_archive(self, temp_dir: Path, context: Dict[str, Any]) -> None:
        """Generate sidebar file from page hierarchy"""
        pages = context['pages']
        page_map = context['page_map']
        
        # Build tree structure
        root_pages = [p for p in pages if not p.parent_id]
        
        # Generate sidebar content
        sidebar_content = self._generate_sidebar_content(root_pages, pages, page_map)
        
        # Write sidebar file
        sidebar_path = temp_dir / '_Sidebar.md'
        with open(sidebar_path, 'w', encoding='utf-8') as f:
            f.write(sidebar_content)
    
    def _generate_sidebar_content(
        self, 
        root_pages: List, 
        all_pages: List, 
        page_map: Dict[int, str]
    ) -> str:
        """Generate markdown for sidebar"""
        lines = ['# Navigation\n']
        
        for page in sorted(root_pages, key=lambda p: getattr(p, 'order', 0)):
            lines.extend(self._generate_page_entry(page, all_pages, page_map, level=0))
        
        return '\n'.join(lines)
    
    def _generate_page_entry(
        self, 
        page, 
        all_pages: List, 
        page_map: Dict[int, str], 
        level: int
    ) -> List[str]:
        """Generate sidebar entry for a page and its children"""
        indent = '  ' * level
        path = page_map.get(page.id, '')
        
        # Remove .md extension for cleaner links
        link_path = path.replace('.md', '')
        
        lines = [f"{indent}- [{page.title}]({link_path})"]
        
        # Add children
        children = [p for p in all_pages if p.parent_id == page.id]
        for child in sorted(children, key=lambda p: getattr(p, 'order', 0)):
            lines.extend(self._generate_page_entry(child, all_pages, page_map, level + 1))
        
        return lines
```

### Link Rewriter Plugin

```python
# app/services/export_plugins/link_rewriter.py

from .base import ExportPlugin, PluginInfo, PluginConfig
from pathlib import Path
from typing import Dict, Any
import re

class LinkRewriterPlugin(ExportPlugin):
    """Rewrite internal links to match export structure"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name='link_rewriter',
            display_name='Link Rewriter',
            description='Rewrites internal page links to match export structure',
            version='1.0.0'
        )
    
    def __init__(self, config: PluginConfig = None):
        super().__init__(config)
        self.link_map = {}  # Maps page IDs to export paths
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite links in page content"""
        content = page_data.get('content', '')
        
        # Store page ID -> path mapping
        self.link_map[page_data['id']] = page_data['path']
        
        # Rewrite internal links
        # Pattern: [text](/wiki/123) or [text](/pages/123)
        content = re.sub(
            r'\[([^\]]+)\]\(/(?:wiki|pages)/(\d+)\)',
            lambda m: self._rewrite_link(m.group(1), m.group(2)),
            content
        )
        
        # Pattern: [[Page Title]] (wikilink style)
        if self.config.options.get('convert_wikilinks', False):
            content = re.sub(
                r'\[\[([^\]]+)\]\]',
                lambda m: self._convert_wikilink(m.group(1)),
                content
            )
        
        page_data['content'] = content
        return page_data
    
    def _rewrite_link(self, link_text: str, page_id: str) -> str:
        """Rewrite a single link"""
        try:
            target_path = self.link_map.get(int(page_id))
            if target_path:
                # Make path relative and remove .md for cleaner links
                rel_path = target_path.replace('.md', '')
                return f'[{link_text}]({rel_path})'
        except (ValueError, KeyError):
            pass
        
        # Link couldn't be resolved, leave as-is
        return f'[{link_text}](/pages/{page_id})'
    
    def _convert_wikilink(self, title: str) -> str:
        """Convert wikilink to standard markdown link"""
        # Simple slug generation
        slug = title.lower().replace(' ', '-')
        return f'[{title}]({slug})'
```

### Plugin Registry

```python
# app/services/export_plugins/__init__.py

from typing import Dict, List, Optional
from .base import ExportPlugin, PluginInfo
from .sidebar_generator import SidebarGeneratorPlugin
from .link_rewriter import LinkRewriterPlugin

class PluginRegistry:
    """Registry for export plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, type] = {}
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Register built-in plugins"""
        self.register(SidebarGeneratorPlugin)
        self.register(LinkRewriterPlugin)
    
    def register(self, plugin_class: type):
        """Register a plugin class"""
        # Instantiate temporarily to get info
        plugin = plugin_class()
        info = plugin.get_info()
        self._plugins[info.name] = plugin_class
    
    def create(self, name: str, config=None) -> Optional[ExportPlugin]:
        """Create plugin instance"""
        plugin_class = self._plugins.get(name)
        if plugin_class:
            return plugin_class(config)
        return None
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all available plugins"""
        return [cls().get_info() for cls in self._plugins.values()]
    
    def exists(self, name: str) -> bool:
        """Check if plugin exists"""
        return name in self._plugins

# Global registry instance
registry = PluginRegistry()
```

### Updated WikiExporter

```python
# app/services/archive_export.py (updated)

from .export_plugins import registry as plugin_registry

class WikiExporter:
    """Main exporter class with plugin support"""
    
    def __init__(self, wiki_id: int, profile_name: str = None, options: ExportOptions = None):
        # ... existing initialization ...
        
        # Get plugins from profile
        self.plugins: List[ExportPlugin] = self.profile.get_plugins()
        
        # Sort plugins by priority
        self.plugins.sort(key=lambda p: p.config.priority)
    
    def add_plugin(self, plugin: ExportPlugin):
        """Add custom plugin"""
        self.plugins.append(plugin)
        self.plugins.sort(key=lambda p: p.config.priority)
    
    def export(self) -> ExportResult:
        """Execute export with plugin support"""
        try:
            # ... existing export setup ...
            
            # Build context for plugins
            page_map = {}  # Maps page ID to export path
            
            # Process pages
            for page in pages:
                page_data = self._build_page_data(page)
                
                # Apply page-level plugins
                for plugin in self.plugins:
                    if plugin.config.enabled:
                        try:
                            page_data = plugin.process_page(page_data)
                        except Exception as e:
                            logger.error(f"Plugin {plugin.get_info().name} failed: {e}")
                
                # Write page
                self._write_page(page_data, temp_dir)
                page_map[page.id] = page_data['path']
            
            # Process attachments
            # ...
            
            # Build context for archive-level plugins
            context = {
                'wiki': wiki,
                'pages': pages,
                'page_map': page_map,
                'attachments': attachments
            }
            
            # Apply archive-level plugins
            for plugin in self.plugins:
                if plugin.config.enabled:
                    try:
                        plugin.process_archive(temp_dir, context)
                    except Exception as e:
                        logger.error(f"Plugin {plugin.get_info().name} failed: {e}")
            
            # ... rest of export ...
            
        except Exception as e:
            # ... error handling ...
    
    def _build_page_data(self, page) -> Dict[str, Any]:
        """Build page data dictionary for plugins"""
        return {
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'content': page.content or '',
            'parent_id': page.parent_id,
            'path': self._get_page_path(page),
            'attachments': self._get_page_attachments(page)
        }
```

### Example: GitHub Profile with Plugins

```python
# app/services/export_profiles/github.py (future)

from .base import ExportProfile, ProfileInfo
from ..export_plugins import registry as plugin_registry
from ..export_plugins.base import PluginConfig

class GitHubProfile(ExportProfile):
    """Profile for GitHub Wiki export"""
    
    def get_info(self) -> ProfileInfo:
        return ProfileInfo(
            name='github',
            display_name='GitHub Wiki',
            description='Export formatted for GitHub Wiki with sidebar and link rewriting'
        )
    
    def get_plugins(self) -> List[ExportPlugin]:
        """Return plugins for GitHub export"""
        return [
            plugin_registry.create('sidebar_generator'),
            plugin_registry.create('link_rewriter', PluginConfig(
                options={'convert_wikilinks': True}
            ))
        ]
    
    def transform_content(self, content: str, page_data: Dict[str, Any]) -> str:
        """GitHub-specific transformations"""
        # Transform any remaining DanWiki syntax to GitHub format
        return content
```

## Plugin Configuration

### Profile-Specific Plugin Configuration

```python
# Example: Configure plugins in a profile
class CustomProfile(ExportProfile):
    def get_plugins(self) -> List[ExportPlugin]:
        return [
            plugin_registry.create('sidebar_generator', PluginConfig(
                enabled=True,
                priority=10,
                options={
                    'include_home_link': True,
                    'max_depth': 3
                }
            )),
            plugin_registry.create('link_rewriter', PluginConfig(
                enabled=True,
                priority=20,
                options={
                    'convert_wikilinks': True,
                    'relative_paths': True
                }
            ))
        ]
```

## Testing Requirements

### Unit Tests

```python
# tests/services/test_export_plugins.py

class TestSidebarGeneratorPlugin:
    def test_plugin_info(self):
        """Test plugin metadata"""
        
    def test_sidebar_generation(self):
        """Test sidebar content is correct"""
        
    def test_nested_pages(self):
        """Test nested page structure in sidebar"""
        
    def test_page_ordering(self):
        """Test pages ordered correctly in sidebar"""

class TestLinkRewriterPlugin:
    def test_plugin_info(self):
        """Test plugin metadata"""
        
    def test_internal_link_rewriting(self):
        """Test internal links rewritten correctly"""
        
    def test_wikilink_conversion(self):
        """Test wikilink format conversion"""
        
    def test_broken_link_handling(self):
        """Test handling of unresolvable links"""

class TestPluginRegistry:
    def test_register_plugin(self):
        """Test registering custom plugin"""
        
    def test_create_plugin(self):
        """Test creating plugin instance"""
        
    def test_list_plugins(self):
        """Test listing all plugins"""
        
    def test_plugin_priority_ordering(self):
        """Test plugins ordered by priority"""
```

### Integration Tests

```python
# tests/integration/test_plugin_export.py

class TestPluginExport:
    def test_export_with_sidebar_plugin(self):
        """Test export generates sidebar file"""
        
    def test_export_with_link_rewriter(self):
        """Test export rewrites links correctly"""
        
    def test_export_with_multiple_plugins(self):
        """Test export with plugin chain"""
        
    def test_plugin_error_handling(self):
        """Test export continues when plugin fails"""
        
    def test_profile_with_plugins(self):
        """Test profile-specified plugins execute"""
```

## Plugin Development Guide

### Creating a Custom Plugin

```python
from app.services.export_plugins.base import ExportPlugin, PluginInfo, PluginConfig
from pathlib import Path
from typing import Dict, Any

class MyCustomPlugin(ExportPlugin):
    """My custom export plugin"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name='my_plugin',
            display_name='My Plugin',
            description='Does something awesome',
            version='1.0.0',
            author='Your Name'
        )
    
    def process_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual page"""
        # Modify page_data['content']
        # Add page_data['custom_field']
        return page_data
    
    def process_archive(self, temp_dir: Path, context: Dict[str, Any]) -> None:
        """Process entire archive"""
        # Generate additional files
        # Modify existing files
        pass

# Register plugin
from app.services.export_plugins import registry
registry.register(MyCustomPlugin)
```

## Success Criteria

- ✓ ExportPlugin base class provides clear extension pattern
- ✓ Plugins can transform page content
- ✓ Plugins can generate additional files
- ✓ Plugin execution order respects priority
- ✓ Plugin errors don't crash export
- ✓ SidebarGeneratorPlugin creates valid sidebar
- ✓ LinkRewriterPlugin rewrites links correctly
- ✓ All unit tests pass
- ✓ All integration tests pass
- ✓ Plugin development guide is clear

## Next Phase

After Phase 4 completion, proceed to **Phase 5: Advanced Profiles** to implement platform-specific export profiles (GitHub, VS Code, Obsidian, etc.).

---

## Progress Tracking

### Feature 1: ExportPlugin Base Class
- [ ] Create `app/services/export_plugins/` directory
- [ ] Create `base.py` file
- [ ] Define `PluginConfig` dataclass
- [ ] Define `PluginInfo` dataclass
- [ ] Define `ExportPlugin` abstract class
- [ ] Add `__init__()` method with config
- [ ] Add `get_info()` abstract method
- [ ] Add `process_page()` abstract method
- [ ] Add `process_archive()` method with default implementation
- [ ] Add `validate_config()` method
- [ ] Document page_data structure
- [ ] Document context structure
- [ ] Add type hints to all methods

### Feature 2: Plugin Registry
- [ ] Create `__init__.py` in export_plugins
- [ ] Create PluginRegistry class
- [ ] Add `_plugins` dictionary
- [ ] Implement `__init__()` method
- [ ] Implement `_register_default_plugins()`
- [ ] Implement `register()` method
- [ ] Implement `create()` method
- [ ] Implement `list_plugins()` method
- [ ] Implement `exists()` method
- [ ] Create global registry instance
- [ ] Test registry operations

### Feature 3: SidebarGeneratorPlugin
- [ ] Create `sidebar_generator.py` file
- [ ] Create SidebarGeneratorPlugin class
- [ ] Implement `get_info()` method
- [ ] Implement `process_page()` method (no-op)
- [ ] Implement `process_archive()` method
- [ ] Implement `_generate_sidebar_content()` helper
- [ ] Implement `_generate_page_entry()` helper
- [ ] Build tree structure from flat page list
- [ ] Sort pages by order attribute
- [ ] Handle nested pages with indentation
- [ ] Generate markdown links
- [ ] Write _Sidebar.md file
- [ ] Test sidebar generation

### Feature 4: LinkRewriterPlugin
- [ ] Create `link_rewriter.py` file
- [ ] Create LinkRewriterPlugin class
- [ ] Implement `get_info()` method
- [ ] Add link_map instance variable
- [ ] Implement `process_page()` method
- [ ] Build page ID to path mapping
- [ ] Implement link pattern matching (regex)
- [ ] Implement `_rewrite_link()` helper
- [ ] Handle /wiki/ID and /pages/ID patterns
- [ ] Make paths relative
- [ ] Implement wikilink conversion (optional)
- [ ] Implement `_convert_wikilink()` helper
- [ ] Handle unresolvable links gracefully
- [ ] Test link rewriting

### Feature 5: Update WikiExporter for Plugins
- [ ] Import plugin_registry in archive_export.py
- [ ] Get plugins from profile in `__init__()`
- [ ] Sort plugins by priority
- [ ] Implement `add_plugin()` method
- [ ] Create `_build_page_data()` helper
- [ ] Build page_data dictionary
- [ ] Apply page-level plugins in export loop
- [ ] Wrap plugin calls in try-catch
- [ ] Log plugin errors
- [ ] Create `_write_page()` helper
- [ ] Build context dictionary for archive plugins
- [ ] Apply archive-level plugins
- [ ] Call `plugin.process_archive()` for each
- [ ] Test exporter with plugins

### Feature 6: Plugin Error Handling
- [ ] Add error handling around plugin calls
- [ ] Log plugin errors with details
- [ ] Continue export if plugin fails
- [ ] Track failed plugins in ExportResult
- [ ] Add plugin_errors field to ExportResult
- [ ] Report plugin failures to user
- [ ] Test plugin error scenarios

### Feature 7: Plugin Priority System
- [ ] Use PluginConfig.priority for ordering
- [ ] Sort plugins by priority before execution
- [ ] Test priority ordering
- [ ] Document priority ranges (0-100)
- [ ] Test plugins execute in correct order

### Feature 8: Plugin Configuration
- [ ] Support plugin options via PluginConfig
- [ ] Pass config to plugin constructor
- [ ] Access config in plugin methods
- [ ] Implement `validate_config()` checks
- [ ] Test plugin configuration

### Feature 9: Update Profile for Plugins
- [ ] Update BackupProfile.get_plugins() (empty list)
- [ ] Update PlainProfile.get_plugins() (empty list)
- [ ] Test profiles with no plugins
- [ ] Document how profiles specify plugins

### Feature 10: Plugin API Endpoint (Optional)
- [ ] Add route GET `/api/wikis/plugins`
- [ ] Call registry.list_plugins()
- [ ] Format plugin info for JSON
- [ ] Test endpoint returns plugins
- [ ] Document endpoint

### Feature 11: Unit Tests - SidebarGenerator
- [ ] Write test: plugin get_info()
- [ ] Write test: sidebar file created
- [ ] Write test: sidebar has correct structure
- [ ] Write test: nested pages indented correctly
- [ ] Write test: pages ordered correctly
- [ ] Write test: links formatted correctly
- [ ] Run sidebar plugin tests

### Feature 12: Unit Tests - LinkRewriter
- [ ] Write test: plugin get_info()
- [ ] Write test: internal links rewritten
- [ ] Write test: /wiki/ID pattern handled
- [ ] Write test: /pages/ID pattern handled
- [ ] Write test: wikilinks converted
- [ ] Write test: broken links handled gracefully
- [ ] Write test: relative paths correct
- [ ] Run link rewriter tests

### Feature 13: Unit Tests - Registry
- [ ] Write test: register plugin
- [ ] Write test: create plugin instance
- [ ] Write test: list plugins
- [ ] Write test: check plugin exists
- [ ] Write test: default plugins registered
- [ ] Run registry tests

### Feature 14: Integration Tests
- [ ] Write test: export with sidebar plugin
- [ ] Write test: verify sidebar file exists
- [ ] Write test: export with link rewriter
- [ ] Write test: verify links rewritten
- [ ] Write test: export with multiple plugins
- [ ] Write test: plugins execute in order
- [ ] Write test: plugin error doesn't crash export
- [ ] Write test: profile plugins execute
- [ ] Run integration tests

### Feature 15: Plugin Development Documentation
- [ ] Document ExportPlugin interface
- [ ] Document PluginConfig options
- [ ] Document page_data structure
- [ ] Document context structure
- [ ] Provide custom plugin example
- [ ] Document plugin registration
- [ ] Document plugin priorities
- [ ] Document error handling
- [ ] Add complete working example

### Feature 16: Manual Testing
- [ ] Test export with sidebar plugin
- [ ] Verify _Sidebar.md created
- [ ] Verify sidebar structure correct
- [ ] Test export with link rewriter
- [ ] Verify links rewritten correctly
- [ ] Test export with both plugins
- [ ] Verify plugin execution order
- [ ] Test plugin error handling
- [ ] Create custom test plugin
- [ ] Test custom plugin registration
