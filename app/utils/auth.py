import jwt
from fastapi import Header, HTTPException
from typing import Optional

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")

        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if not user_id:
            raise ValueError("User ID (sub) not found in token")

        return user_id

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authorization token: {str(e)}")
