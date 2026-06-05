import uuid

from server.models.pix_key import PixKey, PixKeyType


def _row_to_key(row: dict) -> PixKey:
    return PixKey(
        id=row["id"],
        user_id=row["user_id"],
        account_id=row["account_id"],
        key_type=PixKeyType(row["key_type"]),
        key_value=row["key_value"],
        created_at=row["created_at"],
    )


class PixKeyRepository:
    @classmethod
    def get_by_user_id(cls, db, user_id: int) -> list[PixKey]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM pix_keys WHERE user_id = %s ORDER BY created_at ASC",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_key(row) for row in rows]

    @classmethod
    def get_by_key_value(cls, db, key_value: str) -> PixKey | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM pix_keys WHERE key_value = %s",
            (key_value.lower().strip(),),
        )
        row = cursor.fetchone()
        cursor.close()
        return _row_to_key(row) if row else None

    @classmethod
    def exists_type_for_user(cls, db, user_id: int, key_type: PixKeyType) -> bool:
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM pix_keys WHERE user_id = %s AND key_type = %s",
            (user_id, key_type.value),
        )
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0

    @classmethod
    def create(
        cls,
        db,
        *,
        user_id: int,
        account_id: int,
        key_type: PixKeyType,
        key_value: str,
    ) -> PixKey | None:
        normalized = key_value.lower().strip()
        try:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO pix_keys (user_id, account_id, key_type, key_value) VALUES (%s, %s, %s, %s)",
                (user_id, account_id, key_type.value, normalized),
            )
            new_id = cursor.lastrowid
            cursor.close()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM pix_keys WHERE id = %s", (new_id,))
            row = cursor.fetchone()
            cursor.close()
            return _row_to_key(row) if row else None
        except Exception:
            return None

    @classmethod
    def create_random(cls, db, *, user_id: int, account_id: int) -> PixKey | None:
        key_value = str(uuid.uuid4())
        return cls.create(db, user_id=user_id, account_id=account_id, key_type=PixKeyType.RANDOM, key_value=key_value)

    @classmethod
    def delete(cls, db, *, pix_key_id: int, user_id: int) -> bool:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM pix_keys WHERE id = %s AND user_id = %s",
            (pix_key_id, user_id),
        )
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
