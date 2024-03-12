from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


def api_key_auth(valid_keys: list, header_name: str = "X-API-Key"):
    def get_api_key(
        api_key_header: str = Security(APIKeyHeader(name=header_name)),
    ) -> str:
        if api_key_header in valid_keys:
            return api_key_header
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
        )

    return get_api_key
