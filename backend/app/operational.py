"""Explicit loopback-only single operator; never a test identity or OIDC bypass."""
import ipaddress
from urllib.parse import urlparse
from uuid import UUID
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from .security import Context, establish_session, fail

PASSWORDS = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

class OperatorLogin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    password: SecretStr = Field(min_length=1, max_length=1024)

def validate_local(settings):
    if settings.auth_mode != 'operational_local':
        return
    UUID(settings.operator_org_id); UUID(settings.operator_actor_id)
    if not settings.operator_password_hash.get_secret_value().startswith('$argon2id$'):
        raise ValueError('Configure uma senha protegida com Argon2id.')
    if not settings.allowed_origins:
        raise ValueError('Configure a origem local.')
    for origin in settings.allowed_origins:
        u = urlparse(origin)
        if u.hostname not in ('127.0.0.1', 'localhost', '::1') or u.scheme != 'http':
            raise ValueError('O acesso operacional local exige loopback HTTP.')
    from sqlalchemy.engine import make_url
    if make_url(settings.database_url.get_secret_value()).host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('O acesso operacional local exige PostgreSQL local.')

def loopback(request):
    try:
        return ipaddress.ip_address(request.client.host).is_loopback
    except (ValueError, AttributeError):
        return False

def login(app, request, response, body):
    settings = app.state.settings
    if settings.auth_mode != 'operational_local' or not loopback(request):
        fail(404, 'Esta opção não está disponível.')
    denied = None
    with app.state.database.transaction(settings.operator_org_id, settings.operator_actor_id) as db:
        # Serialize attempts across workers. Failures are committed before responding.
        db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))', {'k': settings.operator_org_id+':operator-login'})
        actor = db.one('''SELECT a.id,a.active,m.active AS membership_active FROM actor a
            JOIN membership m ON m.actor_id=a.id WHERE a.id=:a AND m.org_id=:o
            AND a.issuer=:iss AND a.subject='consormulti-operador' ''',
            {'a': settings.operator_actor_id, 'o': settings.operator_org_id, 'iss': settings.issuer})
        if not actor or not actor['active'] or not actor['membership_active']:
            fail(401, 'Este acesso está indisponível.')
        ctx = Context(db, settings.operator_org_id, settings.operator_actor_id, 'planner', 'consortium',
                      'Operador CONSORMULTI', 'CONSORMULTI', '', True)
        attempts = db.one("""SELECT count(*) AS n FROM audit_event WHERE org_id=:o
            AND action='auth.operator_failed' AND created_at>now()-interval '15 minutes'""",
            {'o': settings.operator_org_id})['n']
        if attempts >= 5:
            denied = 429
        else:
            try:
                valid = PASSWORDS.verify(settings.operator_password_hash.get_secret_value(), body.password.get_secret_value())
            except (VerificationError, InvalidHashError):
                valid = False
            if not valid:
                ctx.audit('auth.operator_failed', settings.operator_actor_id)
                denied = 401
            else:
                token, claims = app.state.verifier.mint('consormulti-operador', settings.operator_org_id)
                app.state.verifier.decode(token)
                result = establish_session(app, db, claims, actor, token, response)
                ctx.audit('auth.operator_login', settings.operator_actor_id)
    if denied:
        fail(denied, 'Aguarde 15 minutos antes de tentar novamente.' if denied == 429 else 'Senha incorreta. Confira e tente novamente.', 'LOGIN_LIMIT' if denied == 429 else 'INVALID_LOGIN')
    return result
