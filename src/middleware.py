import base64
import crypt
import traceback
from typing import Any
from fastapi import  \
    HTTPException, Request, status
from helpers.users import get_user_by_token, update_users_token
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin._token_gen import ExpiredIdTokenError
from pymongo.database import Database


cred = credentials.Certificate("/etc/auth/prochords.json")
firebase_admin.initialize_app(cred)

with open("/etc/auth/auth.conf", "r") as f:
    d = f.read().strip()
    basic_login, basic_password = d.split(":")


async def validate_user_middleware(
    request: Request,
    database: Database,
    call_next: Any
):
    if "/adm" in str(request.url) or "openapi.json" in str(request.url):
        return await call_next(request)

    token = request.headers.get("Authorization", None)
    ref = request.headers.get("Referer", None)

    if not token and ref and ref.startswith("https://app.fivechords.com"):
        request.state.user_id = "test"
        return await call_next(request)

    user_id = None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="")
        
    # if token and token.startswith("Basic"):
    #     id_token = token.split(" ").pop()
    #     decoded_credentials = base64.b64decode(id_token).decode("utf-8")
    #     username, password = decoded_credentials.split(":")
    #     assert username == basic_login
    #     hashed_input_password = crypt.crypt(password, basic_password)
    #     assert hashed_input_password == basic_password
    #     user_id = "test"
    # else:
    
    try:
        id_token = token.split(" ").pop()
        user = get_user_by_token(database=database, token=id_token)
        if user is None:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token.get("uid")
            exp = decoded_token.get("exp")
            update_users_token(
                database=database,
                user_id=uid,
                token=id_token,
                exp=exp
            )
            user_id = uid
        else:
            user_id = user["user_id"]

    except ExpiredIdTokenError:
        traceback.print_exc()
        raise HTTPException(status_code=403)
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=e.__str__())
            
    assert user_id is not None
    request.state.user_id = user_id
    response = await call_next(request)
    return response
