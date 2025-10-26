"""
Database Setup Script
Run this script once to initialize the database with required indexes and configurations.

Usage:
    python setup.py
"""

import asyncio
import os
from database import users_collection, email_templates_collection
from pymongo.errors import OperationFailure


async def create_indexes():
    """Create necessary database indexes"""
    print("Creating database indexes...")
    
    try:
        # Create unique index on email field
        await users_collection.create_index("email", unique=True, sparse=True)
        print("✓ Created unique index on 'email' field")
                       
    except OperationFailure as e:
        print(f"✗ Error creating indexes: {e}")
        raise


async def verify_indexes():
    """Verify that indexes were created successfully"""
    print("\nVerifying indexes...")
    
    indexes = await users_collection.index_information()
    
    print("\nExisting indexes:")
    for index_name, index_info in indexes.items():
        print(f"  - {index_name}: {index_info.get('key', [])}")
    
    return indexes


async def load_email_templates():
    """Load email templates from files into database"""
    print("\nLoading email templates...")
    
    try:
        # Read HTML template
        html_path = os.path.join("templates", "reset_password_email.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Read text template
        text_path = os.path.join("templates", "reset_password_text.txt")
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Check if template already exists
        existing_template = await email_templates_collection.find_one({"template_name": "reset_password"})
        
        template_data = {
            "template_name": "reset_password",
            "subject": "Password Reset Code",
            "html_content": html_content,
            "text_content": text_content,
            "variables": ["RESET_CODE"],
            "description": "Template for password reset emails"
        }
        
        if existing_template:
            # Update existing template
            await email_templates_collection.update_one(
                {"template_name": "reset_password"},
                {"$set": template_data}
            )
            print("✓ Updated 'reset_password' email template")
        else:
            # Insert new template
            await email_templates_collection.insert_one(template_data)
            print("✓ Inserted 'reset_password' email template")
        
    except FileNotFoundError as e:
        print(f"✗ Template file not found: {e}")
        print("  Make sure templates directory exists with required files")
        raise
    except Exception as e:
        print(f"✗ Error loading email templates: {e}")
        raise


async def setup_database():
    """Main setup function"""
    print("=" * 50)
    print("Database Setup Script")
    print("=" * 50)
    print()
    
    try:
        # Create indexes
        await create_indexes()
        
        # Load email templates
        await load_email_templates()
        
        # Verify indexes
        indexes = await verify_indexes()
        
        print("\n" + "=" * 50)
        print("✓ Database setup completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ Database setup failed: {e}")
        print("=" * 50)
        raise


if __name__ == "__main__":
    # Run the setup
    asyncio.run(setup_database())