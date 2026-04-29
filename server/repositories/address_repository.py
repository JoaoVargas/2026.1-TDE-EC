from server.models.address import Address


def _row_to_address(row: dict) -> Address:
    return Address(
        id=row["id"],
        cep=row["cep"],
        street=row["street"],
        state=row["state"],
        city=row["city"],
        neighborhood=row["neighborhood"],
        number=row["number"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AddressRepository:
    @classmethod
    def get_by_id(cls, db, address_id: int) -> Address | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM addresses WHERE id = %s", (address_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_address(row) if row else None

    @classmethod
    def create(
        cls,
        db,
        *,
        cep: str,
        street: str,
        state: str,
        city: str,
        neighborhood: str,
        number: str,
    ) -> Address:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO addresses (cep, street, state, city, neighborhood, number)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (cep, street, state, city, neighborhood, number),
        )
        new_id = cursor.lastrowid
        cursor.close()
        return cls.get_by_id(db, new_id)
