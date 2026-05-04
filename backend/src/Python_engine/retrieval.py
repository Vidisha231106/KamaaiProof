import chromadb
import json
import os
from sentence_transformers import SentenceTransformer

# Load embedding model once — small but accurate enough for our use case
model = SentenceTransformer("all-MiniLM-L6-v2")

# Point ChromaDB to your local chroma_store folder
client = chromadb.PersistentClient(path="./backend/src/Python_engine/chroma_store")
collection = client.get_or_create_collection("document_templates")


def load_schemas_into_chromadb():
    """
    Reads all JSON files from your Schemas folder and loads them
    into ChromaDB. Only needs to be run once — ChromaDB remembers.
    Run this manually first before anything else.
    """
    schemas_dir = "./backend/src/Python_engine/Schemas"

    for filename in os.listdir(schemas_dir):
        if filename.endswith(".json"):
            with open(f"{schemas_dir}/{filename}", encoding="utf-8") as f:
                schema = json.load(f)

            # Embed the description field and store full schema as metadata
            collection.upsert(
                ids=[schema["document_type"]],
                documents=[schema["description"]],
                metadatas=[{"schema": json.dumps(schema)}]
            )
            print(f"Loaded: {schema['document_type']}")

    print("\nAll schemas loaded into ChromaDB successfully.")


def retrieve_template(ocr_text: str) -> dict:
    """
    Takes raw OCR text from any document.
    Returns the closest matching schema as a dict.

    Example:
        schema = retrieve_template("Google Pay UPI paid 7900 raaginipriya@okaxis")
        print(schema["document_type"])
        # "gpay_upi"
    """
    results = collection.query(
        query_texts=[ocr_text],
        n_results=1
    )

    # Pull out the best match
    best_match = results["metadatas"][0][0]
    schema = json.loads(best_match["schema"])
    distance = results["distances"][0][0]

    print(f"Matched template: {schema['document_type']} (confidence distance: {distance:.3f})")
    return schema


# Run this file directly to load schemas and test retrieval
if __name__ == "__main__":
    print("=== Loading schemas into ChromaDB ===")
    load_schemas_into_chromadb()

    print("\n=== Testing retrieval ===")

    # Test 1 — should match gpay_upi
    test1 = "Google Pay UPI paid 7900 raaginipriya@okaxis Canara Bank transaction 018600621034"
    result1 = retrieve_template(test1)
    print(f"Test 1 result: {result1['document_type']}\n")

    # Test 2 — should match electricity_bill
    test2 = "BESCOM electricity bill consumer number units consumed kWh amount due billing period"
    result2 = retrieve_template(test2)
    print(f"Test 2 result: {result2['document_type']}\n")

    # Test 3 — should match rent_receipt
    test3 = "received rent payment from tenant landlord signature monthly rent amount property"
    result3 = retrieve_template(test3)
    print(f"Test 3 result: {result3['document_type']}\n")