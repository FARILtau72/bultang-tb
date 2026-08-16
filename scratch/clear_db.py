from app import create_app
from app.core.db import get_engine, _drop_current_schema, _create_schema

app = create_app()
with app.app_context():
    engine = get_engine()
    with engine.begin() as conn:
        _drop_current_schema(conn)
        _create_schema(conn)
print('Database cleared successfully')
