import os
import uuid
import datetime
import sqlite3
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "sentiment_analyzer")

# Global variables for db status
_db_type = "sqlite"
_mongo_client = None
_mongo_db = None
_sqlite_db_path = "sentiment_analyzer.db"

def init_db():
    global _db_type, _mongo_client, _mongo_db
    
    # Try MongoDB
    try:
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
        
        print(f"Attempting to connect to MongoDB...")
        # 2-second timeout for server selection
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        
        _mongo_client = client
        _mongo_db = client[DB_NAME]
        _db_type = "mongodb"
        print("Successfully connected to MongoDB!")
        return
    except (ServerSelectionTimeoutError, ConnectionFailure, ImportError, Exception) as e:
        print(f"MongoDB connection failed: {e}")
        print("Falling back to local SQLite database.")
        _db_type = "sqlite"
        
        # Initialize SQLite
        conn = sqlite3.connect(_sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                media_type TEXT DEFAULT 'text',
                image_data TEXT
            )
        """)
        conn.commit()
        
        # Run migrations in case database was initialized previously without these columns
        try:
            cursor.execute("ALTER TABLE reviews ADD COLUMN media_type TEXT DEFAULT 'text'")
            cursor.execute("ALTER TABLE reviews ADD COLUMN image_data TEXT")
            conn.commit()
            print("SQLite schema migrated successfully (media_type, image_data columns added).")
        except sqlite3.OperationalError:
            # Columns already exist
            pass
            
        conn.close()

def get_db_status():
    if _db_type == "mongodb":
        try:
            # Securely parse URI to isolate the hostname and drop passwords/URL parameters
            parsed = urlparse(MONGO_URI)
            clean_host = parsed.hostname if parsed.hostname else "Remote Cluster"
            return {
                "type": "MongoDB",
                "status": "Connected",
                "host": clean_host
            }
        except Exception:
            return {
                "type": "MongoDB", 
                "status": "Connected", 
                "host": "Protected Cluster Location"
            }
    else:
        return {
            "type": "SQLite (Local Fallback)",
            "status": "Active",
            "host": _sqlite_db_path
        }

def save_review(text, sentiment, confidence, media_type="text", image_data=None):
    timestamp = datetime.datetime.now().isoformat()
    
    if _db_type == "mongodb":
        try:
            review_doc = {
                "text": text,
                "sentiment": sentiment,
                "confidence": float(confidence),
                "timestamp": timestamp,
                "media_type": media_type,
                "image_data": image_data
            }
            result = _mongo_db.reviews.insert_one(review_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"MongoDB save failed: {e}. Trying SQLite fallback.")
            init_db()
            
    # SQLite fallback
    review_id = str(uuid.uuid4())
    conn = sqlite3.connect(_sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (id, text, sentiment, confidence, timestamp, media_type, image_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (review_id, text, sentiment, float(confidence), timestamp, media_type, image_data)
    )
    conn.commit()
    conn.close()
    return review_id

def get_reviews_history(limit=50, offset=0, sentiment_filter=None, search_query=None):
    if _db_type == "mongodb":
        try:
            query = {}
            if sentiment_filter and sentiment_filter.lower() != "all":
                query["sentiment"] = sentiment_filter.lower()
            if search_query:
                query["text"] = {"$regex": search_query, "$options": "i"}
                
            cursor = _mongo_db.reviews.find(query).sort("timestamp", -1).skip(offset).limit(limit)
            
            reviews = []
            for doc in cursor:
                reviews.append({
                    "id": str(doc["_id"]),
                    "text": doc["text"],
                    "sentiment": doc["sentiment"],
                    "confidence": doc["confidence"],
                    "timestamp": doc["timestamp"],
                    "media_type": doc.get("media_type", "text"),
                    "image_data": doc.get("image_data", None)
                })
            return reviews
        except Exception as e:
            print(f"MongoDB read failed: {e}. Falling back to SQLite.")
            init_db()

    # SQLite read
    conn = sqlite3.connect(_sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM reviews WHERE 1=1"
    params = []
    
    if sentiment_filter and sentiment_filter.lower() != "all":
        query += " AND sentiment = ?"
        params.append(sentiment_filter.lower())
        
    if search_query:
        # Escape wildcards (\, %, _) to prevent search-input DOS attacks in SQLite
        clean_query = search_query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query += " AND text LIKE ? ESCAPE '\\'"
        params.append(f"%{clean_query}%")
        
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    reviews = []
    for row in rows:
        reviews.append({
            "id": row["id"],
            "text": row["text"],
            "sentiment": row["sentiment"],
            "confidence": row["confidence"],
            "timestamp": row["timestamp"],
            "media_type": row["media_type"] if "media_type" in row.keys() else "text",
            "image_data": row["image_data"] if "image_data" in row.keys() else None
        })
    conn.close()
    return reviews

def get_sentiment_statistics():
    if _db_type == "mongodb":
        try:
            total_count = _mongo_db.reviews.count_documents({})
            
            sentiments = ["positive", "neutral", "negative"]
            counts = {s: 0 for s in sentiments}
            confidences = {s: 0.0 for s in sentiments}
            
            for s in sentiments:
                counts[s] = _mongo_db.reviews.count_documents({"sentiment": s})
                
                pipeline = [
                    {"$match": {"sentiment": s}},
                    {"$group": {"_id": None, "avg_conf": {"$avg": "$confidence"}}}
                ]
                agg_res = list(_mongo_db.reviews.aggregate(pipeline))
                if agg_res and agg_res[0]["avg_conf"] is not None:
                    confidences[s] = round(agg_res[0]["avg_conf"], 4)
            
            recent_cursor = _mongo_db.reviews.find({}).sort("timestamp", -1).limit(30)
            trend_data = []
            for doc in recent_cursor:
                trend_data.append({
                    "timestamp": doc["timestamp"],
                    "sentiment": doc["sentiment"],
                    "confidence": doc["confidence"]
                })
            trend_data.reverse()
            
            return {
                "total": total_count,
                "counts": counts,
                "averages": confidences,
                "trend": trend_data
            }
        except Exception as e:
            print(f"MongoDB stats failed: {e}. Falling back to SQLite.")
            init_db()
            
    # SQLite Stats fallback
    conn = sqlite3.connect(_sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_count = cursor.fetchone()[0]
    
    sentiments = ["positive", "neutral", "negative"]
    counts = {s: 0 for s in sentiments}
    confidences = {s: 0.0 for s in sentiments}
    
    for s in sentiments:
        cursor.execute("SELECT COUNT(*), AVG(confidence) FROM reviews WHERE sentiment = ?", (s,))
        row = cursor.fetchone()
        if row:
            counts[s] = row[0]
            confidences[s] = round(row[1], 4) if row[1] is not None else 0.0
            
    cursor.execute("SELECT timestamp, sentiment, confidence FROM reviews ORDER BY timestamp DESC LIMIT 30")
    rows = cursor.fetchall()
    trend_data = []
    for row in rows:
        trend_data.append({
            "timestamp": row["timestamp"],
            "sentiment": row["sentiment"],
            "confidence": row["confidence"]
        })
    trend_data.reverse()
    
    conn.close()
    
    return {
        "total": total_count,
        "counts": counts,
        "averages": confidences,
        "trend": trend_data
    }

def delete_review(review_id):
    if _db_type == "mongodb":
        try:
            from bson.objectid import ObjectId
            # Only attempt Mongo deletion if id is a valid 24-character hex ObjectId layout
            if ObjectId.is_valid(review_id):
                result = _mongo_db.reviews.delete_one({"_id": ObjectId(review_id)})
                if result.deleted_count > 0:
                    return True
            else:
                print(f"Skipping Mongo removal: ID '{review_id}' belongs to local SQLite structure.")
        except Exception as e:
            print(f"MongoDB delete failed: {e}. Trying SQLite fallback.")
            init_db()
            
    # SQLite fallback
    conn = sqlite3.connect(_sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Initialize when importing/starting
init_db()
