# KamaaiProof Frontend

This folder contains everything the end user sees and interacts with.

## Frontend Scope

The frontend is responsible for:

- Multi-page navigation and flow
- File upload and user tagging UX
- Calling the backend parse endpoint
- Rendering score and transaction summary
- Showing warning flags in plain language
- Loan comparison calculator in rupees
- Theme switching (white/navy and black/white)

The frontend is not responsible for:

- LangChain extraction logic
- Scoring algorithm source of truth
- Persistent backend storage

## Technology Stack

- React 18
- Vite
- react-router-dom
- react-dropzone
- axios
- @react-pdf/renderer (installed for PDF stage integration)

## Current Folder Structure

```
frontend/
	src/
		App.jsx
		main.jsx
		styles.css
		components/
		pages/
		services/
```

Read subfolder READMEs for module-level context.

## Routing Map

- `/` -> Landing page
- `/upload` -> Upload and tagging page
- `/result` -> Work Passport summary page

## Feature Coverage Checklist

Implemented:

- Landing page with clear headline and start action
- 5-step How It Works strip
- SDG badges
- Drag/drop upload zone for images and PDFs
- Per-file tag requirement before counting toward minimum
- Generate button disabled until at least 3 tagged files
- WhatsApp text area explicitly marked unverified
- Axios integration to backend parse endpoint
- Loading spinner during API call
- Plain-language error display
- Result page score and income summary
- Parsed document table
- Warning card rendering for flags
- Loan reality calculator with rupee-only outputs
- Dual theme support with toggle
- Responsive layout tuned for mobile widths

Pending integration opportunities:

- Direct Work Passport PDF download flow hookup
- Optional richer empty-state analytics and retry telemetry

## API Integration Contract Used by Frontend

The upload page sends:

- `files` (repeated entries)
- `metadata` (JSON string)
- `whatsappText` (plain text)

The result renderer expects normalized fields:

- `estimatedMonthlyIncome`
- `consistencyScore`
- `monthsCovered`
- `documents`
- `flags`

Normalization helper is intentionally tolerant of variant backend payload shapes.

## Environment Variables

- `VITE_BACKEND_API_URL`

Use `.env.example` as template.

## Local Development

1. Open terminal in `frontend`
2. Install dependencies: `npm install`
3. Ensure `.env` has backend URL
4. Run dev server: `npm run dev`
5. Build check: `npm run build`

## UX and Theming Notes

Theme goals:

- Light theme: white base with navy and black contrast
- Dark theme: black base with white contrast

Design goals:

- High legibility
- Professional visual hierarchy
- Motion that supports flow (not decorative noise)
- Mobile-first resilience

## Guidance for AI Agents Editing Frontend

1. Keep the route structure stable unless explicitly requested.
2. Preserve the 3-tag minimum upload guardrail.
3. Preserve rupee-only display for loan calculator outputs.
4. Keep WhatsApp-derived inputs visibly unverified.
5. Keep error messages plain-language and non-technical.
6. Validate both light and dark themes after visual edits.

## Known Constraints

- Backend endpoint behavior is still under active implementation.
- Frontend currently supports a demo fallback flow for review and testing when backend is unavailable.
