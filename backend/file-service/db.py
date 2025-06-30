import os
import time
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://ezlifedb:ezlifedb@ezlife.tyhljcz.mongodb.net/?retryWrites=true&w=majority&appName=EZlife")
LOCAL_URI = "mongodb://localhost:27017"

def get_db():
    """
    Get a MongoDB database connection with retry logic and proper error handling.
    Tries Atlas first, falls back to local MongoDB if Atlas fails.
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    # Try connecting to MongoDB Atlas first
    if "mongodb+srv" in MONGO_URI or ("mongodb://" in MONGO_URI and "localhost" not in MONGO_URI):
        logger.info(f"Attempting to connect to MongoDB Atlas: {MONGO_URI.split('@')[1].split('/?')[0]}")
        
        for attempt in range(max_retries):
            try:
                # Create MongoDB client with appropriate timeouts and server API
                client = MongoClient(
                    MONGO_URI,
                    server_api=ServerApi('1'),
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=10000
                )
                
                # Test the connection
                client.admin.command('ping')
                logger.info("✅ Connected to MongoDB Atlas successfully!")
                
                # Return database handle
                return client["task_management"]
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"❌ MongoDB Atlas connection attempt {attempt+1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("❌ All MongoDB Atlas connection attempts failed")
                    logger.info("⚠️ Falling back to local MongoDB...")
            except Exception as e:
                logger.error(f"❌ Unexpected error connecting to MongoDB Atlas: {str(e)}")
                logger.info("⚠️ Falling back to local MongoDB...")
                break
    
    # Try connecting to local MongoDB as fallback or primary if MONGO_URI is local
    logger.info(f"Attempting to connect to local MongoDB ({LOCAL_URI})...")
    try:
        client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        logger.info("✅ Connected to local MongoDB successfully!")
        
        # Create task_management database if it doesn't exist
        db = client["task_management"]
        logger.info(f"Using database: task_management")
        return db
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to local MongoDB: {str(e)}")
        # If this is reached, it means both Atlas (if attempted) and local connection failed.
        # The application should not silently continue with an in-memory DB.
        raise ConnectionFailure("Could not connect to any MongoDB instance (Atlas or local). Please check your .env configuration and MongoDB server status.")

# Check if this module is being run directly
if __name__ == "__main__":
    print("🧪 Testing MongoDB connections...")
    
    # Test connection
    try:
        db_conn = get_db() # Renamed variable to avoid conflict
        print("✅ Connection successful!")
        
        # List collections in the database
        collections = db_conn.list_collection_names()
        print(f"Collections in database: {collections}")
        
        # Create test document if no documents in users collection
        if "users" not in collections or db_conn.users.count_documents({}) == 0:
            print("Creating test user...")
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            test_user = {
                "email": "test@test.com",
                "password": pwd_context.hash("12345678"),
                "created_at": time.time()
            }
            
            result = db_conn.users.insert_one(test_user)
            print(f"Test user created with ID: {result.inserted_id}")
        else:
            print(f"Users collection exists with {db_conn.users.count_documents({})} documents")
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
