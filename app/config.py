import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_CSRF_CHECK_FORM = False
    JWT_CSRF_IN_COOKIES = False
    # Force JWT to NOT generate CSRF claims in tokens
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = None
    
    # File upload configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size for bulk imports
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'xlsx'},
        'code': {'py', 'js', 'ts', 'html', 'css', 'json', 'yaml', 'yml'},
    }
    
    # Redis & Task Queue Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    RQ_WORKER_COUNT = int(os.getenv('RQ_WORKER_COUNT', '2'))
    
    # Embedding Service Configuration
    EMBEDDING_SERVICE_URL = os.getenv('EMBEDDING_SERVICE_URL', 'http://localhost:8001')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '384'))
    MAX_CHUNK_TOKENS = int(os.getenv('MAX_CHUNK_TOKENS', '256'))
    CHUNK_OVERLAP_TOKENS = int(os.getenv('CHUNK_OVERLAP_TOKENS', '50'))
    EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
    EMBEDDING_REQUEST_TIMEOUT = int(os.getenv('EMBEDDING_REQUEST_TIMEOUT', '30'))
    IVFFLAT_PROBES = int(os.getenv('IVFFLAT_PROBES', '10'))
    
    @property
    def all_allowed_extensions(self):
        return set().union(*self.ALLOWED_EXTENSIONS.values())


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///wiki_dev.db'
    )


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Stricter security settings
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
