from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Dependency to validate the API key.
    The key is expected to be passed as 'Bearer <key>'.
    """
    if " " not in api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <key>'."
        )

    scheme, _, key = api_key_header.partition(" ")
    if scheme.lower() != "bearer" or key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return key 