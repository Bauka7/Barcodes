from dataclasses import dataclass
import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
    phone: str | None
    subject: str


@dataclass(slots=True)
class ExternalTokenResponse:
    access_token: str
    token_type: str
    expires_in: int | None = None


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


def _request_keycloak_token(
    settings: Settings,
    username: str,
    password: str,
) -> dict[str, object]:
    token_url = settings.keycloak_token_url.strip()
    client_id = settings.keycloak_client_id.strip()
    if not token_url:
        raise ExternalAuthConfigurationError("KEYCLOAK_TOKEN_URL is not configured.")
    if not client_id:
        raise ExternalAuthConfigurationError("KEYCLOAK_CLIENT_ID is not configured.")

    form_data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
    }
    client_secret = settings.keycloak_client_secret.strip()
    if client_secret:
        form_data["client_secret"] = client_secret

    scope = settings.keycloak_scope.strip()
    if scope:
        form_data["scope"] = scope

    request = Request(
        token_url,
        data=urlencode(form_data).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code in {400, 401}:
            raise JWTError("Invalid external username or password.") from error
        raise ExternalAuthConfigurationError(
            f"Keycloak token endpoint returned HTTP {error.code}."
        ) from error
    except (OSError, URLError, json.JSONDecodeError) as error:
        raise ExternalAuthConfigurationError(
            "Could not request token from Keycloak token endpoint."
        ) from error


async def login_with_external_password(
    settings: Settings,
    username: str,
    password: str,
) -> ExternalTokenResponse:
    data = await asyncio.to_thread(
        _request_keycloak_token,
        settings,
        username,
        password,
    )

    access_token = data.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise ExternalAuthConfigurationError(
            "Keycloak token response does not contain access_token."
        )

    token_type = data.get("token_type")
    expires_in = data.get("expires_in")
    return ExternalTokenResponse(
        access_token=access_token,
        token_type=token_type.strip() if isinstance(token_type, str) else "bearer",
        expires_in=expires_in if isinstance(expires_in, int) else None,
    )


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
    phone_claim = settings.keycloak_phone_claim.strip() or "phone_number"

    username = claims.get(username_claim)
    if not isinstance(username, str) or not username.strip():
        raise JWTError(f"External JWT does not contain username claim '{username_claim}'.")

    email = claims.get(email_claim)
    full_name = claims.get(full_name_claim)
    phone = claims.get(phone_claim)
    subject = claims.get("sub")

    return ExternalUserClaims(
        username=username.strip(),
        email=email.strip() if isinstance(email, str) and email.strip() else None,
        full_name=full_name.strip()
        if isinstance(full_name, str) and full_name.strip()
        else None,
        phone=phone.strip() if isinstance(phone, str) and phone.strip() else None,
        subject=subject.strip() if isinstance(subject, str) else "",
    )
