import os
import json
from typing import Dict, Any

class SkillLoader:
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.skills = {}
        self.load_skills()

    def load_skills(self):
        for skill_name in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, skill_name)
            manifest_path = os.path.join(skill_path, "manifest.json")
            if os.path.isdir(skill_path) and os.path.isfile(manifest_path):
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                self.skills[skill_name] = manifest

    def get_skill(self, name: str) -> Dict[str, Any]:
        return self.skills.get(name)

    def list_skills(self):
        return list(self.skills.keys())
