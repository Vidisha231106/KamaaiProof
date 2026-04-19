# Person 1 — Frontend Developer (React) Execution Guide

## Overview & Expected Output
**Goal:** Build the complete interactive user interface with React. No backend logic, no AI—pure UI/UX and API integration.
**Estimated Time:** 10–12 hours

---

## Step-by-Step Execution Guide

### Step 1: Project Setup & Dependencies (Hour 1)
1. Navigate to the `frontend/` directory and initialize a React project (e.g., using Vite: `npm create vite@latest . -- --template react`).
2. Run `npm install` followed by:
   `npm install react-router-dom react-dropzone axios @react-pdf/renderer`
3. Identify the `.env.example` file and create a `.env` file with a placeholder for `VITE_BACKEND_API_URL`.
4. Run the development server to ensure everything builds correctly.

### Step 2: Routing Setup (Hour 2)
1. Open `src/App.jsx` and configure `BrowserRouter` from `react-router-dom`.
2. Create three page components inside `src/pages/`:
   - `Landing.jsx`
   - `Upload.jsx`
   - `Result.jsx`
3. Set up routes:
   - `/` -> `Landing`
   - `/upload` -> `Upload`
   - `/result` -> `Result`

### Step 3: Landing Page Implementation (Hours 3-4)
1. **Headline:** Write a clear, jargon-free H1 (e.g., "Get the Credit You Deserve with Your Everyday Proof").
2. **Call to Action:** Create a single, prominent "Start Now" button that routes to `/upload`.
3. **How It Works Strip:** Build a 5-step visual strip explaining the process in plain language (e.g., 1. Gather Documents -> 2. Upload -> 3. Verify -> 4. Score -> 5. Get Passport).
4. **Badges:** Add two SDG (Sustainable Development Goal) badges at the bottom of the page (e.g., No Poverty, Decent Work and Economic Growth).
5. **Responsiveness:** Ensure items stack nicely on a 375px mobile screen.

### Step 4: Upload Page Implementation (Hours 5-7)
1. **Drag-and-Drop Area:** Implement `react-dropzone` to accept `image/*` and `application/pdf`.
2. **File List & Tagging System:** For each dropped file, display it in a list. Provide a dropdown/radio selection mapping each file to one of three tags:
   - *UPI Screenshot*
   - *Utility Bill*
   - *Receipt*
   - *Restriction:* The file does not "count" towards the minimum until it is tagged.
3. **WhatsApp Text Area:** Below the file upload, add a `<textarea>` specifically labeled "WhatsApp Messages (Unverified)".
4. **Generate Button Logic:** Add a "Generate Passport" button. Write a `useEffect` or derived state that keeps this button `disabled` until exactly `taggedFiles.length >= 3`.

### Step 5: Result Page Implementation (Hours 8-9)
1. **State Management:** Assume the page receives a structured JSON object via React Router state (or context) containing: `consistencyScore`, `totalIncome`, `months`, `transactions`, `flags`.
2. **Income & Score Display:** 
   - Show `totalIncome` as "Estimated Monthly Income: ₹X".
   - Show `consistencyScore` with color coding (e.g., 80-100 Green, 50-79 Yellow, <50 Red).
3. **Parsed Document List:** Render a list/table of `transactions` with columns for Date, Amount, and Source. 
4. **Fraud Warning Cards:** If the `flags` array > 0, map over the array and render standard warning cards (e.g., "Suspicious mismatch on billing addresses").

### Step 6: Loan Reality Check Calculator (Hour 10)
1. Build a separate component `LoanCalculator.jsx`.
2. Add a numeric input: "Loan Amount Needed".
3. Write logic to calculate repayment:
   - Moneylender calculation (e.g., 60% per annum over 12 months) -> output in Rupees.
   - MFI calculation (e.g., 24% per annum over 12 months) -> output in Rupees.
   - Total Savings -> Moneylender Rupee - MFI Rupee.
4. Display *only* Rupee figures, no percentages. Embed this on the Result page or as a floating widget.

### Step 7: API Integration & Final Polish (Hours 11-12)
1. **Axios Integration:** In the `Upload.jsx` click handler, bundle the files (via `FormData`) and the WhatsApp text, and `POST` to `import.meta.env.VITE_BACKEND_API_URL + '/parse'`.
2. **Loaders & Error Handling:** 
   - Display a spinning loader or progress bar while the API responds.
   - Surround the call in a `try/catch`. On error, display standard, plain-language text like "We couldn't process your documents. Please try clearer photos."
3. **Mobile Testing:** Use Chrome DevTools. Check every button, grid, and text box at 375px width.
# Person 1 — Frontend Developer (React)

## Overview
Owns everything the user sees. No backend or LangChain — purely React.

## Stack
- React
- React Router DOM (`react-router-dom`)
- React Dropzone (`react-dropzone`)
- Axios (`axios`)
- React PDF Renderer (`@react-pdf/renderer`)

## Responsibilities & Scope
1. **Routing & Pages**: Configure three pages with routing: `Landing`, `Upload`, and `Result`.
2. **Landing Page**: 
   - Clear headline.
   - Single start button.
   - 5-step "How It Works" strip in plain easy language.
   - Two SDG badges at the bottom.
3. **Upload Page**:
   - Drag-and-drop file upload box accepting images and PDFs.
   - Drop files must be tagged by the user as *UPI Screenshot*, *Utility Bill*, or *Receipt* before counting.
   - Text area for WhatsApp messages clearly labeled as *unverified*.
   - Generate Passport button stays disabled until at least 3 tagged files are uploaded.
4. **Result Page**:
   - Display estimated monthly income.
   - Display consistency score with color coding.
   - List of all parsed documents with amounts and dates.
   - Fraud warning cards if the backend returned flags.
5. **Loan Reality Check Calculator**:
   - Simple input for loan amount.
   - Outputs rupee repayment figures for a moneylender versus an MFI.
   - Shows total savings for the worker (Rupees only, no percentages).
6. **API Integration & UX**:
   - Store backend API URL in a `.env` file.
   - Connect all screens to the backend API using Axios.
   - Add loading spinners during API calls.
   - Handle errors with plain-language messages.
   - Ensure every screen works cleanly on a small mobile screen.
