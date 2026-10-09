from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#hash_password: 加密密码
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

#验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#创建访问令牌
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

#
def decode_access_token(token: str) -> str:
    """
    返回 token 里的 sub（这里我们放用户名）。
    失败就抛异常给上层处理。
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    sub = payload.get("sub")
    if not sub:
        raise JWTError("missing sub")
    return sub