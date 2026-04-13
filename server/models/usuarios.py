from datetime import datetime
from mysql.connector import Error
import bcrypt
from config.db import get_connection

def criar_usuario(payload: dict) -> int:
    """
    payload esperado:
    {
      "nome": str,
      "email": str,
      "cpf": str,
      "nascimento": "YYYY-MM-DD",
      "senha": str,
      "endereco": {
         "cep": str, "logradouro": str, "numero": str,
         "bairro": str, "cidade": str, "estado": str
      }
    }
    """
    endereco = payload["endereco"]

    datetime.strptime(payload["nascimento"], "%Y-%m-%d")
    senha_hash = bcrypt.hashpw(payload["senha"].encode('utf-8'), bcrypt.gensalt())
    sql = """
        INSERT INTO usuarios (
            nome, email, senha, data_nascimento, cpf, cep,
            logradouro, numero, bairro, cidade, estado
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    valores = (
        payload["nome"],
        payload["email"],
        senha_hash,
        payload["nascimento"],
        payload["cpf"],
        endereco["cep"],
        endereco["logradouro"],
        endereco["numero"],
        endereco["bairro"],
        endereco["cidade"],
        endereco["estado"],
    )

    conn = None
    cur = None
    try:
        conn = get_connection()
        if conn is None:
            raise RuntimeError("Falha ao conectar ao banco de dados.")
        cur = conn.cursor()
        cur.execute(sql, valores)
        conn.commit()

        lastrowid = cur.lastrowid
        if lastrowid is None:
            raise RuntimeError("Falha ao obter o ID do usuário criado.")

        return int(lastrowid)
    except Error:
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def autenticar_usuario(cpf: str, senha: str):
    sql = """
        SELECT id, nome, email, cpf, senha
        FROM usuarios
        WHERE cpf = %s
        LIMIT 1
    """

    conn = None
    cur = None
    try:
        conn = get_connection()
        if conn is None:
            raise RuntimeError("Falha ao conectar ao banco de dados.")

        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (cpf,))
        usuario = cur.fetchone()

        if not usuario:
            return None

        senha_ok = bcrypt.checkpw(
            senha.encode('utf-8'),
            usuario['senha'].encode('utf-8') if isinstance(usuario['senha'], str) else usuario['senha']
        )

        if not senha_ok:
            return None 

        usuario.pop('senha')
        return usuario

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def usuario_existe(cpf: str = None, email: str = None) -> bool:
    if not cpf and not email:
        return False

    condicoes = []
    valores = []

    if cpf:
        condicoes.append("cpf = %s")
        valores.append(cpf)
    if email:
        condicoes.append("email = %s")
        valores.append(email)

    sql = f"SELECT id FROM usuarios WHERE {' OR '.join(condicoes)} LIMIT 1"

    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, valores)
        return cur.fetchone() is not None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()