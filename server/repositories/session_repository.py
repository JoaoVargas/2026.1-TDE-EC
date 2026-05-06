import secrets
from datetime import datetime


class SessionRepository:
    @classmethod
    def create(
        cls,
        db,
        user_id: int,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        token = secrets.token_hex(32)
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (id, user_id, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (token, user_id, expires_at, ip_address, user_agent),
        )
        db.commit()
        cursor.close()
        return token

    @classmethod
    def get_user_id(cls, db, token: str) -> int | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id FROM sessions WHERE id = %s AND expires_at > UTC_TIMESTAMP()",
            (token,),
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row["user_id"]) if row else None

    @classmethod
    def delete(cls, db, token: str) -> None:
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = %s", (token,))
        db.commit()
        cursor.close()

    @classmethod
    def delete_by_user(cls, db, user_id: int) -> None:
        """Invalidate all sessions for a user (logout from all devices)."""
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
        db.commit()
        cursor.close()

    @classmethod
    def refresh(cls, db, token: str, new_expires_at: datetime) -> None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE sessions SET expires_at = %s WHERE id = %s",
            (new_expires_at, token),
        )
        db.commit()
        cursor.close()

    @classmethod
    def cleanup_expired(cls, db) -> int:
        """Delete expired sessions. Call periodically to keep the table clean."""
        cursor = db.cursor()
        cursor.execute("DELETE FROM sessions WHERE expires_at <= UTC_TIMESTAMP()")
        count = cursor.rowcount
        db.commit()
        cursor.close()
        return count
