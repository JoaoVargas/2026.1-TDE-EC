from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from server.models.orm_models import TipoUsuario, Usuario
from server.repositories.conta_repository import ContaRepository


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
    def get_by_id(cls, db: Session, usuario_id: int) -> Usuario | None:
        return db.get(Usuario, usuario_id)

    @classmethod
    def get_by_login(cls, db: Session, login: str) -> Usuario | None:
        normalized_login = login.strip()
        if not normalized_login:
            return None

        if "@" in normalized_login:
            lookup = Usuario.email == cls._normalize_email(normalized_login)
        else:
            lookup = Usuario.cpf == cls._normalize_cpf(normalized_login)

        return db.execute(select(Usuario).where(lookup)).scalar_one_or_none()

    @classmethod
    def exists_by_cpf_or_email(
        cls,
        db: Session,
        cpf: str | None = None,
        email: str | None = None,
    ) -> bool:
        filtros = []
        if cpf:
            filtros.append(Usuario.cpf == cls._normalize_cpf(cpf))
        if email:
            filtros.append(Usuario.email == cls._normalize_email(email))

        if not filtros:
            return False

        return db.execute(select(Usuario.id).where(or_(*filtros))).first() is not None

    @classmethod
    def is_empty(cls, db: Session) -> bool:
        count = db.execute(select(func.count()).select_from(Usuario)).scalar_one()
        return count == 0

    @classmethod
    def create(
        cls,
        db: Session,
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
        usuario = Usuario(
            nome=nome.strip(),
            email=cls._normalize_email(email),
            senha=senha_hash,
            data_nascimento=data_nascimento,
            cpf=cls._normalize_cpf(cpf),
            cep=cls._normalize_cep(cep),
            logradouro=logradouro.strip() if logradouro else None,
            numero=numero.strip() if numero else None,
            bairro=bairro.strip() if bairro else None,
            cidade=cidade.strip() if cidade else None,
            estado=estado.strip().upper() if estado else None,
            tipo_usuario=tipo_usuario,
        )
        db.add(usuario)
        db.flush()

        if criar_conta_padrao:
            ContaRepository.create(db, usuario_id=usuario.id)

        return usuario
