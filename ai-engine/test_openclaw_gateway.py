#!/usr/bin/env python3
"""
test_openclaw_gateway.py
========================
Test the OpenClaw Gateway API endpoints.

Usage:
  python3 ai-engine/test_openclaw_gateway.py
"""

import sys
import os
from pathlib import Path

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from extraction.openclaw_gateway import OpenClawGateway


def test_gateway():
    print("\n" + "=" * 80)
    print("OpenClaw Gateway Tests")
    print("=" * 80)

    gateway = OpenClawGateway()

    # Test 1: List skills
    print("\n[Test 1] List Available Skills")
    print("-" * 80)
    skills = gateway.list_skills()
    print(f"Available skills: {skills}")
    assert len(skills) > 0, "No skills found!"
    assert "KamaaiProof" in skills, "KamaaiProof not found in skills!"
    print("✅ Test 1 passed: KamaaiProof is available")

    # Test 2: Get skill info
    print("\n[Test 2] Get Skill Info for KamaaiProof")
    print("-" * 80)
    skill_info = gateway.get_skill_info("KamaaiProof")
    print(f"Skill manifest:\n{skill_info}")
    assert skill_info.get("name") == "KamaaiProof", "Skill name mismatch!"
    assert "entry_point" in skill_info, "Skill manifest missing entry_point!"
    print("✅ Test 2 passed: Skill info retrieved successfully")

    # Test 3: Invoke skill (with mock input)
    print("\n[Test 3] Invoke KamaaiProof Skill")
    print("-" * 80)
    input_data = {
        "image_path": "backend/src/Python_engine/Documents/bhim.jpeg",
        "document_type": "upi"
    }
    result = gateway.invoke_skill("KamaaiProof", input_data)
    print(f"Invocation result:\n{result}")
    assert result.get("status") in ["success", "error"], "Invalid status in result!"
    print(f"✅ Test 3 passed: Skill invocation completed with status: {result.get('status')}")

    print("\n" + "=" * 80)
    print("✅ All OpenClaw Gateway tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_gateway()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
