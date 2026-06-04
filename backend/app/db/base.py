from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import mapped classes so Alembic autogenerate sees the complete metadata.
from app import models  # noqa: E402,F401
