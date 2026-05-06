import os
from extraction.skill_loader import SkillLoader


def list_openclaw_skills(skills_dir=None):
    """
    Lists all available skills for OpenClaw by scanning the skills directory.
    """
    # Always use the correct skills directory relative to this script
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_skills_dir = os.path.join(base_dir, "skills")
    skills_dir = skills_dir or default_skills_dir
    loader = SkillLoader(skills_dir)
    skills = loader.list_skills()
    print("Available OpenClaw Skills:")
    for skill in skills:
        print(f"- {skill}")
    return skills

if __name__ == "__main__":
    list_openclaw_skills()
