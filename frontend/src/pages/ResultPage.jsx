import { useMemo, useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import LoanRealityCalculator from "../components/LoanRealityCalculator";
import { fetchSession } from "../services/api";
import { normalizeParseResponse } from "../services/transformResult";
import { useAuth } from "../contexts/AuthContext";

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
  const [WorkPassportDoc, setWorkPassportDoc] = useState(null);
  const [pdfError, setPdfError] = useState(false);
  const [generating, setGenerating] = useState(false);

  // Only import WorkPassport component — NOT @react-pdf/renderer directly here.
  // Using pdf().toBlob() on click avoids the PDFDownloadLink render-prop crash
  // that occurs when @react-pdf/renderer is excluded from Vite's optimizer.
  useEffect(() => {
    import("../components/WorkPassport")
      .then((mod) => {
        const WorkPassportComponent = mod.WorkPassport || mod.default;
        if (!WorkPassportComponent) {
          throw new Error("WorkPassport export not found");
        }
        setWorkPassportDoc(() => WorkPassportComponent);
        setPdfReady(true);
      })
      .catch((err) => {
        console.error("[PDF] WorkPassport import failed:", err);
        setPdfError(true);
      });
  }, []);

  const handleDownload = async () => {
    if (!WorkPassportDoc || generating) return;
    setGenerating(true);
    try {
      // Dynamic import of pdf() — this is the safe pattern for Vite + react-pdf v3
      const { pdf } = await import("@react-pdf/renderer");
      const blob = await pdf(<WorkPassportDoc result={result} />).toBlob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `KamaaiProof-WorkPassport-${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[PDF] Generation failed:", err);
      setPdfError(true);
    } finally {
      setGenerating(false);
    }
  };

  if (pdfError) {
    return (
      <span className="btn btn-pdf" style={{ opacity: 0.5, cursor: "not-allowed" }}>
        PDF unavailable
      </span>
    );
  }

  if (!pdfReady) {
    return (
      <span className="btn btn-pdf" style={{ opacity: 0.6, cursor: "wait" }}>
        <span className="spinner spinner-sm" aria-hidden="true" />
        Loading PDF…
      </span>
    );
  }

  return (
    <button
      className="btn btn-pdf"
      type="button"
      onClick={handleDownload}
      disabled={generating}
      aria-label="Download Work Passport as PDF"
    >
      {generating ? (
        <>
          <span className="spinner spinner-sm" aria-hidden="true" />
          Preparing PDF…
        </>
      ) : (
        <>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
      )}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ResultPage
// ─────────────────────────────────────────────────────────────────────────────

function ResultPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, authReady, signInWithGoogle } = useAuth();

  // Prefer result from router state (fresh navigation)
  const [result, setResult] = useState(location.state?.result || null);
  const [fetchError, setFetchError] = useState(null);
  const [fetching, setFetching] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // session_id from router state or localStorage (lightweight — not the full blob)
  const sessionId =
    location.state?.sessionId ||
    window.localStorage.getItem("kamaaiproof-last-session-id") ||
    null;

  // If result is absent (e.g. page refresh), attempt to re-fetch by session_id.
  // Must be declared BEFORE any conditional early returns (Rules of Hooks).
  useEffect(() => {
    if (result || fetchError) return;
    if (!sessionId) return;
    // Skip re-fetch for anonymous users — their sessions are in-memory only
    // and won't survive a server restart.
    if (!authReady) return;

    setFetching(true);
    setFetchError(null);
    fetchSession(sessionId)
      .then((payload) => {
        const restored = normalizeParseResponse(payload, [], "");
        setResult(restored);
      })
      .catch((err) => {
        const status = err?.response?.status || null;
        // 404 means the session is gone (server restarted or expired).
        // Clear the stale localStorage entry so we don't re-fetch forever.
        if (status === 404) {
          window.localStorage.removeItem("kamaaiproof-last-session-id");
        }
        setFetchError({
          status,
          message:
            err?.response?.data?.detail ||
            err?.response?.data?.message ||
            "We could not load your session right now.",
        });
      })
      .finally(() => setFetching(false));
  }, [sessionId, retryCount, authReady]); // eslint-disable-line react-hooks/exhaustive-deps


  if (!authReady && !result) {
    return (
      <section className="result-page">
        <div className="empty-state" role="status" aria-live="polite">
          <h1>Checking your sign-in…</h1>
          <p>We are verifying your authentication status.</p>
        </div>
      </section>
    );
  }


  // ── Loading state (re-fetching from Supabase) ─────────────────────────────────────────
  if (fetching) {
    return (
      <section className="result-page">
        <div className="empty-state" role="status" aria-live="polite">
          <h1>Restoring your session…</h1>
          <p>Fetching your previous results from the database.</p>
        </div>
      </section>
    );
  }

  // ── No result available ───────────────────────────────────────────────────────────
  if (!result) {
    if (!user) {
      return (
        <section className="result-page">
          <div className="empty-state" role="status" aria-live="polite">
            <h1>Sign in to view your Work Passport</h1>
            <p>Your results are secured to your account.</p>
            <div className="action-row">
              <button className="btn btn-primary" type="button" onClick={signInWithGoogle}>
                Sign in with Google
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => navigate("/upload")}>
                Back to Uploads
              </button>
            </div>
          </div>
        </section>
      );
    }

    if (sessionId && fetchError?.status === 404) {
      return (
        <section className="result-page">
          <div className="empty-state" role="status" aria-live="polite">
            <h1>Still processing your documents</h1>
            <p>Your upload is likely still running. This can happen during rate limits.</p>
            <div className="action-row">
              <button className="btn btn-primary" type="button" onClick={() => setRetryCount((c) => c + 1)}>
                Check again
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => navigate("/upload")}>
                Back to Uploads
              </button>
            </div>
          </div>
        </section>
      );
    }

    if (sessionId && fetchError) {
      return (
        <section className="result-page">
          <div className="empty-state" role="status" aria-live="polite">
            <h1>We could not load your result</h1>
            <p>{fetchError.message}</p>
            <div className="action-row">
              <button className="btn btn-primary" type="button" onClick={() => setRetryCount((c) => c + 1)}>
                Try again
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => navigate("/upload")}>
                Back to Uploads
              </button>
            </div>
          </div>
        </section>
      );
    }

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
