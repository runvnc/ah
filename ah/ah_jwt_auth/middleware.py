from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from ah.route_decorators import public_routes, public_route

SECRET_KEY = "your-secret-key"  # Change this to a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 1 week

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return False
    except jwt.InvalidTokenError:
        print("Invalid token")
        return False

async def middleware(request: Request, call_next):
    try:
        print('-------------------------- auth middleware ----------------------------')
        print('Request URL:', request.url.path)
        if request.url.path in public_routes:
            print('Public route: ', request.url.path)
            return await call_next(request)

        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token)
            if payload:
                request.state.user = payload
                return await call_next(request)
            else:
                return RedirectResponse(url='/login')
        print("..Did not find token in cookies..")
        token = await security(request)
        if token:
            payload = decode_token(token.credentials)
            request.state.user = payload
            return await call_next(request)

        print('No valid token found?')
        print("Not a public route: ", request.url.path)
        print('Redirecting to login')
        return RedirectResponse(url='/login')
    # catch http exceptions
    except HTTPException as e:
        print('HTTPException:', e)
        return RedirectResponse(url='/login')
    except Exception as e:
        print('Error:', e)
        # print traceback
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error handling request: {e}")

    response = await call_next(request)
    return response
