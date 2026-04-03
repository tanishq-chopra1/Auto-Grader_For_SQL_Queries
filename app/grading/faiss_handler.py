import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pymongo
import os

# MongoDB connection
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = mongo_client["grader_db"]
embeddings_collection = db["embeddings"]

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Sample expected queries (in practice, load from DB)
expected_queries = [
    "SELECT * FROM students;",
    "SELECT name FROM students WHERE id = 1;",
    "INSERT INTO students (name) VALUES ('John');"
]

def build_index():
    # Check if index exists in MongoDB
    if embeddings_collection.count_documents({}) == 0:
        embeddings = model.encode(expected_queries)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # Store in MongoDB
        for i, (query, emb) in enumerate(zip(expected_queries, embeddings)):
            embeddings_collection.insert_one({
                "id": i,
                "query": query,
                "embedding": emb.tolist()
            })
    else:
        # Load from MongoDB
        docs = list(embeddings_collection.find())
        embeddings = np.array([doc["embedding"] for doc in docs])
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
    
    return index, expected_queries

# Build index on import
index, expected_queries = build_index()

async def find_similar_queries(sql_query: str, k=5):
    query_embedding = model.encode([sql_query])
    distances, indices = index.search(query_embedding, k)
    similar = [expected_queries[i] for i in indices[0] if i < len(expected_queries)]
    return similar