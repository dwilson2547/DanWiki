# API Authentication Methods

Comprehensive overview of common API authentication approaches.

## API Key Authentication

Simplest form: client sends key in header or query parameter.

```http
GET /api/users
X-API-Key: abc123xyz456
```

**Pros:**
- Simple to implement
- Easy to revoke

**Cons:**
- Keys can be intercepted
- No expiration mechanism
- Difficult to manage permissions

## OAuth 2.0

Industry standard for authorization. Allows third-party access without sharing credentials.

### Authorization Code Flow

Best for server-side applications:

1. Client redirects to authorization server
2. User authenticates and consents
3. Auth server returns authorization code
4. Client exchanges code for access token
5. Client uses token to access resources

### Client Credentials Flow

For machine-to-machine authentication:

```bash
curl -X POST https://auth.example.com/token \
  -d grant_type=client_credentials \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_SECRET
```

## JWT (JSON Web Tokens)

Self-contained tokens encoding user identity and claims.

### Structure

```
header.payload.signature
```

Example:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Usage

```http
GET /api/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Validation

Server must verify:
- Signature is valid
- Token not expired
- Issuer is trusted
- Audience matches

## Basic Authentication

Sends username:password encoded in Base64.

```http
GET /api/data
Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
```

**Only use over HTTPS!**

## Session-Based Authentication

Traditional web authentication using server-side sessions.

1. User logs in with credentials
2. Server creates session, returns session ID cookie
3. Client sends cookie with each request
4. Server validates session

## HMAC Signatures

Sign requests with shared secret for integrity.

```python
import hmac
import hashlib

message = f"{method}{path}{body}"
signature = hmac.new(
    secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()
```

Include in header:
```http
X-Signature: sha256=abc123...
```

## Mutual TLS (mTLS)

Both client and server authenticate with certificates.

**Use cases:**
- Microservices communication
- High-security environments
- IoT devices

## Best Practices

1. **Always use HTTPS** in production
2. **Implement rate limiting** to prevent abuse
3. **Rotate credentials** regularly
4. **Use short-lived tokens** with refresh mechanism
5. **Log authentication attempts** for security monitoring
6. **Never log sensitive data** (passwords, tokens)
7. **Implement proper CORS** policies
8. **Use proven libraries** - don't roll your own

## Security Considerations

### Token Storage

- **Never** store in localStorage (XSS vulnerable)
- Use httpOnly cookies for web apps
- Use secure storage APIs for mobile
- Encrypt tokens at rest

### Token Expiration

- Access tokens: 15-60 minutes
- Refresh tokens: 7-30 days
- API keys: No expiration but allow revocation

### Scope and Permissions

Implement principle of least privilege:

```json
{
  "user_id": "123",
  "scopes": ["read:profile", "write:posts"],
  "permissions": ["user"]
}
```

## Comparison Table

| Method | Complexity | Security | Use Case |
|--------|-----------|----------|----------|
| API Key | Low | Low | Internal APIs |
| OAuth 2.0 | High | High | Third-party access |
| JWT | Medium | Medium-High | Stateless APIs |
| Basic Auth | Low | Low | Legacy systems |
| Session | Medium | Medium | Web applications |
| HMAC | Medium | High | Webhooks |
| mTLS | High | Very High | Microservices |

## Implementation Examples

### Flask JWT

```python
from flask_jwt_extended import create_access_token, jwt_required

@app.route('/login', methods=['POST'])
def login():
    token = create_access_token(identity=user.id)
    return {'access_token': token}

@app.route('/protected')
@jwt_required()
def protected():
    return {'message': 'Access granted'}
```

### Express OAuth

```javascript
const passport = require('passport');
const OAuth2Strategy = require('passport-oauth2');

passport.use(new OAuth2Strategy({
  authorizationURL: 'https://provider.com/oauth2/authorize',
  tokenURL: 'https://provider.com/oauth2/token',
  clientID: CLIENT_ID,
  clientSecret: CLIENT_SECRET
}, (accessToken, refreshToken, profile, done) => {
  // Verify and create user
}));
```
