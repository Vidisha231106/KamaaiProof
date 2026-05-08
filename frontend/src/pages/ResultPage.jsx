import { useMemo, useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import LoanRealityCalculator from "../components/LoanRealityCalculator";

function toRupees(amount) {
  const numeric = Number(amount);
  if (!Number.isFinite(numeric)) return "Not available";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(Math.round(numeric));
}

function scoreTone(score) {
  if (score >= 80) return "score-strong";
  if (score >= 50) return "score-mid";
  return "score-risk";
}

// ─────────────────────────────────────────────────────────────────────────────
// PdfDownloadButton
// Dynamically imports @react-pdf/renderer + WorkPassport after mount.
// This keeps them out of the Vite initial bundle graph, preventing the
// canvas/ESM pre-bundler crash that @react-pdf/renderer v4 causes in Vite 5.
// ─────────────────────────────────────────────────────────────────────────────

function PdfDownloadButton({ result }) {
  const [pdfReady, setPdfReady] = useState(false);
  const [PdfLink, setPdfLink] = useState(null);
  const [WorkPassportDoc, setWorkPassportDoc] = useState(null);
  const [pdfError, setPdfError] = useState(false);

  useEffect(() => {
    Promise.all([
      import("@react-pdf/renderer"),
      import("../components/WorkPassport"),
    ])
      .then(([rendererModule, passportModule]) => {
        setPdfLink(() => rendererModule.PDFDownloadLink);
        setWorkPassportDoc(() => passportModule.WorkPassport);
        setPdfReady(true);
      })
      .catch((err) => {
        console.error("[PDF] Dynamic import failed:", err);
        setPdfError(true);
      });
  }, []);

  const fileName = `KamaaiProof-WorkPassport-${new Date().toISOString().slice(0, 10)}.pdf`;

  if (pdfError) {
    return (
      <span className="btn btn-pdf" style={{ opacity: 0.5, cursor: "not-allowed" }}>
        PDF unavailable
      </span>
    );
  }

  if (!pdfReady || !PdfLink || !WorkPassportDoc) {
    return (
      <span className="btn btn-pdf" aria-busy="true" style={{ opacity: 0.6, cursor: "wait" }}>
        <span className="spinner spinner-sm" aria-hidden="true" />
        Loading PDF…
      </span>
    );
  }

  return (
    <PdfLink
      document={<WorkPassportDoc result={result} />}
      fileName={fileName}
      className="btn btn-pdf"
      aria-label="Download Work Passport as PDF"
    >
      {({ loading }) =>
        loading ? (
          <>
            <span className="spinner spinner-sm" aria-hidden="true" />
            Preparing PDF…
          </>
        ) : (
          <>
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M12 4.75V15.25M12 15.25L8.25 11.5M12 15.25L15.75 11.5M4.75 18.5H19.25"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Download Work Passport
          </>
        )
      }
    </PdfLink>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ResultPage
// ─────────────────────────────────────────────────────────────────────────────

function ResultPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const result = useMemo(() => {
    if (location.state?.result) return location.state.result;

    const cached = window.localStorage.getItem("kamaaiproof-last-result");
    if (!cached) return null;

    try {
      return JSON.parse(cached);
    } catch {
      return null;
    }
  }, [location.state]);

  if (!result) {
    return (
      <section className="result-page">
        <div className="empty-state" role="status" aria-live="polite">
          <h1>No result generated yet</h1>
          <p>Upload your documents first to generate the Work Passport summary.</p>
          <button className="btn btn-primary" type="button" onClick={() => navigate("/upload")}>
            Go to Upload
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="result-page" aria-labelledby="result-heading">
      <div className="panel-heading-row">
        <div>
          <h1 id="result-heading">Your Work Passport Summary</h1>
          <p>Portable supporting evidence for formal credit review</p>
        </div>
        <p className="progress-pill">Share-ready output</p>
      </div>

      <section className="summary-grid" aria-label="Summary highlights">
        <article className="summary-card">
          <p>Estimated Monthly Income</p>
          <h2>{toRupees(result.estimatedMonthlyIncome)}</h2>
        </article>
        <article className="summary-card">
          <p>Consistency Score</p>
          <h2 className={scoreTone(result.consistencyScore)}>{result.consistencyScore}/100</h2>
        </article>
        <article className="summary-card">
          <p>Months Covered</p>
          <h2>{result.monthsCovered || "Not provided"}</h2>
        </article>
      </section>

      <section className="table-panel" aria-labelledby="parsed-documents-heading">
        <h2 id="parsed-documents-heading">Parsed documents</h2>

        <div className="table-wrap">
          <table>
            <caption className="sr-only">Parsed documents with categories, amounts, and verification status</caption>
            <thead>
              <tr>
                <th>Source</th>
                <th>Category</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {result.documents?.length ? (
                result.documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.source}</td>
                    <td>{doc.category}</td>
                    <td>{doc.date}</td>
                    <td>{toRupees(doc.amount)}</td>
                    <td>
                      <span className={doc.verified ? "status-badge verified" : "status-badge unverified"}>
                        {doc.verified ? "Verified" : "UNVERIFIED"}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>No parsed documents available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {result.flags?.length ? (
        <section className="flag-panel" aria-labelledby="flags-heading">
          <h2 id="flags-heading">Manual review warnings</h2>
          <div className="flags-grid">
            {result.flags.map((flag, index) => (
              <article key={`${flag}-${index}`} className="flag-card">
                <p>{flag}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <LoanRealityCalculator />

      <div className="action-row action-row-end">
        {/* PDF download renders lazily after dynamic import resolves */}
        <PdfDownloadButton result={result} />

        <button className="btn btn-primary" type="button" onClick={() => navigate("/upload")}>
          Generate Another Passport
        </button>
        <button className="btn btn-secondary" type="button" onClick={() => navigate("/")}>
          Back to Landing
        </button>
      </div>
    </section>
  );
}

export default ResultPage;
