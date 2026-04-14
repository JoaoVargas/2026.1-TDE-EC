from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = "sua-chave-secreta-troque-isso"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 8  # 8 horas

def criar_token(dados: dict) -> str:
    payload = dados.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None