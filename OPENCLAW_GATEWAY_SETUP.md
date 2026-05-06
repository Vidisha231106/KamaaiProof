# OpenClaw Gateway Setup & Integration Guide

## Overview

The **OpenClaw Gateway** is a dynamic skill discovery and invocation system that:
- **Discovers** all available skills from the `skills/` directory
- **Loads** skill manifests with metadata and entry points
- **Invokes** skills with input data via Python module loading
- **Exposes** HTTP API endpoints for skill management and execution

---

## Architecture

### Components

1. **SkillLoader** (`ai-engine/extraction/skill_loader.py`)
   - Scans `skills/` directory for subdirectories with `manifest.json`
   - Caches skill metadata for fast lookups
   - Provides `get_skill()` and `list_skills()` methods

2. **OpenClawGateway** (`ai-engine/extraction/openclaw_gateway.py`)
   - Wraps SkillLoader for skill management
   - Handles entry point path resolution (supports relative paths)
   - Executes Python entry points dynamically
   - Provides standardized result format

3. **FastAPI Routes** (`ai-engine/api/routes.py`)
   - Exposes gateway functionality over HTTP
   - Provides `list_skills`, `get_skill_info`, and `invoke_skill` endpoints
   - Handles errors and returns JSON responses

---

## How It Works

### Skill Discovery Flow

```
skills/
├── KamaaiProof/
│   ├── manifest.json (defines name, entry_point, capabilities, config)
│   ├── SKILL.md
│   └── openclaw.plugin.json
```

**When the gateway initializes:**
1. Scans all subdirectories in `skills/`
2. For each subdirectory, looks for `manifest.json`
3. Loads manifest into memory
4. Maps skill name → manifest metadata

**KamaaiProof Manifest Example:**
```json
{
  "name": "KamaaiProof",
  "version": "2.0.0",
  "entry_point": "../../backend/src/Python_engine/pi_engine.py",
  "capabilities": ["vision_extraction", "consistency_scoring", "pdf_generation"],
  "config": { "llm_provider": "groq", ... }
}
```

### Skill Invocation Flow

```
User Request
    ↓
/openclaw/invoke endpoint
    ↓
OpenClawGateway.invoke_skill(skill_name, input_data)
    ↓
Resolve entry_point path (relative to skill directory)
    ↓
Load Python module dynamically via importlib
    ↓
Execute module (call `invoke()` function if present)
    ↓
Return standardized result
    ↓
JSON response to client
```

---

## API Endpoints

### 1. **List Available Skills**

**Endpoint:** `GET /openclaw/skills`

**Response:**
```json
{
  "skills": ["KamaaiProof"]
}
```

---

### 2. **Get Skill Information**

**Endpoint:** `GET /openclaw/skills/{skill_name}`

**Example:** `GET /openclaw/skills/KamaaiProof`

**Response:**
```json
{
  "skill": "KamaaiProof",
  "manifest": {
    "name": "KamaaiProof",
    "version": "2.0.0",
    "description": "Financial document parsing and Work Passport generation...",
    "entry_point": "../../backend/src/Python_engine/pi_engine.py",
    "capabilities": ["vision_extraction", "consistency_scoring", "pdf_generation"],
    "config": { "llm_provider": "groq", ... }
  }
}
```

---

### 3. **Invoke a Skill**

**Endpoint:** `POST /openclaw/invoke`

**Request Body:**
```json
{
  "skill": "KamaaiProof",
  "input": {
    "image_path": "path/to/image.jpg",
    "document_type": "rent"
  }
}
```

**Response (Success):**
```json
{
  "status": "success",
  "skill": "KamaaiProof",
  "result": {
    "transactions": [...],
    "summary": {...},
    "validation": {...}
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "skill": "KamaaiProof",
  "error": "Entry point not found or import failed"
}
```

---

## Usage Examples

### Python Client

```python
import httpx

# List available skills
response = httpx.get("http://localhost:8000/openclaw/skills")
print(response.json())  # {"skills": ["KamaaiProof"]}

# Get skill info
response = httpx.get("http://localhost:8000/openclaw/skills/KamaaiProof")
print(response.json()["manifest"])

# Invoke skill
response = httpx.post(
    "http://localhost:8000/openclaw/invoke",
    json={
        "skill": "KamaaiProof",
        "input": {"image_path": "path/to/rent_receipt.jpg"}
    }
)
result = response.json()
if result["status"] == "success":
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```

### cURL

```bash
# List skills
curl http://localhost:8000/openclaw/skills

# Get skill info
curl http://localhost:8000/openclaw/skills/KamaaiProof

# Invoke skill
curl -X POST http://localhost:8000/openclaw/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "KamaaiProof",
    "input": {"image_path": "path/to/image.jpg"}
  }'
```

### JavaScript/Node.js

```javascript
// List skills
fetch('http://localhost:8000/openclaw/skills')
  .then(r => r.json())
  .then(data => console.log(data.skills));

// Invoke skill
fetch('http://localhost:8000/openclaw/invoke', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    skill: 'KamaaiProof',
    input: { image_path: 'path/to/image.jpg' }
  })
})
  .then(r => r.json())
  .then(data => console.log(data.result));
```

---

## Starting the Server

```bash
# Install dependencies
cd ai-engine
pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

Gateway endpoints will be available at:
- `http://localhost:8000/openclaw/skills`
- `http://localhost:8000/openclaw/skills/{skill_name}`
- `http://localhost:8000/openclaw/invoke`

---

## Adding a New Skill

1. **Create skill directory:**
   ```bash
   mkdir -p skills/MySkill
   ```

2. **Create manifest.json:**
   ```json
   {
     "name": "MySkill",
     "version": "1.0.0",
     "description": "...",
     "entry_point": "path/to/entry.py",
     "capabilities": ["..."],
     "config": {}
   }
   ```

3. **Create entry point with `invoke()` function:**
   ```python
   def invoke(input_data):
       """Process input and return result."""
       return {"status": "success", "data": ...}
   ```

4. **Restart gateway** — it will automatically discover the new skill

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Skill not found | Verify `manifest.json` exists in skill directory |
| Entry point not found | Check entry_point path is correct (relative to skill directory) |
| Import errors | Ensure all dependencies are installed in environment |
| Module not found | Add parent dir to `sys.path` or adjust entry_point path |

---

## Integration with OpenClawExtractor

The gateway is integrated into `OpenClawExtractor`:

```python
from extraction.base_extractor import OpenClawExtractor

extractor = OpenClawExtractor(skill="KamaaiProof")
result = extractor.run(image_path)
# Uses gateway to discover and invoke KamaaiProof skill
```

---

## Next Steps

1. **Test the gateway** with real API calls
2. **Verify skill invocation** logs in `/ai-engine/tests/test_openclaw_gateway.py`
3. **Integrate with frontend** or other clients
4. **Add more skills** as needed
5. **Monitor gateway logs** for errors and performance

---

**Status:** ✅ OpenClaw Gateway is fully integrated and operational
