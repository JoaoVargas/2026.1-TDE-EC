from server.models.user import User, UserType
from server.repositories.account_repository import AccountRepository


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        cpf=row["cpf"],
        type=UserType(row["type"]),
        name=row["name"],
        email=row["email"],
        password=row["password"],
        birthday=row["birthday"],
        address_id=row["address_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UserRepository:
    @staticmethod
    def _normalize_cpf(value: str) -> str:
        return "".join(char for char in value if char.isdigit())

    @staticmethod
    def _normalize_email(value: str) -> str:
        return value.strip().lower()

    @classmethod
    def get_by_id(cls, db, user_id: int) -> User | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user(row) if row else None

    @classmethod
    def get_by_login(cls, db, login: str) -> User | None:
        normalized = login.strip()
        if not normalized:
            return None

        cursor = db.cursor(dictionary=True)
        if "@" in normalized:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (cls._normalize_email(normalized),),
            )
        else:
            cursor.execute(
                "SELECT * FROM users WHERE cpf = %s",
                (cls._normalize_cpf(normalized),),
            )
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user(row) if row else None

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
            f"SELECT id FROM users WHERE {' OR '.join(conditions)} LIMIT 1",
            params,
        )
        found = cursor.fetchone() is not None
        cursor.close()
        return found

    @classmethod
    def is_empty(cls, db) -> bool:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        return count == 0

    @classmethod
    def count_all(cls, db) -> int:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def count_by_type(cls, db, user_type: UserType) -> int:
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE type = %s",
            (user_type.value,),
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def list_all(cls, db) -> list[User]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users ORDER BY name ASC, id ASC")
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_user(row) for row in rows]

    @classmethod
    def update_name(cls, db, *, user_id: int, name: str) -> User | None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET name = %s WHERE id = %s",
            (name.strip(), user_id),
        )
        cursor.close()
        return cls.get_by_id(db, user_id)

    @classmethod
    def create(
        cls,
        db,
        *,
        cpf: str,
        type: UserType = UserType.CLIENT,
        name: str,
        email: str,
        password_hash: str,
        birthday,
        address_id: int,
        create_default_account: bool = True,
    ) -> User:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO users (cpf, type, name, email, password, birthday, address_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cls._normalize_cpf(cpf),
                type.value,
                name.strip(),
                cls._normalize_email(email),
                password_hash,
                birthday,
                address_id,
            ),
        )
        new_id = cursor.lastrowid
        cursor.close()

        if create_default_account:
            AccountRepository.create(db, user_id=new_id)

        return cls.get_by_id(db, new_id)
