from server.models.user_avatar import UserAvatar


def _row_to_user_avatar(row: dict) -> UserAvatar:
    return UserAvatar(
        id=row["id"],
        user_id=row["user_id"],
        image_data=row["image_data"],
        mime_type=row["mime_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UserAvatarRepository:
    @classmethod
    def get_by_user_id(cls, db, user_id: int) -> UserAvatar | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_avatars WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user_avatar(row) if row else None

    @classmethod
    def exists_by_user_id(cls, db, user_id: int) -> bool:
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM user_avatars WHERE user_id = %s LIMIT 1", (user_id,))
        found = cursor.fetchone() is not None
        cursor.close()
        return found

    @classmethod
    def upsert(cls, db, *, user_id: int, image_data: bytes, mime_type: str) -> None:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO user_avatars (user_id, image_data, mime_type)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE image_data = VALUES(image_data), mime_type = VALUES(mime_type)
            """,
            (user_id, image_data, mime_type),
        )
        cursor.close()

    @classmethod
    def delete(cls, db, user_id: int) -> None:
        cursor = db.cursor()
        cursor.execute("DELETE FROM user_avatars WHERE user_id = %s", (user_id,))
        cursor.close()
