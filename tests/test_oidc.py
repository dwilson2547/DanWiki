"""authentik sign-in: user resolution, group-owned flags, wiki-creation gate."""
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.integrations.base_client.errors import OAuthError
from flask_jwt_extended import decode_token

from app import create_app
from app.models import db, User, UserIdentity
from app.routes import oidc

ISS = 'https://auth.example/application/o/danwiki/'


class FakeAuthentik:
    def __init__(self):
        self.claims = None
        self.error = None

    def authorize_redirect(self, redirect_uri):
        from flask import redirect
        return redirect('https://auth.example/authorize?redirect_uri=' + redirect_uri)

    def authorize_access_token(self):
        if self.error:
            raise self.error
        return {'userinfo': self.claims}


@pytest.fixture
def app(monkeypatch):
    app = create_app('testing')
    app.config.update(OIDC_ENABLED=True, OIDC_UI_URL='https://wiki.example',
                      OIDC_REDIRECT_URI='https://wiki.example/api/auth/oidc/callback')
    fake = FakeAuthentik()
    monkeypatch.setattr(oidc.oauth, 'authentik', fake, raising=False)
    app.fake = fake
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def claims(sub='abc', email='dan@example.com', groups=(), **extra):
    return {'iss': ISS, 'sub': sub, 'email': email, 'preferred_username': 'dan',
            'name': 'Dan', 'groups': list(groups), **extra}


def sign_in(app, **kw):
    app.fake.claims = claims(**kw)
    resp = app.test_client().get('/api/auth/oidc/callback')
    assert resp.status_code == 302
    loc = urlparse(resp.headers['Location'])
    assert loc.scheme + '://' + loc.netloc + loc.path == 'https://wiki.example/login/callback'
    return {k: v[0] for k, v in parse_qs(loc.fragment).items()}


def test_login_redirects_to_authentik(app):
    resp = app.test_client().get('/api/auth/oidc/login')
    assert resp.status_code == 302
    assert resp.headers['Location'].startswith('https://auth.example/authorize')


def test_first_sign_in_creates_user_and_issues_tokens(app):
    out = sign_in(app)
    user = User.query.one()
    assert (user.username, user.email, user.display_name) == ('dan', 'dan@example.com', 'Dan')
    assert user.is_approved and not user.is_admin and not user.can_create_wikis
    assert UserIdentity.query.one().subject == 'abc'
    assert decode_token(out['access_token'])['sub'] == str(user.id)
    assert decode_token(out['refresh_token'])['type'] == 'refresh'


def test_second_sign_in_matches_by_identity_not_email(app):
    sign_in(app)
    sign_in(app, email='changed@example.com')
    assert User.query.count() == 1


def test_existing_user_linked_by_email(app):
    u = User(username='old', email='Dan@Example.com', password_hash='x', is_approved=False)
    db.session.add(u)
    db.session.commit()
    sign_in(app)
    assert User.query.count() == 1
    assert UserIdentity.query.one().user_id == u.id
    assert db.session.get(User, u.id).is_approved


def test_username_collision_gets_suffix(app):
    db.session.add(User(username='dan', email='other@example.com', password_hash='x'))
    db.session.commit()
    sign_in(app)
    assert User.query.filter_by(email='dan@example.com').one().username == 'dan2'


def test_groups_set_flags_both_ways(app):
    sign_in(app, groups=['danwiki-admins', 'danwiki-creators'])
    user = User.query.one()
    assert user.is_admin and user.can_create_wikis
    sign_in(app, groups=[])
    db.session.refresh(user)
    assert not user.is_admin and not user.can_create_wikis


def test_disabled_user_refused(app):
    sign_in(app)
    user = User.query.one()
    user.is_active = False
    db.session.commit()
    out = sign_in(app)
    assert out == {'error': 'Account is disabled'}


def test_no_email_refused(app):
    out = sign_in(app, email='')
    assert 'no email' in out['error']
    assert User.query.count() == 0


def test_oauth_error_returned_to_ui(app):
    app.fake.error = OAuthError(error='access_denied', description='Permission denied')
    resp = app.test_client().get('/api/auth/oidc/callback')
    assert parse_qs(urlparse(resp.headers['Location']).fragment) == {'error': ['Permission denied']}


def test_password_routes_are_gone(app):
    client = app.test_client()
    for path in ('/api/auth/login', '/api/auth/register', '/api/auth/change-password'):
        assert client.post(path, json={}).status_code in (404, 405)


def test_wiki_creation_requires_creator_group(app):
    client = app.test_client()
    token = sign_in(app)['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    assert client.post('/api/wikis', json={'name': 'W'}, headers=headers).status_code == 403
    assert client.post('/api/wikis/import', headers=headers).status_code == 403

    token = sign_in(app, groups=['danwiki-creators'])['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    assert client.post('/api/wikis', json={'name': 'W'}, headers=headers).status_code == 201


def test_admin_flag_cannot_be_changed_in_app(app):
    sign_in(app, sub='admin', email='a@example.com', groups=['danwiki-admins'])
    sign_in(app, sub='other', email='o@example.com')
    admin_token = sign_in(app, sub='admin', email='a@example.com', groups=['danwiki-admins'])['access_token']
    other = User.query.filter_by(email='o@example.com').one()
    client = app.test_client()
    headers = {'Authorization': f'Bearer {admin_token}'}
    resp = client.patch(f'/api/admin/users/{other.id}', json={'is_admin': True}, headers=headers)
    assert resp.status_code == 400 and 'authentik' in resp.get_json()['error']
    # Unchanged is_admin (the UI always sends it) still lets other fields through.
    resp = client.patch(f'/api/admin/users/{other.id}', json={'is_admin': False, 'display_name': 'O'},
                        headers=headers)
    assert resp.status_code == 200
