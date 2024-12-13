from sqlmodel import create_engine, Session

DATABASE_URL = "postgresql://fastapi_user:fastapi_password@localhost:5432/fastapi_db"

engine = create_engine(DATABASE_URL)

# Dependency for DB session
def get_db():
    with Session(engine) as session:
        yield session