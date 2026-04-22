"""Data access layer modules."""

from server.repositories.table_repository import fetch_all_from_table
from server.repositories.usuario_repository import UsuarioRepository

__all__ = ["fetch_all_from_table", "UsuarioRepository"]
