# Person 3 — Scoring Logic + Firebase + PDF Developer Execution Guide

## Overview & Expected Output
**Goal:** Process the extracted JSON into a "Consistency Score," save the session securely to Firebase, and generate the final downloadable Work Passport PDF.
**Estimated Time:** 10–12 hours

---

## Step-by-Step Execution Guide

### Step 1: Scoring Logic & Algorithm Engine (Hours 1-3)
1. Create `src/services/scoring.js` (or `.py`) in the `backend/` directory.
2. Accept the flattened array of transactions from Person 2's LangChain output.
3. **Monthly Grouping:** Group all valid transactions by calendar month (e.g., "Jan 2026", "Feb 2026").
4. **Consistency Math:** 
   - Look at the last 6 months relative to the current date.
   - Count how many of those 6 months have >0 transactions.
   - Calculate Base Score: `(Covered Months / 6) * 100`.
   - Calculate `totalIncome`: Average of the sum of transactions for the active months.
5. **Deductions & Flags:**
   - Iterate through records. If `amount` is perfectly round (e.g., exactly ₹5000, exactly ₹10000) more than 80% of the time, subtract 5 points and push a flag string: "High frequency of round-number transactions".
   - If Utility Bill `billingAddress` mismatches significantly across 2 bills, subtract 10 points and push a flag string: "Address mismatch detected".
6. Return the finalized object: `{ consistencyScore, totalIncome, months, transactions, flags }`.

### Step 2: Firebase Integration (Hours 4-6)
1. In the Google Cloud / Firebase console, create a new Firebase project.
2. Enable **Firestore Database** and **Firebase Storage**.
3. Generate a Service Account Key and save it locally (DO NOT commit to GitHub). Person 4 handles `.env.example`.
4. In `backend/src/services/firebase.js`, initialize `firebase-admin`.
5. **Data Storage Logic:** 
   - Upload original image/PDF files to Firebase Storage in a unique `session_id` folder.
   - Save the finalized scoring object to Firestore under `sessions/{session_id}`.
   - **Critial Privacy Rule:** Before saving to Firestore, scrub the JSON to ensure `senderName` or PII is obfuscated if necessary, leaving only the structural data.

### Step 3: API Integration (Hour 7)
1. Work with Person 2 to intercept request inside `POST /parse` (or create a new endpoint `POST /score`).
2. Pass Person 2's output through your scoring logic.
3. Save to Firebase.
4. Append `session_id` to the JSON and return it to Person 1's frontend.

### Step 4: PDF Generation (Hours 8-11)
1. Navigate to the `frontend/` directory (you are working in React for this component).
2. Inside `src/components/`, create `WorkPassport.jsx`.
3. Import components from `@react-pdf/renderer` (`Document`, `Page`, `View`, `Text`, `StyleSheet`).
4. **Build the Layout:**
   - **Header:** Dark background, Title: "KamaaiProof Work Passport", Date: `new Date()`.
   - **Summary Box:** `consistencyScore` in dynamic color (Green/Yellow/Red text), and `totalIncome`.
   - **Data Table:** Render rows of the `transactions` array. If a transaction came from WhatsApp, render a red "UNVERIFIED" tag next to it.
   - **Flags Box:** `flags.length > 0 ? <View>RENDER FLAGS</View> : null`.
   - **Disclaimer:** Footer text stating this document is algorithmically generated supporting evidence for MFI loan officers.
5. In `Result.jsx` (with Person 1), wrap your component in a `PDFDownloadLink` so the user can download it completely client-side.

### Step 5: Verification & Merge (Hour 12)
1. Verify the frontend sends `multipart/form-data` correctly.
2. Verify the backend parses, scores, saves, and returns the correct JSON.
3. Verify the PDF Download button actively spits out the styled PDF.
# Person 3 — Scoring Logic + Firebase + PDF Developer

## Overview
Owns consistency scoring, Firebase backend infrastructure, and the final Work Passport PDF. Acts as the integration owner bridging Frontend and Backend data.

## Stack
- Node.js / Python (scoring script)
- Firebase (Firestore, Storage, Cloud Functions / Hosted Backend)
- React PDF Renderer (`@react-pdf/renderer`)

## Responsibilities & Scope
1. **Scoring Logic Algorithm**:
   - Input: Structured JSON from Person 2 (list of transactions with date, amount, source, category).
   - Groups transactions by calendar month.
   - Counts covered months (out of the last 6) with at least one transaction.
   - Calculates base score (out of 100).
   - Applies deductions (e.g., suspiciously round numbers, mismatched addresses -> plain-English flag strings).
   - Calculates estimated monthly income (average across covered months).
   - Final Output: Object with `consistencyScore`, `totalIncome`, `months`, `transactions`, and `flags`.
2. **Firebase Setup**:
   - Configure Firestore, Storage, and backend environment.
   - Ensure CORS is configured for Frontend API calls.
   - Save session scoring result to Firestore; upload original files to Storage.
   - *Security Rule*: Never store names, phone numbers, or UPI IDs — only amounts, dates, scores, flags.
3. **PDF Generation (Work Passport)**:
   - Build `WorkPassport` React component using `@react-pdf/renderer`.
   - Dark header: App name, generation date.
   - Summary section: Color-coded large text score, income, months.
   - Table section: All document sources + verification status (WhatsApp entries labeled *UNVERIFIED* in red).
   - Fraud flags section: Renders only if flags exist.
   - Disclaimer footer: States this is supporting evidence and loan officer retains verification responsibility.
   - Use `PDFDownloadLink` for entirely in-browser generation.
4. **Integration**:
   - Agree on API response shapes with Person 2.
   - Confirm upload format from Person 1 matches the `/parse` endpoint.
