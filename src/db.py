import sqlite3

DB_PATH = "data/processed/taste_drift.db"
SCHEMA_PATH = "sql/schema.sql"

connection = sqlite3.connect(DB_PATH)

with open(SCHEMA_PATH, "r") as f:
    schema = f.read()


connection.executescript(schema)

connection.commit()
connection.close()

print("Database created successfully.", DB_PATH)

