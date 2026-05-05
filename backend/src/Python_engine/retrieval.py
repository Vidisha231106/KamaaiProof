import json
import os

# Resolve paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_store")
SCHEMAS_DIR = os.path.join(BASE_DIR, "Schemas")

# Optional dependencies for the legacy OCR-RAG route
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_RETRIEVAL_LIBS = True
except ImportError:
    HAS_RETRIEVAL_LIBS = False
    # Only print warning if actually attempting to use ChromaDB
    # print("Warning: chromadb not found. Legacy OCR-RAG route disabled.")

# Initialize ChromaDB only if libraries are present
collection = None
if HAS_RETRIEVAL_LIBS:
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection("document_templates")
        
        # Auto-load schemas if collection is empty
        if collection.count() == 0:
            # We will define load_schemas_into_chromadb below
            pass 
    except Exception as e:
        HAS_RETRIEVAL_LIBS = False
        print(f"Warning: Failed to initialize ChromaDB: {e}")

def load_schemas_into_chromadb():
    """
    Reads all JSON files from your Schemas folder and loads them into ChromaDB.
    """
    if not HAS_RETRIEVAL_LIBS or collection is None:
        print("Error: ChromaDB retrieval is not available in this environment.")
        return

    for filename in os.listdir(SCHEMAS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(SCHEMAS_DIR, filename), encoding="utf-8") as f:
                schema = json.load(f)

            collection.upsert(
                ids=[schema["document_type"]],
                documents=[schema["description"]],
                metadatas=[{"schema": json.dumps(schema)}]
            )
            print(f"Loaded into Vector DB: {schema['document_type']}")

    print("\nAll schemas loaded into ChromaDB successfully.")

def get_schema_by_type(doc_type: str) -> dict:
    """
    Directly retrieves a schema by its type name from local JSON files.
    This is the core function for the Pure Vision route.
    """
    file_path = os.path.join(SCHEMAS_DIR, f"{doc_type}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def retrieve_template(ocr_text: str) -> dict:
    """
    Takes raw OCR text and returns the closest matching schema from Vector DB.
    Falls back to a default schema if ChromaDB is unavailable.
    """
    if not HAS_RETRIEVAL_LIBS or collection is None:
        # Fallback for when chromadb isn't working
        return get_schema_by_type("gpay_upi")

    results = collection.query(
        query_texts=[ocr_text],
        n_results=1
    )

    best_match = results["metadatas"][0][0]
    schema = json.loads(best_match["schema"])
    return schema

# Auto-initialize if possible
if HAS_RETRIEVAL_LIBS and collection is not None:
    if collection.count() == 0:
        load_schemas_into_chromadb()