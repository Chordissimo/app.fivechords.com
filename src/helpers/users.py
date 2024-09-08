import time
from typing import Any, Dict, Optional
from pymongo.database import Database

from .db import DATABASE_COLLECTIONS


#with open("tokens.txt", "r") as f:
#    pass_token = f.read().strip()


def get_user_by_token(
        database: Database, token: str
) -> Optional[Dict[str, Any]]:
#    if token == pass_token:
#        return {}

    result = database[DATABASE_COLLECTIONS.USERS.name].find_one({
        "token": token
    })

    if not result:
        return None

    if result["exp"] < time.time():
        return None

    return result


def update_users_token(
        database: Database, user_id: str, token: str, exp: int
):
    user = database[DATABASE_COLLECTIONS.USERS.name].find_one({
        "user_id": user_id
    })
    if user is None:
        database[DATABASE_COLLECTIONS.USERS.name].insert_one({
            "user_id": user_id,
            "token": token,
            "exp": exp
        })
        return

    database[DATABASE_COLLECTIONS.USERS.name].find_one_and_update(
        {"user_id": user_id},
        {"$set": {
            "token": token,
            "exp": exp
        }})
