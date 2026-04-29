from server.models.usuario import TipoUsuario, Usuario
from server.repositories.conta_repository import ContaRepository


def _row_to_usuario(row: dict) -> Usuario:
    return Usuario(
        id=row["id"],
        nome=row["nome"],
        email=row["email"],
        senha=row["senha"],
        data_nascimento=row["data_nascimento"],
        cpf=row["cpf"],
        cep=row["cep"],
        logradouro=row["logradouro"],
        numero=row["numero"],
        bairro=row["bairro"],
        cidade=row["cidade"],
        estado=row["estado"],
        tipo_usuario=TipoUsuario(row["tipo_usuario"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UsuarioRepository:
    @staticmethod
    def _normalize_cpf(value: str) -> str:
        return "".join(char for char in value if char.isdigit())

    @staticmethod
    def _normalize_email(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _normalize_cep(value: str) -> str:
        return "".join(char for char in value if char.isdigit())

    @classmethod
    def get_by_id(cls, db, usuario_id: int) -> Usuario | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_usuario(row) if row else None

    @classmethod
    def get_by_login(cls, db, login: str) -> Usuario | None:
        normalized = login.strip()
        if not normalized:
            return None

        cursor = db.cursor(dictionary=True)
        if "@" in normalized:
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s",
                (cls._normalize_email(normalized),),
            )
        else:
            cursor.execute(
                "SELECT * FROM usuarios WHERE cpf = %s",
                (cls._normalize_cpf(normalized),),
            )
        row = cursor.fetchone()
        cursor.close()
        return _row_to_usuario(row) if row else None

    @classmethod
    def exists_by_cpf_or_email(
        cls,
        db,
        cpf: str | None = None,
        email: str | None = None,
    ) -> bool:
        conditions = []
        params = []
        if cpf:
            conditions.append("cpf = %s")
            params.append(cls._normalize_cpf(cpf))
        if email:
            conditions.append("email = %s")
            params.append(cls._normalize_email(email))

        if not conditions:
            return False

        cursor = db.cursor()
        cursor.execute(
            f"SELECT id FROM usuarios WHERE {' OR '.join(conditions)} LIMIT 1",
            params,
        )
        found = cursor.fetchone() is not None
        cursor.close()
        return found

    @classmethod
    def is_empty(cls, db) -> bool:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]
        cursor.close()
        return count == 0

    @classmethod
    def count_all(cls, db) -> int:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def count_by_tipo(cls, db, tipo_usuario: TipoUsuario) -> int:
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = %s",
            (tipo_usuario.value,),
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def list_all(cls, db) -> list[Usuario]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios ORDER BY nome ASC, id ASC")
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_usuario(row) for row in rows]

    @classmethod
    def update_nome(cls, db, *, usuario_id: int, nome: str) -> Usuario | None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE usuarios SET nome = %s WHERE id = %s",
            (nome.strip(), usuario_id),
        )
        cursor.close()
        return cls.get_by_id(db, usuario_id)

    @classmethod
    def create(
        cls,
        db,
        *,
        nome: str,
        email: str,
        senha_hash: str,
        data_nascimento,
        cpf: str,
        cep: str,
        logradouro: str | None,
        numero: str | None,
        bairro: str | None,
        cidade: str | None,
        estado: str | None,
        tipo_usuario: TipoUsuario = TipoUsuario.CLIENT,
        criar_conta_padrao: bool = True,
    ) -> Usuario:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO usuarios
                (nome, email, senha, data_nascimento, cpf, cep,
                 logradouro, numero, bairro, cidade, estado, tipo_usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                nome.strip(),
                cls._normalize_email(email),
                senha_hash,
                data_nascimento,
                cls._normalize_cpf(cpf),
                cls._normalize_cep(cep),
                logradouro.strip() if logradouro else None,
                numero.strip() if numero else None,
                bairro.strip() if bairro else None,
                cidade.strip() if cidade else None,
                estado.strip().upper() if estado else None,
                tipo_usuario.value,
            ),
        )
        new_id = cursor.lastrowid
        cursor.close()

        if criar_conta_padrao:
            ContaRepository.create(db, usuario_id=new_id)

        return cls.get_by_id(db, new_id)
