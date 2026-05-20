from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserAvatar:
    id: int
    user_id: int
    image_data: bytes
    mime_type: str
    created_at: datetime
    updated_at: datetime
