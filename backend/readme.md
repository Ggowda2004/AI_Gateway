code to setup alembic
0 pip install alembic
0 alembic init -t async alembic
Remember all the imports must be correct and files name must be correct -> base address also
this is create a new file in alembic/versions -> that will have up and down
    1  alembic revision --autogenerate -m "initial_migration"

to actually build the physical tables
    2  alembic upgrade head


Pro-Tip: How to Roll Back
    If you ever make a mistake or want to undo this specific migration later, you can run:
    3  alembic downgrade -1