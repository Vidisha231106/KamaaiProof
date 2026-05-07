import sys
import os
import json
from pathlib import Path

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from extraction.base_extractor import MockExtractor, OpenClawExtractor, FallbackExtractor
from pipeline.orchestrator import run_pipeline

def test_mock_extractor():
    print("\n--- Testing MockExtractor ---")
    mock = MockExtractor(document_type="upi")
    text = "Paid ₹500 to Grocery Store on 12/03/2025 via GPay"
    result = mock.run(text)
    print(f"Mock Result: {json.dumps(result, indent=2)}")
    assert "transactions" in result
    assert len(result["transactions"]) > 0
    assert result["transactions"][0]["amount"] == 500.0

def test_openclaw_fallback():
    print("\n--- Testing OpenClaw Fallback / Integrated Vision ---")
    # In the new integrated mode, the extractor is robust.
    claw = OpenClawExtractor(skill="KamaaiProof")
    mock = MockExtractor(document_type="rent")
    fallback = FallbackExtractor(claw, mock)
    
    text = "Rent payment of ₹12,000 for March 2025"
    result = fallback.run(text)
    print(f"Result: {json.dumps(result, indent=2)}")
    assert "transactions" in result
    assert len(result["transactions"]) > 0
    # The integrated vision engine returns a valid transaction even if image is missing (fallback data)
    assert result["transactions"][0]["amount"] > 0

def test_pipeline_integration():
    print("\n--- Testing Pipeline Integration ---")
    user_id = "test_user_claw"
    doc_type = "upi"
    # Using a real document from your collection
    content = "backend/src/Python_engine/Documents/bhim.jpeg"
    
    # Run pipeline (will use Integrated Vision via OpenClawExtractor)
    result = run_pipeline(user_id, doc_type, content, use_openclaw=True)
    
    print(f"Pipeline Result Summary: {json.dumps(result['summary'], indent=2)}")
    
    # Verify that pipeline completed and produced at least one structured record.
    # Income can be zero when OpenClaw fails and fallback extraction returns unclassified data.
    assert len(result["transactions"]) > 0
    assert result["summary"]["transaction_count"] > 0

if __name__ == "__main__":
    try:
        test_mock_extractor()
        test_openclaw_fallback()
        test_pipeline_integration()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)
