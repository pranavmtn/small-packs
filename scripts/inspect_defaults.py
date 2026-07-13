from sqlalchemy import text

from app import create_app
from app.services.database import db

app = create_app()
with app.app_context():
    cols = db.session.execute(
        text(
            "select column_name, column_default "
            "from information_schema.columns "
            "where table_schema='public' and table_name='inventory_items' "
            "order by ordinal_position"
        )
    ).fetchall()
    for c in cols:
        print(c)
