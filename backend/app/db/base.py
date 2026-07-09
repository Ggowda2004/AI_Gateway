from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

#DNA
# It gathers the table names, columns, and constraints into a single catalog called Base.metadata