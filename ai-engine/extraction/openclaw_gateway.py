"""
openclaw_gateway.py
===================
OpenClaw Gateway: Dynamic skill discovery and invocation.

Responsibilities:
  - Load skills using SkillLoader
  - Invoke skills by name with input data
  - Handle entry point execution (Python files, etc.)
  - Return standardized results
"""

import os
import sys
import json
import logging
import importlib.util
from typing import Dict, Any, List
from extraction.skill_loader import SkillLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenClawGateway")


class OpenClawGateway:
    def __init__(self, skills_dir: str = None):
        """
        Initialize the gateway with skill discovery.
        """
        self.skills_dir = skills_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../skills")
        )
        self.skill_loader = SkillLoader(self.skills_dir)
        logger.info(f"[OpenClawGateway] Initialized with skills dir: {self.skills_dir}")
        logger.info(f"[OpenClawGateway] Available skills: {self.skill_loader.list_skills()}")

    def list_skills(self) -> List[str]:
        """
        Return list of available skills.
        """
        return self.skill_loader.list_skills()

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific skill.
        """
        skill = self.skill_loader.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")
        return skill

    def invoke_skill(self, skill_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a skill by name with input data.

        Process:
          1. Load skill manifest
          2. Get entry point
          3. Execute entry point with input data
          4. Return result

        Returns:
          {
            "status": "success" | "error",
            "skill": skill_name,
            "result": {...},
            "error": "..." (if status == "error")
          }
        """
        try:
            skill = self.skill_loader.get_skill(skill_name)
            if not skill:
                return {
                    "status": "error",
                    "skill": skill_name,
                    "error": f"Skill '{skill_name}' not found",
                }

            logger.info(f"[OpenClawGateway] Invoking skill: {skill_name}")
            logger.info(f"[OpenClawGateway] Manifest: {json.dumps(skill, indent=2)}")

            entry_point = skill.get("entry_point")
            if not entry_point:
                return {
                    "status": "error",
                    "skill": skill_name,
                    "error": "Skill manifest missing 'entry_point'",
                }

            # Resolve entry point relative to skill directory
            skill_path = os.path.join(self.skills_dir, skill_name)
            entry_path = os.path.abspath(os.path.join(skill_path, entry_point))

            # If entry path doesn't exist and goes up levels (..),
            # try resolving from project root instead
            if not os.path.exists(entry_path) and ".." in entry_point:
                project_root = os.path.abspath(os.path.join(self.skills_dir, ".."))
                entry_path = os.path.abspath(os.path.join(project_root, entry_point))
                logger.info(f"[OpenClawGateway] Entry point not found at skill path, trying project root: {entry_path}")

            logger.info(f"[OpenClawGateway] Entry point path: {entry_path}")

            if not os.path.exists(entry_path):
                return {
                    "status": "error",
                    "skill": skill_name,
                    "error": f"Entry point not found: {entry_path}",
                }

            # Execute based on file type
            if entry_path.endswith(".py"):
                result = self._execute_python_entry(entry_path, input_data)
            else:
                return {
                    "status": "error",
                    "skill": skill_name,
                    "error": f"Unsupported entry point type: {entry_path}",
                }

            return {
                "status": "success",
                "skill": skill_name,
                "result": result,
            }

        except Exception as e:
            logger.error(f"[OpenClawGateway] Error invoking skill '{skill_name}': {str(e)}")
            return {
                "status": "error",
                "skill": skill_name,
                "error": str(e),
            }

    def _execute_python_entry(self, entry_path: str, input_data: Dict[str, Any]) -> Any:
        """
        Execute a Python entry point and return result.

        For now, this assumes the entry point exports a callable function
        named 'invoke' or is the module's main execution.
        """
        logger.info(f"[OpenClawGateway] Executing Python entry: {entry_path}")

        # Add the parent directory to sys.path for imports
        parent_dir = os.path.dirname(entry_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Import the module
        spec = importlib.util.spec_from_file_location("skill_module", entry_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Try to call an 'invoke' function if it exists
        if hasattr(module, "invoke"):
            logger.info("[OpenClawGateway] Found 'invoke' function in entry point")
            result = module.invoke(input_data)
        else:
            # Otherwise just import and assume the module has done its work
            logger.warning("[OpenClawGateway] No 'invoke' function found; returning empty result")
            result = {"message": "Entry point executed", "input": input_data}

        return result
