#!/usr/bin/env python3
"""
Migration script to remove brain and pneumonia analysis tables and keep only sunflower analysis
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from flask import Flask
from models.database import db, SunflowerAnalysis
from sqlalchemy import text

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable must be set")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def migrate_database():
    """Migrate database to sunflower-only schema"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database migration...")
        
        try:
            # Drop old tables if they exist
            print("🗑️ Dropping old brain_analyses table...")
            try:
                db.session.execute(text("DROP TABLE IF EXISTS brain_analyses CASCADE;"))
                print("✅ brain_analyses table dropped")
            except Exception as e:
                print(f"⚠️ brain_analyses table drop: {e}")
            
            print("🗑️ Dropping old pneumonia_analyses table...")
            try:
                db.session.execute(text("DROP TABLE IF EXISTS pneumonia_analyses CASCADE;"))
                print("✅ pneumonia_analyses table dropped")
            except Exception as e:
                print(f"⚠️ pneumonia_analyses table drop: {e}")
            
            # Create new sunflower_analyses table
            print("🌻 Creating sunflower_analyses table...")
            db.create_all()
            print("✅ sunflower_analyses table created")
            
            # Commit changes
            db.session.commit()
            print("✅ Database migration completed successfully!")
            
            # Verify table exists
            result = db.session.execute(text("SELECT COUNT(*) FROM sunflower_analyses;"))
            count = result.scalar()
            print(f"📊 sunflower_analyses table verified with {count} records")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    print("🚀 Sunflower Database Migration Tool")
    print("=" * 50)
    
    try:
        migrate_database()
        print("=" * 50)
        print("🎉 Migration completed successfully!")
        print("🌻 Your database now supports only sunflower disease detection")
        
    except Exception as e:
        print("=" * 50)
        print(f"💥 Migration failed: {e}")
        sys.exit(1)
