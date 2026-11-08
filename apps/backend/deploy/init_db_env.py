"""Create private, ignored P0 DB settings once, without printing credentials."""

import os
import secrets
from pathlib import Path

from sqlalchemy import URL


def main() -> int:
    target = Path(__file__).resolve().parent / ".env"
    password = secrets.token_urlsafe(36)
    user, db = "oke_migration", "oke_jihye_p0"
    url = URL.create("postgresql+psycopg", username=user, password=password,
                     host="postgres", port=5432, database=db)
    contents = (f"POSTGRES_USER={user}\nPOSTGRES_DB={db}\nPOSTGRES_PASSWORD={password}\n"
                f"DATABASE_URL={url.render_as_string(hide_password=False)}\nSERVICE_MODE=app\n")
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print("deploy/.env already exists; no settings changed")
        return 0
    with os.fdopen(fd, "w") as stream:
        stream.write(contents)
    print("Created private deploy/.env; no credentials printed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
