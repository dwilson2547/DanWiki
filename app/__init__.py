import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

from app.config import config
from app.models import db


jwt = JWTManager()
migrate = Migrate()


def create_app(config_name: str = None) -> Flask:
    """Application factory for creating Flask app instances."""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Disable CSRF for JWT since we're using Authorization headers
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS - adjust origins for production
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Create upload folder if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder):
        upload_folder = os.path.join(app.root_path, '..', upload_folder)
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Register blueprints
    from app.routes import (auth_bp, wikis_bp, pages_bp, attachments_bp, 
                           search_bp, semantic_search_bp, bulk_import_bp, admin_bp,
                           tags_bp, page_tags_bp)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(wikis_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(semantic_search_bp)
    app.register_blueprint(bulk_import_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(page_tags_bp)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'code': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.error(f"Invalid token error: {error}")
        return jsonify({
            'error': 'Invalid token',
            'code': 'invalid_token',
            'details': str(error)
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization token required',
            'code': 'token_required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has been revoked',
            'code': 'token_revoked'
        }), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token verification failed',
            'code': 'token_verification_failed',
            'details': str(jwt_payload)
        }), 401
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'version': '1.1.0'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413
    
    return app
