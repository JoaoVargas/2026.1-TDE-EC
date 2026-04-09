from datetime import datetime
from mysql.connector import Error

from server.config.db import get_connection

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
        payload["senha"],
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
    """Retorna dados mínimos do usuário quando CPF e senha conferem."""
    sql = """
        SELECT id, nome, email, cpf
        FROM usuarios
        WHERE cpf = %s AND senha = %s
        LIMIT 1
    """

    conn = None
    cur = None
    try:
        conn = get_connection()
        if conn is None:
            raise RuntimeError("Falha ao conectar ao banco de dados.")

        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (cpf, senha))
        return cur.fetchone()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()