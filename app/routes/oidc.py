"""Sign-in through authentik (OIDC authorization code flow).

authentik answers "who is this"; DanWiki keeps its own users and wiki memberships.
After the code exchange the user is matched to a local account and gets the same
access/refresh tokens a password login used to issue. They reach the UI in the URL
fragment (``/login/callback#access_token=...``), which browsers never send to a
server, so tokens stay out of access logs.

Matching: by (issuer, sub) in ``user_identities``; on first sign-in, by email,
after which the link is stored. authentik's own sign-up is held for admin
approval, so anyone who gets this far has been vetted there.

Site-wide flags are owned by authentik and set at every sign-in, both ways:
  OIDC_ADMIN_GROUP   -> is_admin
  OIDC_CREATOR_GROUP -> can_create_wikis
Per-wiki roles (viewer/editor/admin) stay in DanWiki.
"""
import re
import secrets
from urllib.parse import urlencode

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, redirect
from flask_jwt_extended import create_access_token, create_refresh_token

from app.models import db, User, UserIdentity

oidc_bp = Blueprint('oidc', __name__, url_prefix='/api/auth/oidc')
oauth = OAuth()


class SignInRefused(Exception):
    pass


def init_oidc(app):
    oauth.init_app(app)
    if not app.config['OIDC_ENABLED']:
        return
    oauth.register(
        'authentik',
        client_id=app.config['OIDC_CLIENT_ID'],
        client_secret=app.config['OIDC_CLIENT_SECRET'],
        server_metadata_url=app.config['OIDC_ISSUER'].rstrip('/') + '/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


def _to_ui(**params):
    return redirect(current_app.config['OIDC_UI_URL'] + '/login/callback#' + urlencode(params))


def _unique_username(wanted: str) -> str:
    base = re.sub(r'[^A-Za-z0-9_.-]', '', wanted or '')[:70] or 'user'
    name, n = base, 1
    while User.query.filter_by(username=name).first() is not None:
        n += 1
        name = f'{base}{n}'
    return name


def _resolve_user(claims: dict) -> User:
    issuer, subject = claims['iss'], claims['sub']
    identity = UserIdentity.query.filter_by(issuer=issuer, subject=subject).first()
    if identity:
        return identity.user

    email = (claims.get('email') or '').strip()
    if not email:
        raise SignInRefused('Your authentik account has no email address')
    user = User.query.filter(db.func.lower(User.email) == email.lower()).first()
    if user is None:
        username = _unique_username(claims.get('preferred_username') or email.split('@')[0])
        user = User(
            username=username,
            email=email,
            display_name=claims.get('name') or username,
            # Never used: there is no password login. Not a bcrypt hash, so it can't match.
            password_hash='!oidc:' + secrets.token_hex(16),
            is_approved=True,
        )
        db.session.add(user)
        db.session.flush()
        current_app.logger.warning('oidc: created user %s', user.username)
    else:
        current_app.logger.warning('oidc: linked existing user %s by email', user.username)
    db.session.add(UserIdentity(user_id=user.id, issuer=issuer, subject=subject))
    return user


def _sync_flags(user: User, claims: dict):
    groups = set(claims.get('groups') or [])
    is_admin = current_app.config['OIDC_ADMIN_GROUP'] in groups
    can_create = current_app.config['OIDC_CREATOR_GROUP'] in groups
    if (user.is_admin, user.can_create_wikis) != (is_admin, can_create):
        current_app.logger.warning('oidc: %s admin %s -> %s, creator %s -> %s', user.username,
                                   user.is_admin, is_admin, user.can_create_wikis, can_create)
    user.is_admin = is_admin
    user.can_create_wikis = can_create
    user.is_approved = True


def _disabled():
    return redirect(current_app.config['OIDC_UI_URL'] + '/login/callback#'
                    + urlencode({'error': 'Sign-in is not configured'}))


@oidc_bp.route('/login', methods=['GET'])
def login():
    if not current_app.config['OIDC_ENABLED']:
        return _disabled()
    return oauth.authentik.authorize_redirect(current_app.config['OIDC_REDIRECT_URI'])


@oidc_bp.route('/callback', methods=['GET'])
def callback():
    if not current_app.config['OIDC_ENABLED']:
        return _disabled()
    try:
        token = oauth.authentik.authorize_access_token()
        claims = token.get('userinfo') or oauth.authentik.parse_id_token(token)
        user = _resolve_user(claims)
        if not user.is_active:
            raise SignInRefused('Account is disabled')
        _sync_flags(user, claims)
        db.session.commit()
        return _to_ui(
            access_token=create_access_token(identity=str(user.id), fresh=True),
            refresh_token=create_refresh_token(identity=str(user.id)),
        )
    except SignInRefused as ex:
        db.session.rollback()
        return _to_ui(error=str(ex))
    except OAuthError as ex:
        db.session.rollback()
        current_app.logger.warning('oidc: %s', ex)
        return _to_ui(error=ex.description or ex.error)
    except Exception as ex:
        db.session.rollback()
        current_app.log_exception(ex)
        return _to_ui(error='Sign-in failed')


@oidc_bp.route('/logout', methods=['GET'])
def logout():
    """End the authentik session too; the UI has already dropped its tokens."""
    if not current_app.config['OIDC_ENABLED']:
        return redirect(current_app.config['OIDC_UI_URL'] + '/')
    end_session = oauth.authentik.load_server_metadata().get('end_session_endpoint')
    return redirect(end_session or current_app.config['OIDC_UI_URL'] + '/')
