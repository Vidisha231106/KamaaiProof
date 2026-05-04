import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def encode_image(image_path: str) -> tuple[str, str]:
    """
    Converts image file to base64 string so it can be sent to Groq.
    Also detects whether it's a jpg or png.
    """
    extension = image_path.lower().split(".")[-1]
    media_type = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"
    
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    return encoded, media_type


def extract_financial_data(image_path: str) -> dict:
    """
    MAIN HANDOFF FUNCTION — this is what Member 2 calls.
    
    Takes a path to any financial document image.
    Sends it to Groq Vision and returns structured JSON.
    
    Example:
        result = extract_financial_data("Documents/bhim.jpeg")
        print(result)
    """

    print(f"\nProcessing: {image_path}")
    print("=" * 40)

    # Step 1 — encode image to base64
    print("Step 1: Encoding image...")
    image_data, media_type = encode_image(image_path)

    # Step 2 — send to Groq with structured extraction prompt
    print("Step 2: Sending to Groq Vision...")
    
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """You are a financial document parser for Indian documents.

Look at this image and extract the following information.

First identify the document type — it will be one of:
- phonePe_upi
- gpay_upi  
- bhim_upi
- electricity_bill
- water_bill
- rent_receipt

Then extract all relevant fields based on document type.

For UPI payments (phonePe_upi, gpay_upi, bhim_upi) extract:
- amount (number only, no currency symbol)
- date (as it appears in the document)
- receiver_name
- upi_id (format: something@bankname)
- transaction_id
- bank_name
- status (SUCCESS, FAILED, or PENDING)

For electricity_bill extract:
- amount_due
- due_date
- consumer_number
- units_consumed
- billing_period
- discom_name

For water_bill extract:
- amount_due
- due_date
- consumer_number
- billing_period
- connection_id

For rent_receipt extract:
- rent_amount
- payment_date
- month_covered
- landlord_name
- tenant_name
- property_address

Rules:
- Return ONLY a JSON object, no explanation, no markdown, no backticks
- If a field is not visible in the image, set it to null
- Amount must be a number like 500.0 not a string like "₹500"
- Be precise, do not guess or hallucinate values not visible in the image"""
                    }
                ]
            }
        ],
        temperature=0,
    )

    # Step 3 — parse the response
    # Step 3 — parse the response
    print("Step 3: Parsing response...")
    raw_response = response.choices[0].message.content.strip()

    try:
        # First try direct parse
        extracted = json.loads(raw_response)
    except json.JSONDecodeError:
        try:
            # Find first complete JSON object by matching braces
            start = raw_response.find("{")
            depth = 0
            end = start
            for i, char in enumerate(raw_response[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            extracted = json.loads(raw_response[start:end])
        except json.JSONDecodeError as e:
            print(f"Raw response was: {raw_response}")
            raise Exception(f"Could not parse Groq response as JSON: {e}")

    # Step 4 — calculate confidence score based on filled fields
    fields = {k: v for k, v in extracted.items() if k != "document_type"}
    total = len(fields)
    filled = sum(1 for v in fields.values() if v is not None)
    confidence = round(filled / total, 2) if total > 0 else 0.0

    result = {
        "document_type": extracted.get("document_type", "unknown"),
        "fields": {k: v for k, v in extracted.items() if k != "document_type"},
        "confidence_score": confidence
    }

    print("Done.")
    print("=" * 40)

    return result


def process_multiple_images(image_paths: list) -> list:
    """
    Processes a batch of images — Member 3 needs this for 6 months of documents.
    
    Example:
        results = process_multiple_images([
            "Documents/jan_gpay.png",
            "Documents/feb_bhim.jpeg",
        ])
    """
    results = []
    for path in image_paths:
        try:
            result = extract_financial_data(path)
            results.append(result)
        except Exception as e:
            print(f"Failed to process {path}: {e}")
            results.append({
                "document_type": "unknown",
                "fields": {},
                "confidence_score": 0.0,
                "error": str(e),
                "image_path": path
            })
    return results


# Test end to end
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "backend/src/Python_engine/Documents/bhim.jpeg"

    result = extract_financial_data(image_path)

    print("\n=== FINAL EXTRACTED OUTPUT ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("==============================")