import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv
import ocr
import retrieval

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def encode_image(image_path: str) -> tuple[str, str]:
    """Converts image to base64 for Groq Vision."""
    extension = image_path.lower().split(".")[-1]
    media_type = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded, media_type

def extract_financial_data(image_path: str) -> dict:
    """
    LEGACY ROUTE — OCR-ANCHORED RAG
    Uses Tesseract OCR to find the document type, then LLM to extract.
    """
    print(f"\n[OCR-RAG Route] Processing: {image_path}")
    ocr_text = ocr.extract_text_from_image(image_path)
    schema_context = retrieval.retrieve_template(ocr_text)
    doc_type = schema_context["document_type"]
    
    image_data, media_type = encode_image(image_path)
    return _vision_extract_step(image_data, media_type, schema_context, doc_type)

def extract_with_pure_vision(image_path: str) -> dict:
    """
    NEW ROUTE — LLM VISION ONLY
    Directly uses Groq Vision for identification and extraction.
    """
    print(f"\n[Pure Vision Route] Processing: {image_path}")
    image_data, media_type = encode_image(image_path)
    
    # Identify Pass
    id_response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
            {"type": "text", "text": "Identify this document type. Return ONLY one of: phonePe_upi, gpay_upi, bhim_upi, electricity_bill, water_bill, rent_receipt. If unknown, return 'unknown'."}
        ]}],
        temperature=0,
    )
    doc_type = id_response.choices[0].message.content.strip().lower().strip('.').replace(" ", "_")
    
    # Retrieve Schema Passively
    schema_context = retrieval.get_schema_by_type(doc_type)
    if not schema_context:
        schema_context = {"document_type": doc_type, "fields": {}}

    return _vision_extract_step(image_data, media_type, schema_context, doc_type)

def _vision_extract_step(image_data, media_type, schema_context, doc_type) -> dict:
    """Shared LLM extraction logic."""
    fields_list = ", ".join(schema_context["fields"].keys()) if schema_context["fields"] else "all visible data"
    
    prompt = f"""You are a financial document parser.
Retrieved Schema for '{doc_type}':
{json.dumps(schema_context, indent=2)}

Instructions:
1. Extract values for: {fields_list}
2. For Rent Receipts: 'landlord_name' is the name near the signature at the bottom-right. 'tenant_name' is the name written after 'Received from'.
3. For Bills: Look at the top-right and top-left header areas for dates (YYYY-MM-DD).
4. For UPI: Search the entire image for an '@' symbol to find 'upi_id'. Look for bank names in the top/bottom logos.
5. Amount must be a numeric value.
6. Return ONLY valid JSON. No conversational text. """

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
            {"type": "text", "text": prompt}
        ]}],
        temperature=0,
    )

    raw_response = response.choices[0].message.content.strip()
    print(f"\nDEBUG - Raw LLM Response for {doc_type}: {raw_response}")
    return _parse_json_response(raw_response, doc_type)

def _parse_json_response(raw_response: str, doc_type: str) -> dict:
    try:
        # Cleanup
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0].strip()
            
        extracted = json.loads(raw_response)
    except:
        start, end = raw_response.find("{"), raw_response.rfind("}") + 1
        extracted = json.loads(raw_response[start:end])
        
    if isinstance(extracted, list) and len(extracted) > 0:
        extracted = extracted[0]
    elif not isinstance(extracted, dict):
        extracted = {}

    # Flatten nested 'fields' if present
    if "fields" in extracted and isinstance(extracted["fields"], dict):
        extracted = extracted["fields"]

    fields = {k: v for k, v in extracted.items() if k != "document_type"}
    filled = sum(1 for v in fields.values() if v is not None)
    confidence = round(filled / len(fields), 2) if fields else 0.0

    return {
        "document_type": doc_type,
        "fields": fields,
        "confidence_score": confidence
    }