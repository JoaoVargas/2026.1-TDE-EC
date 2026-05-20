#!/usr/bin/env python3
"""
add_column.py

Patches Python source files to scaffold a new column into the project.
Does NOT touch the database directly — adds an ALTER TABLE entry to
_apply_migrations() so the column is created on the next app startup.

Usage:
    python add_column.py <table> <column_name> <sql_type> [options]

Arguments:
    table        Target table name          (e.g. users)
    column_name  New column in snake_case   (e.g. phone)
    sql_type     SQL type string            (e.g. VARCHAR(20), INT, DATE)

Options:
    --label TEXT   Human-readable label for the HTML input
    --not-null     Add NOT NULL constraint (default: nullable)

Examples:
    python add_column.py users phone VARCHAR(20)
    python add_column.py users score INT --not-null
    python add_column.py users birth_date DATE --label "Data de nascimento"

Files patched (users table only for model/route/template):
    server/db/init_db.py
    server/models/user.py
    server/repositories/user_repository.py
    server/web/routes/cadastro.py
    server/templates/cadastro.html
    server/templates/home.html
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# ── Type maps ─────────────────────────────────────────────────────────────────

_SQL_TO_PY: dict[str, str] = {
    "VARCHAR": "str",    "CHAR": "str",      "TEXT": "str",
    "TINYTEXT": "str",   "MEDIUMTEXT": "str", "LONGTEXT": "str",
    "INT": "int",        "INTEGER": "int",    "BIGINT": "int",
    "SMALLINT": "int",   "TINYINT": "int",
    "FLOAT": "float",    "DOUBLE": "float",   "DECIMAL": "float",  "NUMERIC": "float",
    "DATE": "date",      "DATETIME": "datetime", "TIMESTAMP": "datetime",
    "BOOLEAN": "bool",   "BOOL": "bool",
    "ENUM": "str",       "JSON": "str",
}

_PY_FORM_TYPE: dict[str, str] = {
    "str": "str", "int": "int", "float": "float",
    "bool": "bool",
    "date": "str",      # HTML sends strings; caller handles fromisoformat
    "datetime": "str",
}

_PY_HTML_INPUT_TYPE: dict[str, str] = {
    "str": "text", "int": "number", "float": "number",
    "bool": "text", "date": "date", "datetime": "datetime-local",
}

_DATETIME_IMPORTS = {"date", "datetime"}


def _sql_base(sql_type: str) -> str:
    return re.match(r"[A-Za-z]+", sql_type).group(0).upper()


def sql_to_python(sql_type: str) -> str:
    return _SQL_TO_PY.get(_sql_base(sql_type), "str")


# ── I/O helpers ───────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, original: str, text: str) -> None:
    if text == original:
        print(f"  [SKIP] {path.relative_to(PROJECT_ROOT)} — no changes needed")
        return
    path.write_text(text, encoding="utf-8")
    print(f"  [OK]   {path.relative_to(PROJECT_ROOT)}")


def _warn(rel: str, reason: str) -> None:
    print(f"  [WARN] {rel} — {reason}", file=sys.stderr)


# ── Patch: server/db/init_db.py ───────────────────────────────────────────────

def patch_init_db(table: str, column: str, sql_type: str, nullable: bool) -> None:
    path = PROJECT_ROOT / "server" / "db" / "init_db.py"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    null_kw = " NOT NULL" if not nullable else ""

    # ── 1. CREATE TABLE: insert column before created_at ──────────────────────
    tbl_pat = re.compile(
        rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}\s*\(.*?(?=[ \t]+created_at)",
        re.DOTALL | re.IGNORECASE,
    )
    m = tbl_pat.search(text)
    if not m:
        _warn(rel, f"CREATE TABLE {table} block not found — skipped CREATE patch")
    elif re.search(rf"[ \t]+{re.escape(column)}[ \t]", m.group(0)):
        pass  # already present
    else:
        indent_m = re.search(r"\n([ \t]+)\w", m.group(0))
        indent = indent_m.group(1) if indent_m else "            "
        col_def = f"{indent}{column:<12} {sql_type}{null_kw},\n"
        # Insert at the end of the table block match (right before created_at)
        text = text[:m.end()] + col_def + text[m.end():]

    # ── 2. _apply_migrations: add ALTER TABLE guard ───────────────────────────
    if f'_column_exists(cursor, "{table}", "{column}")' not in text:
        migration = (
            f'\n    if not _column_exists(cursor, "{table}", "{column}"):\n'
            f'        cursor.execute(\n'
            f'            "ALTER TABLE {table} ADD COLUMN {column} {sql_type}{null_kw}"\n'
            f'        )\n'
            f'        conn.commit()\n'
        )
        m2 = re.search(r"(    cursor\.close\(\)\n)(\n+def init_db)", text)
        if m2:
            text = text[:m2.start(1)] + migration + text[m2.start(1):]
        else:
            _warn(rel, "cursor.close() anchor in _apply_migrations not found")

    # ── 3. Seed calls: add column=None to every UserRepository.create() in seed ──
    if table == "users":
        needle = f"        {column}=None,"
        matches = list(re.finditer(r"        address_id=\w+\.id,\n", text))
        for m3 in reversed(matches):
            if needle not in text[m3.start():m3.start() + 60]:
                text = text[:m3.end()] + f"        {column}=None,\n" + text[m3.end():]

    _write(path, original, text)


# ── Patch: server/models/user.py ──────────────────────────────────────────────

def patch_user_model(column: str, py_type: str, nullable: bool) -> None:
    path = PROJECT_ROOT / "server" / "models" / "user.py"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    field_type = f"{py_type} | None" if nullable else py_type

    if f"\n    {column}:" in text:
        print(f"  [SKIP] {rel} — field '{column}' already defined")
        return

    # Ensure datetime/date import exists
    if py_type in _DATETIME_IMPORTS:
        dt_m = re.search(r"from datetime import ([^\n]+)", text)
        if dt_m:
            existing = [x.strip() for x in dt_m.group(1).split(",")]
            if py_type not in existing:
                merged = ", ".join(sorted(set(existing + [py_type])))
                text = text[:dt_m.start(1)] + merged + text[dt_m.end(1):]
        else:
            text = f"from datetime import {py_type}\n" + text

    # Insert after address_id field
    anchor = re.search(r"(    address_id:\s+int\n)", text)
    if not anchor:
        anchor = re.search(r"(    created_at:)", text)
    if not anchor:
        _warn(rel, "insertion point not found")
        return

    text = text[:anchor.end()] + f"    {column}: {field_type}\n" + text[anchor.end():]
    _write(path, original, text)


# ── Patch: server/repositories/user_repository.py ────────────────────────────

def patch_user_repository(column: str, py_type: str, nullable: bool) -> None:
    path = PROJECT_ROOT / "server" / "repositories" / "user_repository.py"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    param_type = f"{py_type} | None" if nullable else py_type

    # ── _row_to_user: add field after address_id ──────────────────────────────
    if f'        {column}=row["{column}"],' not in text:
        m = re.search(r'(        address_id=row\["address_id"\],\n)', text)
        if m:
            text = text[:m.end()] + f'        {column}=row["{column}"],\n' + text[m.end():]
        else:
            _warn(rel, "_row_to_user address_id anchor not found")

    # ── create() signature: add parameter before create_default_account ───────
    if f"\n        {column}:" not in text:
        m = re.search(r"(        create_default_account: bool = True,\n)", text)
        if m:
            text = text[:m.start()] + f"        {column}: {param_type},\n" + text[m.start():]
        else:
            _warn(rel, "create_default_account anchor not found")

    # ── INSERT: columns list, VALUES %s, and values tuple ─────────────────────
    insert_start = text.find("INSERT INTO users (")
    lastrow_pos = text.find("cursor.lastrowid")
    if insert_start == -1 or lastrow_pos == -1:
        _warn(rel, "INSERT INTO users block not found")
    elif column not in text[insert_start:lastrow_pos]:
        # Add column name to column list (before address_id)
        m = re.search(r"(INSERT INTO users \([^)]+?)(,\s*address_id)(\))", text, re.DOTALL)
        if m:
            text = text[:m.end(1)] + f", {column}" + text[m.end(1):]

        # Add one %s to VALUES
        m = re.search(r"([ \t]+VALUES \([^)]+)(\))", text)
        if m:
            text = text[:m.start(2)] + ", %s" + text[m.start(2):]

        # Add variable to values tuple (before address_id)
        m = re.search(r"(                address_id,\n)", text)
        if m:
            text = text[:m.start()] + f"                {column},\n" + text[m.start():]

    _write(path, original, text)


# ── Patch: server/web/routes/cadastro.py ─────────────────────────────────────

def patch_cadastro_route(column: str, py_type: str, nullable: bool) -> None:
    path = PROJECT_ROOT / "server" / "web" / "routes" / "cadastro.py"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    form_type = _PY_FORM_TYPE.get(py_type, "str")
    param_type = f"{form_type} | None" if nullable else form_type
    default = "None" if nullable else "..."

    # ── Form parameter ────────────────────────────────────────────────────────
    if f"\n    {column}:" not in text:
        m = re.search(r"(    db=Depends\(get_db\),\n)", text)
        if m:
            text = text[:m.start()] + f"    {column}: {param_type} = Form({default}),\n" + text[m.start():]
        else:
            _warn(rel, "db=Depends anchor not found")

    # ── form_ctx dict ─────────────────────────────────────────────────────────
    if f'"{column}": {column}' not in text:
        m = re.search(r'(form_ctx\s*=\s*\{.*?)\n    \}', text, re.DOTALL)
        if m:
            text = text[:m.end(1)] + f'\n        "{column}": {column},' + text[m.end(1):]
        else:
            _warn(rel, "form_ctx closing brace anchor not found")

    # ── UserRepository.create() kwarg ─────────────────────────────────────────
    if f"            {column}={column}," not in text:
        m = re.search(r"(            address_id=address\.id,\n)", text)
        if m:
            text = text[:m.end()] + f"            {column}={column},\n" + text[m.end():]
        else:
            _warn(rel, "address_id=address.id anchor not found")

    _write(path, original, text)


# ── Patch: server/templates/cadastro.html ────────────────────────────────────

def patch_cadastro_html(column: str, label: str, py_type: str) -> None:
    path = PROJECT_ROOT / "server" / "templates" / "cadastro.html"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    if f"'{column}'" in text or f'"{column}"' in text:
        print(f"  [SKIP] {rel} — input '{column}' already present")
        return

    html_type = _PY_HTML_INPUT_TYPE.get(py_type, "text")
    type_arg = f", '{html_type}'" if html_type != "text" else ""
    input_line = (
        f"                {{{{ input_field('{column}', '{label}'"
        f"{type_arg}, value=(form.{column} | default(''))) }}}}\n"
    )

    # Insert after nascimento input (before senha)
    m = re.search(r"(\{\{ input_field\('nascimento'[^\n]+\n)", text)
    if not m:
        _warn(rel, "nascimento input anchor not found — trying before senha")
        m = re.search(r"(\{\{ input_field\('senha'[^\n]+\n)", text)
    if not m:
        _warn(rel, "insertion point not found")
        return

    text = text[:m.end()] + input_line + text[m.end():]
    _write(path, original, text)


# ── Patch: server/templates/home.html ────────────────────────────────────────

def patch_home_html(column: str, label: str) -> None:
    path = PROJECT_ROOT / "server" / "templates" / "home.html"
    rel = str(path.relative_to(PROJECT_ROOT))
    original = _read(path)
    text = original

    if f"user.{column}" in text:
        print(f"  [SKIP] {rel} — '{column}' already displayed")
        return

    display_line = f'    <p class="user-detail"><strong>{label}:</strong> {{{{ user.{column} if user else \'\' }}}}</p>\n'

    # Insert after the greeting paragraph ("Resumo rapido...")
    m = re.search(r"(    <p>Resumo rapido[^\n]+</p>\n)", text)
    if not m:
        # Fallback: after <h1> greeting
        m = re.search(r"(    <h1>[^\n]+</h1>\n)", text)
    if not m:
        _warn(rel, "greeting anchor not found in home.html")
        return

    text = text[:m.end()] + display_line + text[m.end():]
    _write(path, original, text)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new column into project source files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("table",    help="Table name           (e.g. users)")
    parser.add_argument("column",   help="Column name          (e.g. phone)")
    parser.add_argument("sql_type", help="SQL type             (e.g. VARCHAR(20))")
    parser.add_argument("--label",    default=None, help="HTML label text (default: title-cased column)")
    parser.add_argument("--not-null", action="store_true", dest="not_null", help="Add NOT NULL constraint (default: nullable)")
    args = parser.parse_args()

    table    = args.table.lower()
    column   = args.column.lower()
    sql_type = args.sql_type.upper()
    py_type  = sql_to_python(sql_type)
    label    = args.label or column.replace("_", " ").title()
    nullable = not args.not_null

    null_label = "" if nullable else " NOT NULL"
    print(f"\nScaffolding  {table}.{column}  [{sql_type}{null_label} → Python:{py_type}{'?' if nullable else ''}]\n")

    patch_init_db(table, column, sql_type, nullable)

    if table == "users":
        patch_user_model(column, py_type, nullable)
        patch_user_repository(column, py_type, nullable)
        patch_cadastro_route(column, py_type, nullable)
        patch_cadastro_html(column, label, py_type)
        patch_home_html(column, label)
    else:
        print(f"  [INFO] model/route/template patches only apply to the 'users' table — skipped")

    print("\nDone. Review changes, then restart the app to apply the migration.\n")


if __name__ == "__main__":
    main()
