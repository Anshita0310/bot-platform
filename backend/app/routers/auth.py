from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ..db import get_db
from ..schemas import UserSignup, UserLogin, UserOut
from ..auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", status_code=201, response_model=UserOut)
async def signup(payload: UserSignup, db=Depends(get_db)):
    existing = await db.users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(400, "Email already registered")

    now = datetime.utcnow()
    user_doc = {
        "email": payload.email,
        "name": payload.name,
        "orgId": payload.orgId,
        "hashedPassword": hash_password(payload.password),
        "createdAt": now,
    }
    res = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(res.inserted_id)

    token = create_token({"sub": user_doc["email"], "orgId": user_doc["orgId"], "name": user_doc["name"]})
    return {
        "access_token": token,
        "user": {"email": user_doc["email"], "name": user_doc["name"], "orgId": user_doc["orgId"]},
    }


@router.post("/login", response_model=UserOut)
async def login(payload: UserLogin, db=Depends(get_db)):
    user = await db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["hashedPassword"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_token({"sub": user["email"], "orgId": user["orgId"], "name": user["name"]})
    return {
        "access_token": token,
        "user": {"email": user["email"], "name": user["name"], "orgId": user["orgId"]},
    }
