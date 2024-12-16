from sqlmodel import create_engine, Session

DATABASE_URL = "postgresql://xtrimchat:xtrimchat@localhost:4001/xtrimchat"

engine = create_engine(DATABASE_URL)

# Dependency for DB session
def get_db():
    with Session(engine) as session:
        yield session