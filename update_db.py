from app import app, db
from sqlalchemy import text

with app.app_context():
    # Add the thumbnail column to the post table
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE post ADD COLUMN thumbnail VARCHAR(200)'))
        conn.commit()
    print("Database updated successfully!")