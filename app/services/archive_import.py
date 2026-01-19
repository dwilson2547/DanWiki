"""
Archive import service for bulk wiki page creation.
Supports zip and tar.gz archives with hierarchical directory structures.
"""
import os
import re
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from werkzeug.utils import secure_filename

from app.models import db, Wiki, Page, Attachment, Tag, User


class ImportResult:
    """Container for import operation results."""
    
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.pages_created = []
        self.attachments_created = []
        self.errors = []
        
    def add_success(self, page_title: str, page_id: int):
        """Record successful page creation."""
        self.success_count += 1
        self.pages_created.append({'title': page_title, 'id': page_id})
    
    def add_attachment(self, filename: str, attachment_id: int):
        """Record successful attachment creation."""
        self.attachments_created.append({'filename': filename, 'id': attachment_id})
    
    def add_error(self, item: str, error: str):
        """Record an error during import."""
        self.failure_count += 1
        self.errors.append({'item': item, 'error': error})
    
    def to_dict(self) -> dict:
        """Serialize result to dictionary."""
        return {
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'pages_created': self.pages_created,
            'attachments_created': self.attachments_created,
            'errors': self.errors,
            'total_processed': self.success_count + self.failure_count,
        }


class ArchiveImporter:
    """Service for importing wiki pages from archive files."""
    
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    MARKDOWN_EXTENSIONS = {'.md', '.markdown'}
    
    def __init__(self, wiki: Wiki, user: User, upload_folder: str):
        self.wiki = wiki
        self.user = user
        self.upload_folder = upload_folder
        self.result = ImportResult()
        self.tag_cache: Dict[str, Tag] = {}  # Cache tags by name
        
    def import_archive(self, archive_path: str, parent_page: Optional[Page] = None) -> ImportResult:
        """
        Import pages from an archive file.
        
        Args:
            archive_path: Path to the zip or tar.gz file
            parent_page: Optional parent page to import under (None = root level)
            
        Returns:
            ImportResult with success/failure counts and details
        """
        # Validate file size
        file_size = os.path.getsize(archive_path)
        if file_size > self.MAX_FILE_SIZE:
            self.result.add_error(
                archive_path, 
                f'Archive too large: {file_size / (1024*1024):.1f}MB (max: 500MB)'
            )
            return self.result
        
        # Create temporary extraction directory
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract archive
                self._extract_archive(archive_path, temp_dir)
                
                # Process the extracted files
                self._process_directory(Path(temp_dir), parent_page)
                
                # Note: Do NOT commit here - let the caller manage the transaction
                # This allows proper transaction handling if import fails
                
            except Exception as e:
                # Do NOT rollback here - let the caller manage the transaction
                # Just record the error and let caller decide what to do
                self.result.add_error(archive_path, f'Import failed: {str(e)}')
                # Re-raise the exception so the caller knows import failed
                raise
        
        return self.result
    
    def _extract_archive(self, archive_path: str, extract_to: str):
        """Extract zip or tar archive."""
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.endswith(('.tar.gz', '.tgz', '.tar')):
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise ValueError('Unsupported archive format. Use .zip or .tar.gz')
    
    def _process_directory(self, dir_path: Path, parent_page: Optional[Page] = None):
        """
        Recursively process directory structure.
        
        Directory structure maps to page hierarchy:
        - .md files become pages
        - Directories with matching .md file: files inside become children of that page
        - Directories without matching .md: create blank page for directory
        - Non-.md files become attachments to their parent page
        """
        # Get all items in this directory
        items = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
        
        # Separate markdown files, directories, and other files
        markdown_files = [f for f in items if f.is_file() and f.suffix.lower() in self.MARKDOWN_EXTENSIONS]
        directories = [d for d in items if d.is_dir() and not d.name.startswith('.')]
        attachment_files = [f for f in items if f.is_file() and f.suffix.lower() not in self.MARKDOWN_EXTENSIONS]
        
        # Create a local page map for this directory level only
        # This prevents name collisions across different parts of the tree
        local_page_map: Dict[str, Page] = {}
        
        # Process markdown files first
        for md_file in markdown_files:
            try:
                page = self._create_page_from_markdown(md_file, parent_page)
                if page:
                    # Map the file stem (without extension) to the page
                    # This allows matching directories to pages at THIS level
                    local_page_map[md_file.stem] = page
            except Exception as e:
                self.result.add_error(str(md_file), str(e))
        
        # Process directories
        for directory in directories:
            dir_name = directory.name
            
            # Check if there's a matching markdown file at THIS level
            if dir_name in local_page_map:
                # Directory contents become children of the matching page
                self._process_directory(directory, local_page_map[dir_name])
            else:
                # No matching .md file - create a blank page for this directory
                try:
                    blank_page = self._create_blank_page(dir_name, parent_page)
                    # Process directory contents as children of the blank page
                    self._process_directory(directory, blank_page)
                except Exception as e:
                    self.result.add_error(dir_name, str(e))
        
        # Process attachments (non-markdown files)
        if attachment_files and parent_page:
            for att_file in attachment_files:
                try:
                    self._create_attachment(att_file, parent_page)
                except Exception as e:
                    self.result.add_error(str(att_file), str(e))
    
    def _create_page_from_markdown(self, md_file: Path, parent: Optional[Page] = None) -> Optional[Page]:
        """Create a page from a markdown file."""
        # Read file content
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 if UTF-8 fails
            with open(md_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Parse frontmatter and extract metadata
        title, tags, content_without_frontmatter = self._parse_frontmatter(content, md_file.stem)
        
        # If no title from frontmatter, try to extract from first H1
        if title == md_file.stem:  # Only filename was used
            h1_title = self._extract_first_h1(content_without_frontmatter)
            if h1_title:
                title = h1_title
        
        # Generate unique slug to avoid conflicts
        unique_slug = self._generate_unique_slug(title, parent.id if parent else None)
        
        # Create the page
        page = Page(
            title=title,
            slug=unique_slug,
            content=content_without_frontmatter.strip(),
            wiki_id=self.wiki.id,
            parent_id=parent.id if parent else None,
            created_by_id=self.user.id,
            last_modified_by_id=self.user.id,
            embeddings_status='pending'  # Will be processed by background task
        )
        
        db.session.add(page)
        db.session.flush()  # Get the page ID
        
        # Add tags if any
        if tags:
            for tag_name in tags:
                tag = self._get_or_create_tag(tag_name)
                page.tags.append(tag)
        
        self.result.add_success(title, page.id)
        return page
    
    def _create_blank_page(self, directory_name: str, parent: Optional[Page] = None) -> Page:
        """Create a blank page for a directory that has no matching .md file."""
        # Clean up directory name to use as title
        title = directory_name.replace('_', ' ').replace('-', ' ').title()
        
        # Generate unique slug to avoid conflicts
        unique_slug = self._generate_unique_slug(title, parent.id if parent else None)
        
        page = Page(
            title=title,
            slug=unique_slug,
            content='',
            wiki_id=self.wiki.id,
            parent_id=parent.id if parent else None,
            created_by_id=self.user.id,
            last_modified_by_id=self.user.id,
            embeddings_status='pending'
        )
        
        db.session.add(page)
        db.session.flush()
        
        self.result.add_success(title, page.id)
        return page
    
    def _create_attachment(self, file_path: Path, page: Page) -> Optional[Attachment]:
        """Create an attachment from a file."""
        import magic
        import uuid
        from datetime import datetime, timezone
        
        # Generate unique filename
        file_ext = file_path.suffix
        stored_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create upload directory for this page
        page_upload_dir = os.path.join(self.upload_folder, str(self.wiki.id), str(page.id))
        os.makedirs(page_upload_dir, exist_ok=True)
        
        # Copy file to uploads directory
        destination = os.path.join(page_upload_dir, stored_filename)
        import shutil
        shutil.copy2(file_path, destination)
        
        # Detect mime type
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(destination)
        except:
            mime_type = 'application/octet-stream'
        
        # Determine file type
        file_type = self._get_file_type(mime_type, file_ext.lstrip('.'))
        
        # Create attachment record
        attachment = Attachment(
            filename=file_path.name,
            stored_filename=stored_filename,
            file_path=destination,
            file_size=os.path.getsize(destination),
            mime_type=mime_type,
            file_type=file_type,
            page_id=page.id,
            uploaded_by_id=self.user.id
        )
        
        db.session.add(attachment)
        db.session.flush()
        
        self.result.add_attachment(file_path.name, attachment.id)
        return attachment
    
    def _parse_frontmatter(self, content: str, fallback_title: str) -> Tuple[str, List[str], str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Returns:
            (title, tags, content_without_frontmatter)
        """
        # Check for YAML frontmatter (--- at start and end)
        if not content.startswith('---'):
            return fallback_title, [], content
        
        # Find the end of frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return fallback_title, [], content
        
        try:
            # Parse YAML
            frontmatter = yaml.safe_load(parts[1])
            if not isinstance(frontmatter, dict):
                return fallback_title, [], content
            
            # Extract title
            title = frontmatter.get('title', fallback_title)
            
            # Extract tags
            tags = frontmatter.get('tags', [])
            if isinstance(tags, str):
                # Handle comma-separated tags
                tags = [t.strip() for t in tags.split(',')]
            elif not isinstance(tags, list):
                tags = []
            
            # Return content without frontmatter
            content_without_fm = parts[2].lstrip('\n')
            return title, tags, content_without_fm
            
        except yaml.YAMLError:
            # If YAML parsing fails, treat as regular content
            return fallback_title, [], content
    
    def _extract_first_h1(self, content: str) -> Optional[str]:
        """Extract the first H1 heading from markdown content."""
        # Match # Heading or Heading\n====
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # ATX-style heading: # Heading
            if line.startswith('# ') and not line.startswith('##'):
                return line[2:].strip()
            
            # Setext-style heading: Heading\n====
            if i > 0 and line.strip() and all(c == '=' for c in line.strip()):
                prev_line = lines[i-1].strip()
                if prev_line:
                    return prev_line
        
        return None
    
    def _get_or_create_tag(self, tag_name: str) -> Tag:
        """Get existing tag or create new one."""
        # Clean tag name
        tag_name = tag_name.strip().lower()
        
        # Check cache
        if tag_name in self.tag_cache:
            return self.tag_cache[tag_name]
        
        # Check database
        tag = Tag.query.filter_by(wiki_id=self.wiki.id, name=tag_name).first()
        if not tag:
            # Create new tag
            tag = Tag(name=tag_name, wiki_id=self.wiki.id)
            db.session.add(tag)
            db.session.flush()
        
        # Cache it
        self.tag_cache[tag_name] = tag
        return tag
    
    def _generate_unique_slug(self, base_title: str, parent_id: Optional[int] = None) -> str:
        """Generate a unique slug for a page within the wiki.
        
        Note: Slugs must be unique across the entire wiki, not just within the same parent,
        due to the database constraint on (wiki_id, slug).
        """
        from slugify import slugify
        
        base_slug = slugify(base_title)
        slug = base_slug
        counter = 1
        
        # Check if slug already exists anywhere in this wiki
        while Page.query.filter_by(wiki_id=self.wiki.id, slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _get_file_type(self, mime_type: str, extension: str) -> str:
        """Determine file type category from mime type or extension."""
        image_types = {'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml'}
        if mime_type in image_types or extension in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}:
            return 'image'
        
        doc_types = {
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'text/markdown', 'text/csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        if mime_type in doc_types or extension in {'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'xlsx'}:
            return 'document'
        
        code_types = {
            'text/javascript', 'application/javascript', 'text/html', 'text/css',
            'application/json', 'text/x-python', 'application/x-yaml'
        }
        if mime_type in code_types or extension in {'py', 'js', 'ts', 'html', 'css', 'json', 'yaml', 'yml'}:
            return 'code'
        
        return 'other'
