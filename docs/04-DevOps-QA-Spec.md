# Person 4 — DevOps, QA + Reliability Developer Execution Guide

## Overview & Expected Output
**Goal:** Maintain codebase structure, handle CI/CD, enforce code styling, configure environments, and own end-to-end testing. Ensure the demo goes perfectly.
**Estimated Time:** 8–10 hours

---

## Step-by-Step Execution Guide

### Step 1: Git & Codebase Setup (Hours 1-2)
1. **GitHub Initialization:** Create the remote GitHub repo. Create `main` and `dev` branches. Add branch protection to `main` (requires PRs).
2. Add `.gitignore` files to both `frontend/` (Node modules, `.env`) and `backend/` (Node modules/`__pycache__`, venv, `.env`).
3. **Linting & Prettier:** 
   - In `frontend/`: Install `eslint`, `prettier`, and `eslint-config-prettier`. Add `.prettierrc`.
   - In `backend/`: (If Node) same as above. (If Python) install `flake8` and `black`.
   - Ensure the team knows to format their code before committing.

### Step 2: Environment Variables & Documentation (Hours 3-4)
1. Open `.env.example` in both folders.
   - *Backend `backend/.env.example`:* Include `ANTHROPIC_API_KEY=`, `FIREBASE_PROJECT_ID=`, `FIREBASE_PRIVATE_KEY=`, `FIREBASE_CLIENT_EMAIL=`, `PORT=8000`.
   - *Frontend `frontend/.env.example`:* Include `VITE_BACKEND_API_URL=http://localhost:8000`.
2. Expand the root `README.md`.
   - Write incredibly explicit "How to run the backend locally" (e.g., `cd backend`, python: `python -m venv venv`, `source venv/Scripts/activate`, `pip install -r requirements.txt`, `uvicorn main:app --reload`).
   - Write explicit "How to run the frontend locally" (e.g., `npm i`, `npm run dev`).

### Step 3: Firebase Hosting & Deployment (Hours 5-6)
1. In the `frontend/` directory, run `firebase init hosting`. Log into the shared Google account.
2. Link it to the project created by Person 3.
3. Set the build directory to `dist` (if using Vite). Set as a Single Page App (rewrites to `index.html`).
4. Trigger the first deployment: `npm run build && firebase deploy --only hosting`.
5. Provide the live URL to the team so they can test their API against it. Make sure Person 2/3 update Backend CORS to allow this specific Firebase URL.

### Step 4: Quality Assurance / Core Logic Testing (Hours 7-8)
1. You are the logic gatekeeper. 
2. **Frontend Constraints Check:** Pull the `dev` branch. Open the frontend. Do the file uploads. Confirm the "Generate Passport" button is literally disabled and unclickable if you upload < 3 files, or if files aren't tagged.
3. **Math Test (Loan Calculator):**
   - Type `10000` into the loan calculator.
   - Assert the UI outputs exactly `16000` for Moneylender and `11200` for MFI based on the deck's presentation variables. If it doesn't, force Person 1 to fix the `LoanCalculator.jsx`.
4. **Mobile Check:** Open Chrome DevTools, set device to iPhone SE (375px). Verify text isn't cut off and tables don't scroll off-screen infinitely.

### Step 5: Edge Case Testing & QA Script (Hour 9)
Manually test the backend resilience:
1. Upload a completely blurry or blank image. Ensure the UI gracefully says "Data unreadable" instead of throwing a blank 500 server error screen.
2. Turn off the backend server. Click Generate. Ensure the frontend shows a "Network Error" spinner/toast gracefully.
3. Check the downloaded PDF. Verify it contains exactly the mock info and flags. Formally test rendering with 15+ rows of transactions to ensure it appropriately pages to a second page.

### Step 6: End-to-End Demo Rehearsal (Hour 10)
1. Run the entire demo flow start to finish on `localhost` and then on the deployed `Firebase` URL.
2. Note load times (LangChain prompts can take 5-10 seconds to generate). Inform the team they need a loading state, or note that the presenter must talk during this 10-second gap.
3. Confirm final merge of `dev` to `main`.
# Person 4 — DevOps, QA + Reliability Developer

## Overview
Owns codebase structure, deployment pipeline, validation, and all testing to ensure demo-readiness.

## Stack
- GitHub / Git
- ESLint, Prettier
- Firebase Hosting
- Testing Frameworks

## Responsibilities & Scope
1. **Repo & Codebase Management**:
   - Create GitHub repo with `main` (stable), `dev` (integration), and feature branches. Own all merges.
   - Configure ESLint and Prettier across frontend and backend for consistent formatting.
2. **Environment & Onboarding**:
   - Create `.env.example` file listing every required variable (Firebase keys, Claude API key, backend URL) with blank values.
   - Write clear `README.md` containing Setup steps, Environment variables context, and Local run commands.
3. **Deployment**:
   - Configure Firebase Hosting for React frontend with single-command deploy.
   - Deploy first live version fast (Hour 3) for real-URL testing.
   - Confirm backend CORS allows `localhost` and the deployed Firebase domain.
4. **Quality Assurance (QA)**:
   - Write/run tests covering critical paths:
     - Generate button disabled until 3 tagged files uploaded.
     - Loan Calculator logic (₹10,000 loan -> ₹16,000 moneylender vs ₹11,200 MFI).
     - Result page rendering correctly with mock API data.
   - Manually test edge cases (blurry image, network timeout, 375px mobile screen width, PDF with 10+ rows).
5. **End-to-End Rehearsal**:
   - Run a full demo block (Landing -> Upload -> Result -> PDF -> Calculator).
   - Coordinate fixes for freezes or broken transitions prior to final demo.
