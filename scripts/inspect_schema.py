from sqlalchemy import text

from app import create_app
from app.services.database import db

app = create_app()
with app.app_context():
    cols = db.session.execute(
        text(
            "select column_name, data_type, udt_name, is_nullable "
            "from information_schema.columns "
            "where table_schema='public' and table_name='inventory_items' "
            "order by ordinal_position"
        )
    ).fetchall()
    for c in cols:
        print(c)
    print("---")
    rows = db.session.execute(
        text("select id, user_id, name from inventory_items limit 5")
    ).fetchall()
    print("rows:", rows)
