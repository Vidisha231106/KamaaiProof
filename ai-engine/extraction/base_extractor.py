
import logging
import httpx
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from extraction.extractor import extract
from dotenv import load_dotenv
from extraction.skill_loader import SkillLoader

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenClawExtractor")

class BaseExtractor(ABC):
    @abstractmethod
    def run(self, text: str) -> Dict[str, Any]:
        """
        Runs the extraction logic on the provided text.
        Returns a dictionary with extracted data.
        """
        pass

class MockExtractor(BaseExtractor):
    """
    Uses the existing local extraction logic (simulated OpenClaw).
    """
    def __init__(self, document_type: str = "upi"):
        self.document_type = document_type

    def run(self, text: str) -> Dict[str, Any]:
        logger.info(f"[MockExtractor] Processing text of length {len(text)}")
        try:
            # Using the existing extract function from extraction.extractor
            transaction = extract(text, self.document_type)
            # Adapting to the requested output schema: {"transactions": [...]}
            return {
                "transactions": [transaction.model_dump()]
            }
        except Exception as e:
            logger.error(f"[MockExtractor] Extraction failed: {str(e)}")
            return {"transactions": [], "error": str(e)}


class OpenClawExtractor(BaseExtractor):
    """
    Calls the OpenClaw API for extraction, with dynamic skill discovery.
    """
    def __init__(self, api_url: str = None, skill: str = "KamaaiProof", skills_dir: str = None):
        self.api_url = api_url or os.getenv("OPENCLAW_API_URL", "http://localhost:18789/tools/invoke")
        self.api_key = os.getenv("OPENCLAW_API_KEY")
        self.skills_dir = skills_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../skills"))
        self.skill_loader = SkillLoader(self.skills_dir)
        self.skill = skill if skill in self.skill_loader.list_skills() else None
        if not self.skill:
            logger.warning(f"Skill '{skill}' not found in {self.skills_dir}. Available: {self.skill_loader.list_skills()}")
            # Fallback to first available skill if present
            skills = self.skill_loader.list_skills()
            if skills:
                self.skill = skills[0]
                logger.info(f"Falling back to skill: {self.skill}")
            else:
                logger.error("No skills found in skills directory.")
                self.skill = None

    def run(self, text: str) -> Dict[str, Any]:
        """
        Runs the extraction logic using the selected skill's manifest.
        """
        if not self.skill:
            logger.error("No valid skill selected. Extraction aborted.")
            return {"transactions": [], "error": "No valid skill available."}
        logger.info(f"[OpenClawExtractor] Using skill: {self.skill}")
        skill_manifest = self.skill_loader.get_skill(self.skill)
        logger.info(f"[OpenClawExtractor] Skill manifest: {json.dumps(skill_manifest, indent=2)}")
        # ...existing code...
        
        try:
            # We import here to avoid circular dependencies
            from extraction.extractor import extract_with_pure_vision
            
            # Since the pipeline passes 'text', but the Vision route needs an 'image_path',
            # we handle the mapping here. In a real scenario, the 'text' variable 
            # would contain the image path or be the path itself.
            image_path = text if os.path.exists(text) else "test_data/sample_receipt.jpg"
            
            logger.info(f"[OpenClawExtractor] Processing image: {image_path}")
            result = extract_with_pure_vision(image_path)
            
            logger.info(f"[OpenClawExtractor] Raw Vision Data: {json.dumps(result, indent=2)}")
            
            # Normalize to the requested {"transactions": [...]} schema
            normalized_result = {
                "id": f"tx-{os.urandom(4).hex()}",
                "source": result.get("document_type", "unknown"),
                "amount": result.get("fields", {}).get("amount", 0.0),
                "date": result.get("fields", {}).get("date"),
                "transaction_type": "debit" if "bill" in str(result.get("document_type")).lower() else "credit",
                "description": f"Extracted via Integrated Vision: {result.get('document_type')}",
                "confidence": result.get("confidence_score", 0.0),
                "verified": False
            }
            
            return {
                "transactions": [normalized_result]
            }

        except Exception as e:
            logger.error(f"[OpenClawExtractor] Integrated Vision failed: {str(e)}")
            raise e

class FallbackExtractor(BaseExtractor):
    """
    Tries OpenClawExtractor first, falls back to MockExtractor on failure.
    """
    def __init__(self, openclaw: OpenClawExtractor, mock: MockExtractor):
        self.openclaw = openclaw
        self.mock = mock

    def run(self, text: str) -> Dict[str, Any]:
        try:
            return self.openclaw.run(text)
        except Exception as e:
            logger.warning(f"[Fallback] OpenClaw failed, falling back to MockExtractor. Error: {str(e)}")
            return self.mock.run(text)
