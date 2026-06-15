from dataclasses import dataclass
import json
from urllib.error import URLError
from urllib.request import urlopen

from jose import JWTError, jwt

from app.core.config import Settings

JWKS_CACHE: dict[str, object] = {}
ALLOWED_EXTERNAL_JWT_ALGORITHMS = {"RS256", "RS384", "RS512"}


class ExternalAuthConfigurationError(RuntimeError):
    pass


@dataclass(slots=True)
class ExternalUserClaims:
    username: str
    email: str | None
    full_name: str | None
    subject: str


def external_auth_is_configured(settings: Settings) -> bool:
    return bool(settings.keycloak_jwks_url.strip())


def _load_jwks(url: str) -> dict[str, object]:
    cached = JWKS_CACHE.get(url)
    if isinstance(cached, dict):
        return cached

    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as error:
        raise ExternalAuthConfigurationError(
            f"Could not load external JWKS from {url}."
        ) from error

    if not isinstance(data, dict) or not isinstance(data.get("keys"), list):
        raise ExternalAuthConfigurationError("External JWKS response is invalid.")

    JWKS_CACHE[url] = data
    return data


def _find_jwk_for_token(token: str, jwks: dict[str, object]) -> dict[str, object]:
    header = jwt.get_unverified_header(token)
    key_id = header.get("kid")
    keys = jwks.get("keys")

    if not isinstance(keys, list):
        raise ExternalAuthConfigurationError("External JWKS does not contain keys.")

    if key_id:
        for key in keys:
            if isinstance(key, dict) and key.get("kid") == key_id:
                return key

    if len(keys) == 1 and isinstance(keys[0], dict):
        return keys[0]

    raise JWTError("No matching external JWT signing key was found.")


async def validate_external_token(
    token: str,
    settings: Settings,
) -> ExternalUserClaims:
    jwks_url = settings.keycloak_jwks_url.strip()
    if not jwks_url:
        raise ExternalAuthConfigurationError(
            "External auth is enabled but KEYCLOAK_JWKS_URL is not configured."
        )

    jwks = _load_jwks(jwks_url)
    key = _find_jwk_for_token(token=token, jwks=jwks)
    algorithm = str(key.get("alg") or jwt.get_unverified_header(token).get("alg") or "RS256")
    if algorithm not in ALLOWED_EXTERNAL_JWT_ALGORITHMS:
        raise JWTError("External JWT signing algorithm is not allowed.")

    issuer = settings.keycloak_issuer_uri.strip() or None
    audience = settings.keycloak_audience.strip() or None
    claims = jwt.decode(
        token,
        key,
        algorithms=[algorithm],
        issuer=issuer,
        audience=audience,
        options={
            "verify_iss": issuer is not None,
            "verify_aud": audience is not None,
        },
    )

    username_claim = settings.keycloak_username_claim.strip() or "preferred_username"
    email_claim = settings.keycloak_email_claim.strip() or "email"
    full_name_claim = settings.keycloak_full_name_claim.strip() or "name"

    username = claims.get(username_claim)
    if not isinstance(username, str) or not username.strip():
        raise JWTError(f"External JWT does not contain username claim '{username_claim}'.")

    email = claims.get(email_claim)
    full_name = claims.get(full_name_claim)
    subject = claims.get("sub")

    return ExternalUserClaims(
        username=username.strip(),
        email=email.strip() if isinstance(email, str) and email.strip() else None,
        full_name=full_name.strip()
        if isinstance(full_name, str) and full_name.strip()
        else None,
        subject=subject.strip() if isinstance(subject, str) else "",
    )
