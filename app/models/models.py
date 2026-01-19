from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from slugify import slugify
from pgvector.sqlalchemy import Vector
import bcrypt

db = SQLAlchemy()


# Association tables for many-to-many relationships
wiki_members = db.Table(
    'wiki_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('wiki_id', db.Integer, db.ForeignKey('wikis.id'), primary_key=True),
    db.Column('role', db.String(20), default='viewer'),  # viewer, editor, admin
    db.Column('joined_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)

page_tags = db.Table(
    'page_tags',
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc))
)


class User(db.Model):
    """User model with authentication and wiki membership."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # System-wide admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owned_wikis = db.relationship('Wiki', back_populates='owner', lazy='dynamic')
    wikis = db.relationship('Wiki', secondary=wiki_members, back_populates='members')
    pages_created = db.relationship('Page', back_populates='created_by', 
                                    foreign_keys='Page.created_by_id', lazy='dynamic')
    pages_modified = db.relationship('Page', back_populates='last_modified_by',
                                     foreign_keys='Page.last_modified_by_id', lazy='dynamic')
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def get_wiki_role(self, wiki_id: int) -> str | None:
        """Get user's role in a specific wiki."""
        result = db.session.execute(
            db.select(wiki_members.c.role)
            .where(wiki_members.c.user_id == self.id)
            .where(wiki_members.c.wiki_id == wiki_id)
        ).scalar()
        return result
    
    def can_edit_wiki(self, wiki_id: int) -> bool:
        """Check if user can edit a wiki."""
        wiki = Wiki.query.get(wiki_id)
        if not wiki:
            return False
        if wiki.owner_id == self.id or self.is_admin:
            return True
        role = self.get_wiki_role(wiki_id)
        return role in ('editor', 'admin')
    
    def can_admin_wiki(self, wiki_id: int) -> bool:
        """Check if user can administer a wiki."""
        wiki = Wiki.query.get(wiki_id)
        if not wiki:
            return False
        if wiki.owner_id == self.id or self.is_admin:
            return True
        return self.get_wiki_role(wiki_id) == 'admin'
    
    def to_dict(self, include_email: bool = False) -> dict:
        """Serialize user to dictionary."""
        data = {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
        return data


class Wiki(db.Model):
    """Wiki container that holds pages."""
    __tablename__ = 'wikis'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, index=True)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    owner = db.relationship('User', back_populates='owned_wikis')
    members = db.relationship('User', secondary=wiki_members, back_populates='wikis')
    pages = db.relationship('Page', back_populates='wiki', lazy='dynamic',
                           cascade='all, delete-orphan')
    
    # Unique constraint on slug per owner
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'slug', name='unique_wiki_slug_per_owner'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.name and not self.slug:
            self.slug = slugify(self.name)
    
    def add_member(self, user: User, role: str = 'viewer') -> None:
        """Add a member to the wiki with a specified role."""
        if user not in self.members:
            stmt = wiki_members.insert().values(
                user_id=user.id,
                wiki_id=self.id,
                role=role
            )
            db.session.execute(stmt)
    
    def update_member_role(self, user: User, role: str) -> None:
        """Update a member's role in the wiki."""
        stmt = wiki_members.update().where(
            wiki_members.c.user_id == user.id,
            wiki_members.c.wiki_id == self.id
        ).values(role=role)
        db.session.execute(stmt)
    
    def remove_member(self, user: User) -> None:
        """Remove a member from the wiki."""
        stmt = wiki_members.delete().where(
            wiki_members.c.user_id == user.id,
            wiki_members.c.wiki_id == self.id
        )
        db.session.execute(stmt)
    
    def get_root_pages(self):
        """Get all top-level pages (no parent)."""
        return self.pages.filter(Page.parent_id.is_(None)).order_by(Page.title)
    
    def to_dict(self, include_pages: bool = False) -> dict:
        """Serialize wiki to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'is_public': self.is_public,
            'owner': self.owner.to_dict() if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_pages:
            data['pages'] = [p.to_dict() for p in self.get_root_pages()]
        return data


class Page(db.Model):
    """Wiki page with hierarchical structure (parent-child pages)."""
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(320), nullable=False, index=True)
    content = db.Column(db.Text, default='')  # Markdown content
    summary = db.Column(db.String(500))  # Short description for search/preview
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)  # For ordering siblings
    
    # Embedding status tracking
    embeddings_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    embeddings_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys
    wiki_id = db.Column(db.Integer, db.ForeignKey('wikis.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    last_modified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    wiki = db.relationship('Wiki', back_populates='pages')
    parent = db.relationship('Page', back_populates='children', remote_side=[id])
    children = db.relationship('Page', back_populates='parent', lazy='dynamic',
                               order_by='Page.sort_order, Page.title',
                               cascade='all, delete-orphan')
    created_by = db.relationship('User', foreign_keys=[created_by_id],
                                 back_populates='pages_created')
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id],
                                       back_populates='pages_modified')
    attachments = db.relationship('Attachment', back_populates='page', lazy='dynamic',
                                  cascade='all, delete-orphan')
    embeddings = db.relationship('PageEmbedding', back_populates='page', lazy='dynamic',
                                 cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=page_tags, back_populates='pages')
    
    # Unique constraint on slug within a wiki
    __table_args__ = (
        db.UniqueConstraint('wiki_id', 'slug', name='unique_page_slug_per_wiki'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.title and not self.slug:
            self.slug = slugify(self.title)
    
    def get_breadcrumbs(self) -> list[dict]:
        """Get the path from root to this page."""
        breadcrumbs = []
        page = self
        while page:
            breadcrumbs.insert(0, {'id': page.id, 'title': page.title, 'slug': page.slug})
            page = page.parent
        return breadcrumbs
    
    def get_full_path(self) -> str:
        """Get the full URL path for this page."""
        parts = [p['slug'] for p in self.get_breadcrumbs()]
        return '/'.join(parts)
    
    def get_descendants(self) -> list['Page']:
        """Get all descendant pages (children, grandchildren, etc.)."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def move_to_parent(self, new_parent: 'Page | None') -> None:
        """Move this page to a new parent (or root if None)."""
        # Prevent circular references
        if new_parent:
            current = new_parent
            while current:
                if current.id == self.id:
                    raise ValueError("Cannot move page to its own descendant")
                current = current.parent
        self.parent = new_parent
    
    def to_dict(self, include_content: bool = False, include_children: bool = False) -> dict:
        """Serialize page to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'summary': self.summary,
            'is_published': self.is_published,
            'sort_order': self.sort_order,
            'wiki_id': self.wiki_id,
            'parent_id': self.parent_id,
            'full_path': self.get_full_path(),
            'breadcrumbs': self.get_breadcrumbs(),
            'created_by': self.created_by.to_dict() if self.created_by else None,
            'last_modified_by': self.last_modified_by.to_dict() if self.last_modified_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'attachment_count': self.attachments.count(),
            'tags': [tag.to_dict() for tag in self.tags],
        }
        if include_content:
            data['content'] = self.content
        if include_children:
            data['children'] = [c.to_dict(include_children=True) for c in self.children]
        return data


class Attachment(db.Model):
    """File attachment for a wiki page."""
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    stored_filename = db.Column(db.String(255), nullable=False)  # UUID-based stored name
    file_path = db.Column(db.String(500), nullable=False)  # Full path on disk
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    file_type = db.Column(db.String(20))  # image, document, code, other
    
    # Foreign keys
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    page = db.relationship('Page', back_populates='attachments')
    uploaded_by = db.relationship('User')
    
    def to_dict(self) -> dict:
        """Serialize attachment to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_type': self.file_type,
            'uploaded_by': self.uploaded_by.to_dict() if self.uploaded_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'url': f'/api/attachments/{self.id}/download',
        }


class PageRevision(db.Model):
    """Stores page revision history."""
    __tablename__ = 'page_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text)
    revision_number = db.Column(db.Integer, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    change_summary = db.Column(db.String(500))
    
    # Relationships
    page = db.relationship('Page')
    created_by = db.relationship('User')
    
    __table_args__ = (
        db.UniqueConstraint('page_id', 'revision_number', name='unique_revision_per_page'),
    )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'page_id': self.page_id,
            'title': self.title,
            'revision_number': self.revision_number,
            'created_by': self.created_by.to_dict() if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'change_summary': self.change_summary,
        }


class PageEmbedding(db.Model):
    """Store embeddings for page content chunks."""
    __tablename__ = 'page_embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)  # Order of chunk in page
    chunk_text = db.Column(db.Text, nullable=False)  # The actual text chunk
    heading_path = db.Column(db.String(500))  # e.g., "Introduction > Setup > Installation"
    token_count = db.Column(db.Integer)
    
    # pgvector column - dimension 384 for all-MiniLM-L6-v2
    # Can be updated to 768 for larger models like all-mpnet-base-v2
    embedding = db.Column(Vector(384))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    page = db.relationship('Page', back_populates='embeddings')
    
    # Unique constraint and vector index
    __table_args__ = (
        db.UniqueConstraint('page_id', 'chunk_index', name='unique_page_chunk'),
        # Vector similarity index - created via migration
        # db.Index('idx_page_embeddings_vector', 'embedding', postgresql_using='ivfflat'),
    )
    
    def to_dict(self, include_embedding: bool = False) -> dict:
        """Serialize embedding to dictionary."""
        data = {
            'id': self.id,
            'page_id': self.page_id,
            'chunk_index': self.chunk_index,
            'chunk_text': self.chunk_text[:200] + '...' if len(self.chunk_text) > 200 else self.chunk_text,
            'heading_path': self.heading_path,
            'token_count': self.token_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_embedding and self.embedding is not None:
            data['embedding'] = self.embedding
        return data


class Tag(db.Model):
    """Tag for categorizing pages."""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey('wikis.id'), nullable=False)
    color = db.Column(db.String(7))  # Hex color code like #FF5733
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # AI/Automation tracking fields
    source = db.Column(db.String(20), default='human')  # 'human', 'ai', 'automated', 'imported'
    auto_generated = db.Column(db.Boolean, default=False, nullable=False)  # True if created by automation
    confidence = db.Column(db.Float)  # Confidence score for AI-generated tags (0.0 to 1.0)
    model_name = db.Column(db.String(100))  # Name/version of AI model that generated the tag
    verified = db.Column(db.Boolean, default=False, nullable=False)  # True if reviewed/approved by human
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who verified the tag
    verified_at = db.Column(db.DateTime)  # When the tag was verified
    
    # Relationships
    wiki = db.relationship('Wiki')
    pages = db.relationship('Page', secondary=page_tags, back_populates='tags')
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])
    
    # Unique constraint on tag name per wiki
    __table_args__ = (
        db.UniqueConstraint('wiki_id', 'name', name='unique_tag_name_per_wiki'),
    )
    
    def to_dict(self) -> dict:
        """Serialize tag to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'wiki_id': self.wiki_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source': self.source,
            'auto_generated': self.auto_generated,
            'confidence': self.confidence,
            'model_name': self.model_name,
            'verified': self.verified,
            'verified_by_id': self.verified_by_id,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
