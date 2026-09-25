import os

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from ..database import get_db
from ..models import User


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Auth0 Authentication"]
)


# =========================================================
# AUTH0 CONFIGURATION
# =========================================================

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL")


if not AUTH0_DOMAIN:
    raise RuntimeError("AUTH0_DOMAIN is missing from .env")

if not AUTH0_CLIENT_ID:
    raise RuntimeError("AUTH0_CLIENT_ID is missing from .env")

if not AUTH0_CLIENT_SECRET:
    raise RuntimeError("AUTH0_CLIENT_SECRET is missing from .env")

if not AUTH0_CALLBACK_URL:
    raise RuntimeError("AUTH0_CALLBACK_URL is missing from .env")


# =========================================================
# OAUTH
# =========================================================

oauth = OAuth()

oauth.register(
    name="auth0",

    client_id=AUTH0_CLIENT_ID,

    client_secret=AUTH0_CLIENT_SECRET,

    server_metadata_url=(
        f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration"
    ),

    client_kwargs={
        "scope": "openid profile email"
    }
)


# =========================================================
# GOOGLE LOGIN
# =========================================================

@router.get("/auth0/login")
async def auth0_login(request: Request):

    print("Starting Google login...")

    return await oauth.auth0.authorize_redirect(
        request,
        AUTH0_CALLBACK_URL,
        connection="google-oauth2"
    )


# =========================================================
# FACEBOOK LOGIN
# =========================================================

@router.get("/facebook/login")
async def facebook_login(request: Request):

    print("Starting Facebook login...")

    return await oauth.auth0.authorize_redirect(
        request,
        AUTH0_CALLBACK_URL,
        connection="facebook"
    )


# =========================================================
# AUTH0 CALLBACK
# =========================================================

@router.get("/callback")
async def auth0_callback(
    request: Request,
    db: Session = Depends(get_db)
):

    try:

        # -------------------------------------------------
        # Get token from Auth0
        # -------------------------------------------------

        token = await oauth.auth0.authorize_access_token(request)

        print("AUTH0 TOKEN RECEIVED")


        # -------------------------------------------------
        # Get user information
        # -------------------------------------------------

        userinfo = token.get("userinfo")

        if not userinfo:

            userinfo = await oauth.auth0.userinfo(
                token=token
            )


        if not userinfo:

            raise HTTPException(
                status_code=400,
                detail="User information was not returned by Auth0"
            )


        # -------------------------------------------------
        # Extract user information
        # -------------------------------------------------

        email = userinfo.get("email")

        name = (
            userinfo.get("name")
            or userinfo.get("nickname")
            or "Auth0 User"
        )

        auth0_id = userinfo.get("sub")


        if not email:

            raise HTTPException(
                status_code=400,
                detail="Email was not provided by Auth0"
            )


        # -------------------------------------------------
        # Find existing user
        # -------------------------------------------------

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )


        # -------------------------------------------------
        # Create new user
        # -------------------------------------------------

        if not user:

            username = (
                userinfo.get("nickname")
                or email.split("@")[0]
            )

            existing_username = (
                db.query(User)
                .filter(User.username == username)
                .first()
            )


            if existing_username:

                username = (
                    f"{username}_{abs(hash(email)) % 10000}"
                )


            user = User(
                username=username,
                email=email,
                password=None
            )


            db.add(user)

            db.commit()

            db.refresh(user)


        # -------------------------------------------------
        # Store session
        # -------------------------------------------------

        request.session["user_id"] = user.id

        request.session["email"] = user.email

        request.session["name"] = name

        request.session["auth0_id"] = auth0_id


        # -------------------------------------------------
        # Redirect to dashboard
        # -------------------------------------------------

        print("AUTH0 LOGIN SUCCESS")

        return RedirectResponse(
            url="/dashboard/",
            status_code=302
        )


    except HTTPException:
        raise


    except Exception as e:

        print(
            "AUTH0 CALLBACK ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=f"Auth0 authentication failed: {str(e)}"
        )