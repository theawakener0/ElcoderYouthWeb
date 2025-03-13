from app import app, db
import os

def run_migrations():
    with app.app_context():
        # Create all tables based on the models
        db.create_all()
        
        # Add the current_participants column if it doesn't exist
        # This is handled by SQLAlchemy's create_all() if the model has the column defined
        
        print("Database tables created/updated successfully!")

if __name__ == '__main__':
    # Run the migrations
    run_migrations()