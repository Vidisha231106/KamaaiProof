# Frontend Pages

This folder contains route-level page components.

## Current Pages

1. Landing page
2. Upload page
3. Result page

## Responsibilities by Page

### Landing

- Communicates product value in plain language.
- Drives user to upload flow.
- Shows 5-step process strip.
- Displays SDG context badges.

### Upload

- Handles drag/drop of images and PDFs.
- Requires user tag per file (UPI Screenshot, Utility Bill, Receipt).
- Enforces minimum 3 tagged files before generation.
- Collects optional WhatsApp text and marks it unverified.
- Sends multipart request to backend parse endpoint.
- Handles loading and plain-language error states.

### Result

- Displays estimated monthly income.
- Displays consistency score with visual tone.
- Renders parsed records table and verification state.
- Renders warning cards when flags exist.
- Hosts loan reality calculator.

## Editing Rules for AI Agents

1. Preserve page-level accessibility and semantic heading structure.
2. Preserve upload constraints and guardrails.
3. Keep language simple and user-facing.
4. Keep mobile layout functional for narrow screens.
5. Coordinate response-shape changes with services normalization layer.