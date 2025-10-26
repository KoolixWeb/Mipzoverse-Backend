"""
Database Setup Script
Run this script once to initialize the database with required indexes and configurations.

Usage:
    python setup.py
"""

import asyncio
from database import users_collection
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


async def setup_database():
    """Main setup function"""
    print("=" * 50)
    print("Database Setup Script")
    print("=" * 50)
    print()
    
    try:
        # Create indexes
        await create_indexes()
        
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