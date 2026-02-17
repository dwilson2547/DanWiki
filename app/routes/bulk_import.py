"""
Bulk import routes for uploading and importing wiki archives.
"""
import os
import tempfile
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.tasks import enqueue_page_embedding

from app.models import db, User, Wiki, Page
from app.services.archive_import import ArchiveImporter
import logging

bulk_import_bp = Blueprint('bulk_import', __name__)

logger = logging.getLogger(__name__)


def allowed_archive_file(filename: str) -> bool:
    """Check if file is an allowed archive format."""
    return filename.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz'))


@bulk_import_bp.route('/api/wikis/import', methods=['POST'])
@jwt_required()
def import_new_wiki():
    """
    Create a new wiki and import pages from an archive.
    
    Form data:
        - archive: The zip or tar.gz file
        - name: Wiki name
        - description: Wiki description (optional)
        - is_public: Whether the wiki is public (optional, default: false)
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Validate form data
    if 'archive' not in request.files:
        return jsonify({'error': 'No archive file provided'}), 400
    
    archive_file = request.files['archive']
    if archive_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_archive_file(archive_file.filename):
        return jsonify({'error': 'Invalid file format. Use .zip or .tar.gz'}), 400
    
    wiki_name = request.form.get('name')
    if not wiki_name or not wiki_name.strip():
        return jsonify({'error': 'Wiki name is required'}), 400
    
    wiki_description = request.form.get('description', '')
    is_public = request.form.get('is_public', 'false').lower() == 'true'
    
    # Save archive to temporary file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archive_file.filename)[1]) as temp_file:
        archive_file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Create the wiki
        wiki = Wiki(
            name=wiki_name.strip(),
            description=wiki_description.strip() if wiki_description else None,
            is_public=is_public,
            owner_id=user.id
        )
        db.session.add(wiki)
        db.session.flush()  # Get wiki ID
        
        # Import the archive
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        importer = ArchiveImporter(wiki, user, upload_folder)
        result = importer.import_archive(temp_path)
        
        # If import completely failed, rollback everything including the wiki
        if result.success_count == 0 and result.failure_count > 0:
            db.session.rollback()
            return jsonify({
                'error': 'Import failed',
                'details': result.to_dict()
            }), 400
        
        # Commit the wiki and import results
        db.session.commit()
        
        pending_pages = Page.query.filter_by(wiki_id=wiki.id, embeddings_status='pending').all()
        for page in pending_pages:
            try:
                job = enqueue_page_embedding(page.id)
            except Exception as e:
                current_app.logger.error(f"Failed to enqueue embedding job for page {page.id}: {str(e)}")
                logger.info(f"Enqueued embedding task for page {page.id}, job: {job.id}")
        
        return jsonify({
            'message': 'Wiki created and import completed',
            'wiki': wiki.to_dict(),
            'import_result': result.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Import new wiki failed for user {current_user_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Import failed: {str(e)}'}), 500
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@bulk_import_bp.route('/api/wikis/<int:wiki_id>/import', methods=['POST'])
@jwt_required()
def import_to_existing_wiki(wiki_id):
    """
    Import pages from an archive into an existing wiki.
    
    Form data:
        - archive: The zip or tar.gz file
        - parent_page_id: Optional ID of parent page to import under (omit for root level)
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check wiki exists and user has permission
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    # Check if user can edit the wiki (admins can edit any wiki)
    if not user.is_admin and not user.can_edit_wiki(wiki_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Validate file upload
    if 'archive' not in request.files:
        return jsonify({'error': 'No archive file provided'}), 400
    
    archive_file = request.files['archive']
    if archive_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_archive_file(archive_file.filename):
        return jsonify({'error': 'Invalid file format. Use .zip or .tar.gz'}), 400
    
    # Get optional parent page
    parent_page = None
    parent_page_id = request.form.get('parent_page_id')
    if parent_page_id:
        try:
            parent_page_id = int(parent_page_id)
            parent_page = Page.query.filter_by(id=parent_page_id, wiki_id=wiki_id).first()
            if not parent_page:
                return jsonify({'error': 'Parent page not found'}), 404
        except ValueError:
            return jsonify({'error': 'Invalid parent_page_id'}), 400
    
    # Save archive to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archive_file.filename)[1]) as temp_file:
        archive_file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Import the archive
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        importer = ArchiveImporter(wiki, user, upload_folder)
        result = importer.import_archive(temp_path, parent_page)
        
        # Commit changes
        db.session.commit()
        
        pending_pages = Page.query.filter_by(wiki_id=wiki.id, embeddings_status='pending').all()
        for page in pending_pages:
            try:
                job = enqueue_page_embedding(page.id)
            except Exception as e:
                current_app.logger.error(f"Failed to enqueue embedding job for page {page.id}: {str(e)}")
                logger.info(f"Enqueued embedding task for page {page.id}, job: {job.id}")
        
        return jsonify({
            'message': 'Import completed',
            'import_result': result.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Import to existing wiki {wiki_id} failed for user {current_user_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Import failed: {str(e)}'}), 500
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@bulk_import_bp.route('/api/wikis/<int:wiki_id>/pages/tree', methods=['GET'])
@jwt_required()
def get_page_tree(wiki_id):
    """
    Get hierarchical tree of all pages in a wiki.
    Useful for selecting a parent page when importing.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check wiki exists and user has permission
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    # Check access (public wiki or member)
    if not wiki.is_public:
        role = user.get_wiki_role(wiki_id)
        if wiki.owner_id != user.id and not role and not user.is_admin:
            return jsonify({'error': 'Access denied'}), 403
    
    # Build tree structure
    def build_tree(page):
        return {
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'children': [build_tree(child) for child in page.children]
        }
    
    root_pages = wiki.get_root_pages()
    tree = [build_tree(page) for page in root_pages]
    
    return jsonify({
        'wiki_id': wiki_id,
        'wiki_name': wiki.name,
        'pages': tree
    }), 200
