# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2026-01-24

### Added
- **Vector Search Recall Tuning**: Added configurable IVFFlat probe setting for pgvector searches
  - New `IVFFLAT_PROBES` config/env setting to improve recall when using IVFFlat indexes
  - Applied `SET LOCAL ivfflat.probes` in semantic and hybrid search queries
  - Rationale: higher probes increase recall and reduce missed matches when thresholding

### Changed
- **Semantic Similarity Scoring**: Fixed cosine similarity scaling in search queries
  - Adjusted similarity computation to $1 - (distance / 2)$ for pgvector cosine distance
  - Keeps scores in the expected $[0,1]$ range, matching API thresholds
  - Rationale: previous scaling forced lower thresholds and under-scored matches

- **Chunking Defaults & Granularity**: Standardized default chunk size to 256 tokens
  - `MAX_CHUNK_TOKENS` default set to 256 to match embedding model truncation limits
  - Removed `EMBEDDING_MAX_SEQ_LENGTH` variable in favor of a single chunk size source
  - Rationale: reduces truncation and aligns chunk size with embedding model context

- **Tokenizer Alignment**: Chunker now uses the sentence-transformers tokenizer for token counting
  - Uses model tokenizer via `transformers` with fallback to tiktoken/word-count
  - Rationale: token counts now match the embedding model’s true tokenization behavior

- **Heading Context Accuracy**: Chunk heading paths now derive from paragraph start offsets
  - Avoids `find()`-based position errors on repeated text or overlaps
  - Rationale: improves metadata correctness for search results and UI context

- **Documentation Updates**: Updated search docs and env examples to reflect new defaults
  - Chunk size defaults, probe tuning, and tokenizer behavior documented for operators

### Fixed
- **Search Threshold Sensitivity**: Corrected similarity scaling to prevent overly low thresholds
  - Results now align with documented $0$–$1$ similarity range

### Technical
- **Dependencies**: Added `transformers` to support model-accurate token counting

## [1.4.0] - 2026-01-21

### Added
- **User Account Approval System**: Added administrator approval requirement for new user registrations
  - New users must be approved by an administrator before they can log in
  - Added `is_approved` field to User model (default: False for new registrations)
  - Existing users automatically set to approved during migration
  - Admin panel now displays pending user count in dashboard statistics
  - New "Pending Approvals" page in admin panel for reviewing registrations
  - Admins can approve or reject pending users with confirmation dialogs
  - Registration page shows success message indicating pending approval status
  - Login page displays appropriate error message for unapproved accounts
  - Backend endpoints:
    - `GET /api/admin/pending-users` - List pending user approvals
    - `POST /api/admin/users/<id>/approve` - Approve a user
    - `POST /api/admin/users/<id>/reject` - Reject and delete a pending user
  - Frontend components:
    - AdminPendingUsers page with approve/reject actions
    - Dashboard stats card showing pending approval count
    - Navigation link to pending approvals in admin sidebar

## [1.3.3] - 2026-01-19

### Changed
- **Page Edit Tags Layout**: Improved tag management visibility and organization
  - Moved tags to their own dedicated row below the title header
  - Tags now span the full width for better visibility and easier management
  - Separated tags from the title input for cleaner visual hierarchy
  - Provides more horizontal space for tag display and editing

## [1.3.2] - 2026-01-19

### Changed
- **Page Edit Layout Improvement**: Reorganized page editor metadata fields for better workflow
  - Moved parent page selection, summary, and change summary fields above the editor
  - Fields now appear in a dedicated metadata section between the title and editor
  - Improved visual hierarchy with fields positioned under the page title
  - Removed footer section to provide more vertical space for the editor
  - Responsive layout with flexible field sizing for smaller screens

## [1.3.1] - 2026-01-19

### Fixed
- **Dark Mode Compatibility**: Fixed text visibility in ParentPageSelect dropdown when hovering over options in dark mode
  - Removed hardcoded fallback colors that caused invisible text on hover
  - Dropdown now properly uses theme CSS variables for both light and dark modes
- **Modal Overflow Issue**: Fixed ParentPageSelect dropdown causing modal overflow in page creation dialog
  - Dropdown menu now renders to document.body using menuPortalTarget
  - Menu appears in front of modal with proper z-index layering
  - Long page lists no longer cause the create page modal to overflow

## [1.3.0] - 2026-01-19

### Added
- **Enhanced Parent Page Selection**: Improved parent page dropdown with searchable interface and depth visualization
  - Replaced standard dropdowns with react-select searchable component
  - Visual depth indicators using tree-style characters (└─) to show page hierarchy
  - Real-time search filtering to quickly find parent pages by title
  - Consistent parent page selection experience across page creation and editing
  - Better visual clarity for nested page structures
  - New reusable `ParentPageSelect` component for maintainability

### Changed
- Parent page selection dropdowns now use react-select library for enhanced UX
- Page depth is now clearly indicated with visual tree characters instead of just spacing
- Search functionality allows filtering through large page hierarchies efficiently

## [1.2.1] - 2026-01-19

### Added
- **CLAUDE.md Repository Guide**: Created comprehensive guidance document for Claude Code
  - Project overview with all 5 core services
  - Common commands for development, database migrations, testing, and building
  - Architecture overview (backend routes, models, services, frontend structure, AI/ML components)
  - Key patterns for API conventions, database, and frontend development
  - Environment setup instructions
  - Documentation references

- **Enhanced Attachment Management**: Wiki-wide attachment browsing and improved UX
  - New `GET /api/wikis/<wiki_id>/attachments` endpoint to fetch all attachments across wiki pages
  - Attachments modal now shows all attachments from all pages in the wiki (not just current page)
  - Search functionality to filter attachments by filename, file type, or page name
  - 120x120px image previews for all image attachments
  - Separated attachments into two sections: "This Page" and "Other Pages"
  - Visual distinction with highlighted background for current page attachments
  - Smart delete functionality (only current page attachments can be deleted)
  - Enhanced attachment counter showing "X/Y" (current page / total wiki attachments)
  - Each attachment shows which page it belongs to for easy reference
  - Improved modal layout with better spacing and card-based design
  - Attachments remain shareable only within the same wiki (access control maintained)

### Changed
- **Attachment Modal UI**: Complete redesign of the attachments interface in page editor
  - Larger modal size (800px width) with scrollable content
  - Section headers with counts for each group
  - Better visual hierarchy with clear separation between sections
  - Upload button clarified as "Upload to this page"
  - More informative help text showing total wiki attachment count

## [1.2.0] - 2026-01-19

### Added
- **AI Tagging Microservice**: GPU-enabled FastAPI service for automated wiki page tagging using local LLMs
  - Standalone microservice running on GPU-enabled machines with HTTP/REST API
  - Gemma 2 2B model support with 4-bit quantization (configurable to other models up to 70B)
  - Bearer token authentication for all endpoints
  - Hybrid tag generation: LLM-based contextual analysis + semantic matching against existing tags
  - Sentence transformers for tag similarity matching to prevent tag proliferation
  - Four specialized prompt templates: detailed, quick, technical, and general
  - Synchronous `/analyze` endpoint for real-time tag generation
  - Asynchronous `/analyze/batch` endpoint for bulk processing via Redis Queue
  - Integration with existing RQ infrastructure using new `tagging` queue
  - Persistent job queue that survives service restarts
  - Support for multiple worker instances on different GPU machines
  - Confidence scoring (0.0-1.0) for each suggested tag
  - Category classification (technology, concept, domain, level, type, platform)
  - Tag embedding cache for faster similarity matching
  - GPU memory tracking and health monitoring
  - `/health` endpoint with GPU utilization metrics
  - `/info` endpoint with model capabilities and configuration details
  - `/jobs/{job_id}` endpoint for batch job status tracking
  - Comprehensive error handling and retry logic
  - Configurable via environment variables for easy model swapping
  - Complete API documentation via FastAPI's built-in Swagger UI
  
- **Tagging Service Components**:
  - `tagging_api/app.py`: FastAPI application with authentication and endpoints
  - `tagging_api/worker.py`: RQ worker for background batch processing
  - `tagging_api/config.py`: Environment-based configuration management
  - `tagging_api/models.py`: Pydantic models for request/response validation
  - `tagging_api/llm_service.py`: LLM loading, inference, and tag generation logic
  - `tagging_api/prompts/`: Modular prompt template system with registry
  - `tagging_api/requirements.txt`: All dependencies including transformers, FastAPI, RQ
  - `tagging_api/.env.example`: Comprehensive configuration template
  - `tagging_api/README_QUICK.md`: Quick start guide
  - `tagging_api/readme.md`: Full requirements and architecture documentation

- **Documentation**:
  - Comprehensive requirements document covering architecture, API design, model options, deployment
  - 8 recommended model options ranked by size (2B to 70B parameters)
  - Prompt engineering guidelines and templates
  - Integration patterns with wiki application
  - Performance targets and monitoring recommendations
  - Security considerations and best practices
  - Development roadmap with phased implementation plan

### Technical
- **Model Support**: Gemma 2 2B (default), Phi-3 Mini, Gemma 2 9B, Llama 3.1, Mistral 7B, and more
- **Quantization**: 4-bit and 8-bit quantization support via BitsAndBytes
- **Hardware Requirements**: 8GB+ VRAM for small models, 40GB+ for large models
- **Queue Architecture**: Persistent Redis Queue with FIFO ordering and automatic retry
- **Caching Strategy**: Tag embedding cache with configurable TTL
- **Resource Management**: One request per worker to prevent GPU OOM
- **Dependencies**: torch, transformers, accelerate, bitsandbytes, sentence-transformers, FastAPI, RQ

## [1.1.3] - 2026-01-19

### Added
- **404 Not Found Page**: User-friendly error page for broken or invalid links
  - Custom NotFound component with helpful messaging and navigation options
  - "Go Back" button to return to previous page
  - "Go to Home" button for quick navigation to homepage
  - Helpful tips section explaining common causes and solutions
  - Consistent styling with existing design system using CSS variables
  - Replaces generic redirect behavior for better user experience
  - Handles broken wiki links and non-existent page routes gracefully

## [1.1.2] - 2026-01-19

### Fixed
- **Attachment Viewing Authentication**: Fixed 401 UNAUTHORIZED errors when viewing uploaded images
  - Modified `/api/attachments/<id>/view` and `/api/attachments/<id>/download` endpoints to support optional JWT authentication
  - Added query parameter authentication fallback (`?token=...`) for browser image requests
  - Public wiki attachments now viewable without authentication
  - Frontend dynamically adds auth tokens to attachment URLs after rendering
  - Implemented post-processing in PageView to append tokens to `<img>` tags
  - Added MutationObserver in MarkdownEditor to handle preview pane images
  - Stored markdown remains clean without embedded tokens (prevents token expiration issues)

- **Attachment Insert Button**: Fixed non-functional insert button in attachments modal during page editing
  - Converted MarkdownEditor to forwardRef component with useImperativeHandle
  - Added `insertText()` method to insert markdown at current cursor position
  - Fixed insert button to properly interact with Toast UI Editor instance instead of React state
  - Added insert functionality for non-image attachments (creates download links)
  - Image attachments insert as `![filename](url)`, other files as `[filename](url)`
  - Modal automatically closes after successful insertion

## [1.1.1] - 2026-01-19

### Fixed
- **Layout & Scrolling**: Fixed main content and sidebar layout issues
  - Fixed main content width calculation to properly account for resizable sidebar
  - Made sidebar fixed position for consistent visibility across all pages
  - Implemented independent scrolling for sidebar and main content areas
  - Added responsive max-width (1200px) to page content for optimal readability
  - Prevented content overflow that was hiding the sidebar
  - Improved smooth transitions when toggling or resizing sidebar

## [1.1.0] - 2026-01-18

### Added
- **Tag Management System**: Full-featured tagging system for wiki pages
  - Create, edit, and delete tags with custom colors
  - Add and remove tags from pages in both view and edit modes
  - Visual tag badges with color customization
  - Reusable TagManager React component
  - Tag API endpoints for CRUD operations
  - Page-level tag associations with many-to-many relationship
  - Random color picker for new tags
  - Real-time tag updates without page refresh
  
- **AI Tag Tracking**: Comprehensive metadata for automated tagging systems
  - `source` field to distinguish human/AI/automated/imported tags
  - `auto_generated` boolean flag for quick filtering
  - `confidence` score (0.0-1.0) for AI-generated tags
  - `model_name` field to track which AI model/version created tags
  - `verified` status for human review of AI tags
  - `verified_by_id` and `verified_at` for audit trail
  - Visual indicators: Bot icon for AI tags, User icon for human tags, Check icon for verified tags
  - Tag verification endpoint for human-in-the-loop workflows
  - Hover tooltips showing confidence scores and model information
  - Database migration for new tag tracking fields
  
- **Tag UI Features**:
  - Existing tag selection dropdown with color-coded buttons
  - New tag creation form with color picker
  - Tag removal with confirmation
  - Permission-based editing (editors can modify, viewers see read-only)
  - Dark theme support for all tag components
  - AI/automation badges and verification indicators
  - Dedicated tag styling with special borders for AI-generated tags
  
- **Documentation**: AI Tagging Integration Guide
  - Comprehensive guide for integrating tagging microservices
  - API usage examples for AI tag generation
  - Best practices for confidence thresholds and verification
  - Example tagging service implementation
  - Database schema reference
  - Future enhancement suggestions

### Changed
- **Tag Model**: Extended Tag model with AI/automation tracking fields
- **API Routes**: Enhanced tag routes to handle AI metadata in create/update operations
- **Frontend Components**: Updated PageView and PageEdit to include tag management

## [Unreleased]

### Added
- **Admin Panel**: Comprehensive administrative interface for platform management
  - User Management: View, search, edit, and deactivate user accounts with pagination
  - Wiki Management: View all wikis (flat or grouped by owner), delete wikis, transfer ownership
  - Embeddings Management: View pages without embeddings, manually trigger embedding generation (individual or bulk)
  - Admin-only access protected by `@require_admin` decorator
  - Consistent UI with adjustable sidebar matching main application design
  - Quick action dashboard with statistics overview

### Fixed
- **Admin Wiki Management Grouping**: Fixed SQL error when grouping wikis by owner in admin panel
  - Issue: User table wasn't joined to query when `group_by=owner` parameter was used
  - Error: `psycopg2.errors.UndefinedTable: missing FROM-clause entry for table "users"`
  - Solution: Added User table join whenever grouping by owner or searching by username
  - Admin can now successfully view wikis organized by their owners

- **Site Admin Access Permissions**: Fixed 403 errors when admins tried to access private wikis
  - Updated all wiki routes to check `user.is_admin` before denying access
  - Admins can now view, edit, and manage any wiki regardless of ownership or membership
  - Updated routes: `get_wiki()`, `update_wiki()`, `list_members()`, `add_member()`, `update_member()`, `remove_member()`
  - Updated `get_accessible_wiki_ids()` in search and semantic search routes to return all wikis for admins
  - Updated bulk import routes to allow admins to import to any wiki
  - Pages routes already had admin support via `check_wiki_access()` function

- **Bulk Import Transaction Management**: Fixed silent failure during wiki creation from archive
  - Wiki objects were being flushed but rolled back on import errors, causing 404 errors after navigation
  - Moved wiki creation inside try block for proper transaction control
  - Removed inappropriate `db.session.rollback()` and `db.session.commit()` calls from `ArchiveImporter` service
  - Transaction lifecycle now properly managed by endpoint layer only
  - Added comprehensive error logging with stack traces for debugging
  
- **Slug Uniqueness in Bulk Import**: Fixed duplicate slug constraint violations during archive import
  - Added automatic unique slug generation with incremental suffixes (`page-1`, `page-2`, etc.)
  - Implemented `_generate_unique_slug()` method in `ArchiveImporter` 
  - Updated `generate_unique_slug()` in pages route to match database constraint
  - Fixed to check wiki-level uniqueness (not parent-level) per `unique_page_slug_per_wiki` constraint
  - Prevents import failures when archive contains files/directories with duplicate names
  
- **Page Map Scope in Archive Import**: Fixed name collision bug in hierarchical imports
  - Changed `page_map` from instance variable to local variable scoped per directory level
  - Prevents cross-contamination when same file/directory names appear in different parts of tree
  - Example: `/tools/3d_scanner/` and `/projects/3d_scanner/` no longer interfere with each other

- **Page Creation Slug Conflicts**: Applied same unique slug generation to standard page creation
  - Manual page creation now auto-generates unique slugs instead of returning 409 errors
  - Page updates with conflicting slugs automatically adjusted to unique values
  - Consistent behavior across all page creation methods (manual, bulk import, API)

- **Anchor Link Navigation**: Fixed table of contents anchor links not working in wiki pages
  - Dynamically generates and assigns IDs to headings in rendered markdown (ToastUI doesn't add them by default)
  - Implements slug generation matching markdown processor conventions (lowercase, hyphenated)
  - Adds click handler for smooth scrolling to heading anchors
  - Compensates for fixed header height with offset calculation to prevent headings from hiding under header
  - Properly updates URL hash on navigation

- **Prism.js Syntax Highlighting Error**: Fixed "Cannot read properties of undefined (reading 'tokenizePlaceholders')" error
  - Added required base dependencies (`prism-clike`, `prism-markup`, `prism-markup-templating`) before language components
  - Ensures proper dependency order for JSX, TSX, PHP, and other templating languages
  - Fixes white screen crash when viewing pages with code blocks
  
- **Dark Mode Theme Support for Editor**: Toast UI Editor and Viewer now properly support dark mode
  - Imported Toast UI dark theme CSS (`toastui-editor-dark.css`)
  - Added theme prop to both Editor and Viewer components
  - Implemented theme context integration for automatic theme switching
  - Added `key` prop to force component remount on theme change for immediate visual update
  - Editor content is now readable in dark mode without requiring page refresh

### Changed
- **Markdown Editor Configuration**: Disabled ToastUI usage statistics to prevent telemetry prompts
  - Added `usageStatistics={false}` to Editor component
  - Added `autofocus={false}` for better UX

### Added
- **Public Home Page**: Created a public-facing landing page that displays all public wikis organized by author
  - Users can browse public wikis without authentication
  - Search functionality to filter wikis
  - Responsive card layout with author avatars and wiki metadata
  - Added `/api/wikis/public` endpoint with pagination and search support

- **AI-Powered Semantic Search**: Full semantic search implementation using locally-run open source models
  - Vector similarity search using PostgreSQL with pgvector extension
  - sentence-transformers/all-MiniLM-L6-v2 model for 384-dimension embeddings
  - Automatic background embedding generation via Redis Queue (RQ) when pages are created or edited
  - Intelligent markdown-aware text chunking for long documents (~400 tokens with 50 token overlap)
  - GPU-accelerated Flask microservice for embedding generation
  - Three search modes: AI Search (semantic only), Hybrid (semantic + keyword), and Traditional (keyword only)
  - Dedicated AI Search page with reusable search component
  - Adjustable search parameters (similarity threshold, hybrid search weight)
  - Rich result cards showing relevance scores and matched content snippets
  
- **User Settings Page**: Comprehensive user settings interface with multiple sections
  - Profile management: Upload/remove avatar, update display name
  - Appearance settings: Light/dark theme toggle
  - Wiki management: View all owned wikis with quick access to edit permissions or delete
  - Danger Zone: Account deletion options (with or without associated wikis)
  
- **User Menu Component**: Replaced static logout buttons with interactive user dropdown menu
  - Displays user avatar or initials
  - Quick access to user settings
  - Theme toggle button
  - Logout option
  - Click-outside detection for smooth UX
  
- **Dark Mode Support**: Full theming system with light and dark mode
  - Theme persistence via localStorage
  - System preference detection
  - CSS custom properties for consistent theming across all components
  - Theme-aware syntax highlighting for code blocks
  
- **Syntax Highlighting**: Integrated Prism.js for code block highlighting in markdown
  - Support for 30+ programming languages (JavaScript, TypeScript, Python, Java, C/C++, Go, Rust, SQL, etc.)
  - Custom theme that adapts to light/dark mode
  - Applied to both markdown editor and page viewer
  - Uses Toast UI Editor plugin for seamless integration
  
- **Account Deletion API**: New `/api/auth/me` DELETE endpoint
  - Option to delete account while preserving wikis
  - Option to cascade delete all owned wikis with account
  
### Changed
- **Unified Header Design**: Standardized header appearance across all pages
  - Dashboard header updated to match public home page style
  - WikiLayout header redesigned with consistent navigation
  - Removed sidebar footer in favor of header-based user menu
  
- **Improved Navigation**: Enhanced user navigation patterns
  - Consistent user menu placement across all authenticated pages
  - Centralized settings access from any page
  - Improved visual hierarchy in headers
  
### Fixed
- **Search Functionality Bug**: Resolved SQLAlchemy TypeError in search endpoint
  - Changed `func.case()` to `case()` by importing it directly from SQLAlchemy
  - Fixed issue where `func.case()` didn't support `else_` parameter
  - Search now properly handles case-insensitive matching across wiki pages

### Technical
- **Test Infrastructure**:
  - Added `test_slug_uniqueness.py`: Comprehensive test for slug generation and database constraints
  - Validates wiki-level uniqueness requirements
  - Tests incremental suffix generation logic
  
- **Dependencies Added**:
  - `@toast-ui/editor-plugin-code-syntax-highlight` for syntax highlighting
  - `prismjs` for code tokenization and highlighting
  - `pgvector` (Python) for PostgreSQL vector operations
  - `sentence-transformers` for embedding model
  - `tiktoken` for token counting and text chunking
  - `rq` (Redis Queue) for background task processing
  
- **Infrastructure**:
  - PostgreSQL 16 with pgvector extension (Docker container)
  - Redis 7 for task queue with persistence (Docker container)
  - Flask embedding microservice on port 8001 with GPU support
  - RQ worker process for background embedding generation
  
- **New Backend Components**:
  - `embedding_service/app.py`: Standalone Flask microservice for GPU-accelerated embeddings
  - `app/models/models.py`: Added `PageEmbedding` model with Vector(384) column
  - `app/services/chunking.py`: `TextChunker` for markdown-aware text splitting
  - `app/services/embeddings.py`: `EmbeddingServiceClient` HTTP client
  - `app/tasks/embedding_tasks.py`: RQ background tasks for embedding generation
  - `app/routes/semantic_search.py`: Semantic and hybrid search endpoints
  - `worker.py`: RQ worker script for processing embedding tasks
  
- **New Frontend Components**:
  - `UserMenu.jsx`: User dropdown menu component
  - `ThemeContext.jsx`: Global theme state management
  - `UserSettings.jsx`: Comprehensive settings page
  - `Home.jsx`: Public wiki explorer page
  - `SemanticSearch.jsx`: Reusable AI search component with mode toggle
  - `SemanticSearchPage.jsx`: Dedicated AI search page at `/search`
  
- **New Stylesheets**:
  - `prism-theme.css`: Theme-aware syntax highlighting styles
  - `semantic-search.css`: Complete styling for AI search components
  - Updated `index.css` with CSS custom properties for theming
  
- **API Endpoints**:
  - `GET /api/wikis/public`: List public wikis grouped by author
  - `DELETE /api/auth/me`: Delete user account with optional wiki cascade
  - `POST /api/search/semantic`: Vector similarity search with configurable threshold
  - `POST /api/search/hybrid`: Combined semantic and keyword search with adjustable weights
  - `POST /embed` (embedding service): Generate embeddings for text batches

---

## [1.0.0] - Initial Release

### Added
- User authentication and authorization with JWT
- Wiki creation and management
- Hierarchical page structure with parent-child relationships
- Rich markdown editor with image upload support
- Page version history and revisions
- File attachments for wiki pages
- Public/private wiki visibility settings
- Collaborative editing with permissions
- Search functionality across wiki pages
- Responsive UI built with React
- RESTful API built with Flask
