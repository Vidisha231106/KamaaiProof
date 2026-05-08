import { useMemo, useState, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import { parseDocuments } from "../services/api";
import { createDemoResult, normalizeParseResponse } from "../services/transformResult";
import { useAuth } from "../contexts/AuthContext";

const TAG_OPTIONS = ["UPI Screenshot", "Utility Bill", "Receipt"];
const UPLOAD_DB_NAME = "kamaaiproof-upload-cache";
const UPLOAD_STORE_NAME = "documents";

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(name = "") {
  const parts = name.split(".");
  if (parts.length < 2) return "FILE";
  return parts.pop().toUpperCase().slice(0, 5);
}

function canPersistUploads() {
  return typeof window !== "undefined" && "indexedDB" in window;
}

function openUploadDb() {
  return new Promise((resolve, reject) => {
    if (!canPersistUploads()) {
      resolve(null);
      return;
    }

    const request = window.indexedDB.open(UPLOAD_DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(UPLOAD_STORE_NAME)) {
        db.createObjectStore(UPLOAD_STORE_NAME, { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function loadPersistedDocuments() {
  try {
    const db = await openUploadDb();
    if (!db) return [];

    return await new Promise((resolve, reject) => {
      const tx = db.transaction(UPLOAD_STORE_NAME, "readonly");
      const store = tx.objectStore(UPLOAD_STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const rows = request.result || [];
        const docs = rows
          .map((row) => {
            if (!row?.file) return null;
            const file =
              row.file instanceof File
                ? row.file
                : new File([row.file], row.name || "document", {
                    type: row.type || row.file.type || "",
                    lastModified: row.lastModified || Date.now(),
                  });
            return {
              id: row.id,
              file,
              tag: row.tag || "",
            };
          })
          .filter(Boolean);
        resolve(docs);
      };

      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.warn("[UploadPage] Failed to load cached uploads:", error);
    return [];
  }
}

async function replacePersistedDocuments(documents) {
  try {
    const db = await openUploadDb();
    if (!db) return;

    await new Promise((resolve, reject) => {
      const tx = db.transaction(UPLOAD_STORE_NAME, "readwrite");
      const store = tx.objectStore(UPLOAD_STORE_NAME);
      store.clear();

      documents.forEach((doc) => {
        store.put({
          id: doc.id,
          tag: doc.tag || "",
          file: doc.file,
          name: doc.file?.name || "document",
          type: doc.file?.type || "",
          lastModified: doc.file?.lastModified || Date.now(),
        });
      });

      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (error) {
    console.warn("[UploadPage] Failed to persist uploads:", error);
  }
}

async function clearPersistedDocuments() {
  try {
    const db = await openUploadDb();
    if (!db) return;
    await new Promise((resolve, reject) => {
      const tx = db.transaction(UPLOAD_STORE_NAME, "readwrite");
      const store = tx.objectStore(UPLOAD_STORE_NAME);
      store.clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (error) {
    console.warn("[UploadPage] Failed to clear cached uploads:", error);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// FilePreview — thumbnail for images, icon for PDF/TXT
// ─────────────────────────────────────────────────────────────────────────────
function FilePreview({ file }) {
  const [url, setUrl] = useState(null);
  const isImage = file.type.startsWith("image/");
  const isPdf   = file.type === "application/pdf";
  const isText  = file.type.startsWith("text/") || file.name.toLowerCase().endsWith(".txt");
  const extensionLabel = getFileExtension(file.name);

  useEffect(() => {
    if (!isImage) return;
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file, isImage]);

  if (isImage && url) {
    return (
      <div className="file-thumb-wrap">
        <img src={url} alt={file.name} className="file-thumb-img" />
      </div>
    );
  }

  if (isPdf) {
    return (
      <div className="file-thumb-wrap file-thumb-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
            stroke="var(--danger)" strokeWidth="1.6" strokeLinejoin="round"/>
          <path d="M14 2v6h6M8 13h8M8 17h5"
            stroke="var(--danger)" strokeWidth="1.6" strokeLinecap="round"/>
          <text x="7" y="12" fontSize="5" fill="var(--danger)" fontWeight="700">PDF</text>
        </svg>
      </div>
    );
  }

  return (
    <div className="file-thumb-wrap file-thumb-icon">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
          stroke="var(--secondary)" strokeWidth="1.6" strokeLinejoin="round"/>
        <path d="M14 2v6h6M8 13h8M8 17h8M8 9h3"
          stroke="var(--secondary)" strokeWidth="1.6" strokeLinecap="round"/>
      </svg>
      <span className="file-ext-label">{isText ? "TXT" : extensionLabel}</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// UploadPage
// ─────────────────────────────────────────────────────────────────────────────
function UploadPage() {
  const navigate  = useNavigate();
  const { user, authReady, signInWithGoogle } = useAuth();
  const [documents, setDocuments]         = useState([]);
  const [whatsappText, setWhatsappText]   = useState("");
  const [loading, setLoading]             = useState(false);
  const [errorMessage, setErrorMessage]   = useState("");
  const [recoverySessionId, setRecoverySessionId] = useState(null);
  const [lastSessionId, setLastSessionId] = useState(() =>
    window.localStorage.getItem("kamaaiproof-last-session-id")
  );
  // Progress state
  const [progressIdx, setProgressIdx]     = useState(0);
  const [progressLabel, setProgressLabel] = useState("");
  const progressInterval                  = useRef(null);
  const hasHydrated                        = useRef(false);

  useEffect(() => {
    loadPersistedDocuments().then((docs) => {
      if (docs.length) {
        setDocuments((current) => (current.length ? current : docs));
      }
      hasHydrated.current = true;
    });
  }, []);

  useEffect(() => {
    if (!hasHydrated.current) return;
    if (!documents.length) {
      clearPersistedDocuments();
      return;
    }
    replacePersistedDocuments(documents);
  }, [documents]);

  const onDrop = (acceptedFiles, rejectedFiles) => {
    if (rejectedFiles?.length) {
      setErrorMessage(
        `${rejectedFiles.length} file(s) were rejected. Try smaller files or remove any encryption.`
      );
    }
    if (!acceptedFiles.length) return;

    const mapped = acceptedFiles.map((file, i) => ({
      id: crypto?.randomUUID?.() ?? `${Date.now()}-${i}`,
      file,
      tag: "",
    }));
    setDocuments((cur) => [...cur, ...mapped]);
    setErrorMessage("");
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png", ".webp", ".heic"],
      "application/pdf": [".pdf"],
      "text/plain": [".txt", ".csv", ".md", ".log"],
      "text/csv": [".csv"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
  });

  const taggedCount  = useMemo(() => documents.filter((d) => d.tag).length, [documents]);
  const canGenerate  = taggedCount >= 1 && !loading;

  const updateTag = (id, tag) =>
    setDocuments((cur) => cur.map((d) => (d.id === id ? { ...d, tag } : d)));

  const removeDocument = (id) =>
    setDocuments((cur) => cur.filter((d) => d.id !== id));

  const handlePreview = (file) => {
    const objectUrl = URL.createObjectURL(file);
    window.open(objectUrl, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  };

  const handleResetUploads = async () => {
    clearInterval(progressInterval.current);
    setDocuments([]);
    setWhatsappText("");
    setErrorMessage("");
    setProgressIdx(0);
    setProgressLabel("");
    setRecoverySessionId(null);
    await clearPersistedDocuments();
  };

  const goToResult = (result, sessionId = null) => {
    if (sessionId) {
      window.localStorage.setItem("kamaaiproof-last-session-id", sessionId);
    }
    navigate("/result", { state: { result, sessionId } });
  };

  // ── Per-document fake progress ticker ──────────────────────────────────────
  const startProgress = (total) => {
    setProgressIdx(0);
    setProgressLabel(documents[0]?.file.name ?? "document 1");
    let idx = 0;
    progressInterval.current = setInterval(() => {
      idx = Math.min(idx + 1, total - 1);
      setProgressIdx(idx);
      setProgressLabel(documents[idx]?.file.name ?? `document ${idx + 1}`);
    }, Math.max(400, Math.min(800, (25000 / total))));  // spread across ~25 s max
  };

  const stopProgress = (total) => {
    clearInterval(progressInterval.current);
    setProgressIdx(total);
    setProgressLabel("Finalising your passport…");
  };

  // ── Generate handler ────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!canGenerate) return;

    const sessionId = crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    window.localStorage.setItem("kamaaiproof-last-session-id", sessionId);
    setLastSessionId(sessionId);
    setRecoverySessionId(sessionId);

    const formData = new FormData();
    const metadata = documents.map((d) => ({
      id:       d.id,
      filename: d.file.name,
      mimeType: d.file.type,
      tag:      d.tag,
    }));
    documents.forEach((d) => formData.append("files", d.file, d.file.name));
    formData.append("metadata",     JSON.stringify(metadata));
    formData.append("whatsappText", whatsappText);
    formData.append("sessionId", sessionId);

    setLoading(true);
    setErrorMessage("");
    startProgress(documents.length);

    try {
      const payload   = await parseDocuments(formData);
      stopProgress(documents.length);
      const resolvedSessionId = payload.session_id || sessionId;
      if (resolvedSessionId) {
        window.localStorage.setItem("kamaaiproof-last-session-id", resolvedSessionId);
        setLastSessionId(resolvedSessionId);
      }
      const result    = normalizeParseResponse(payload, documents, whatsappText);
      goToResult(result, resolvedSessionId);
    } catch (error) {
      stopProgress(documents.length);
      const isTimeout =
        error?.code === "ECONNABORTED" ||
        String(error?.message || "").toLowerCase().includes("timeout");
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        (isTimeout
          ? "Processing is taking longer than usual. Your results may still finish on the server."
          : "We could not process your files right now. Please try again.");
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleUseDemo = () => {
    const result = createDemoResult(documents, whatsappText);
    goToResult(result, null);
  };

  // ── Derived progress values ─────────────────────────────────────────────────
  const total          = documents.length || 1;
  const progressPct    = loading ? Math.min(95, (progressIdx / total) * 100) : 0;

  return (
    <section className="upload-page" aria-labelledby="upload-heading">
      <div className="panel-heading-row">
        <div>
          <h1 id="upload-heading">Upload documents and generate your Work Passport</h1>
          <p>Tag each file clearly to improve confidence in your earning summary.</p>
        </div>
        <p className="progress-pill" aria-live="polite">
          {taggedCount} file{taggedCount !== 1 ? "s" : ""} tagged
        </p>
      </div>

      {/* ── Dropzone ─────────────────────────────────────────────────────── */}
      <section className="dropzone-panel" aria-label="Upload area">
        <div
          {...getRootProps({
            role: "button",
            "aria-label": "Upload documents by dragging and dropping or selecting files",
          })}
          className={`dropzone ${isDragActive ? "active" : ""}`}
        >
          <input {...getInputProps()} />
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={{ opacity: 0.5 }}>
            <path d="M12 16V4M8 8l4-4 4 4M4 20h16"
              stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <p className="dropzone-title">Drag and drop files here, or click to browse</p>
          <p className="dropzone-subtitle">Supports images, PDFs, text, and office docs</p>
          <div className="dropzone-hint-row" aria-hidden="true">
            <span className="dropzone-hint">Secure local upload</span>
            <span className="dropzone-hint">No edits to original files</span>
            <span className="dropzone-hint">Text files work best</span>
          </div>
        </div>
      </section>

      {!documents.length && lastSessionId && (
        <section className="resume-panel" aria-label="Previous upload session">
          <div>
            <h2>Previous session detected</h2>
            <p>You can resume your most recent Work Passport results from here.</p>
          </div>
          <div className="resume-actions">
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => navigate("/result", { state: { sessionId: lastSessionId } })}
            >
              View last result
            </button>
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => {
                window.localStorage.removeItem("kamaaiproof-last-session-id");
                setLastSessionId(null);
              }}
            >
              Clear
            </button>
          </div>
        </section>
      )}

      {/* ── Uploaded files list ───────────────────────────────────────────── */}
      <section className="documents-panel" aria-labelledby="uploaded-files-heading">
        <h2 id="uploaded-files-heading">
          Uploaded files
          {documents.length > 0 && (
            <span className="file-count-badge">{documents.length}</span>
          )}
        </h2>

        {documents.length === 0 ? (
          <p className="helper-text">No files uploaded yet.</p>
        ) : (
          <ul className="document-list">
            {documents.map((item, index) => {
              const isProcessing = loading && index === progressIdx;
              const isDone       = loading && index < progressIdx;
              return (
                <li
                  key={item.id}
                  className={`document-item ${isProcessing ? "doc-processing" : ""} ${isDone ? "doc-done" : ""}`}
                >
                  {/* Thumbnail */}
                  <FilePreview file={item.file} />

                  {/* Name + meta */}
                  <div className="doc-info">
                    <p className="document-name">{item.file.name}</p>
                    <p className="document-meta">
                      {formatFileSize(item.file.size)}
                      <button
                        className="btn btn-link"
                        type="button"
                        onClick={() => handlePreview(item.file)}
                        disabled={loading}
                      >
                        Preview
                      </button>
                      {isProcessing && (
                        <span className="doc-status-label"> · Analysing…</span>
                      )}
                      {isDone && (
                        <span className="doc-status-label doc-status-done"> · Done ✓</span>
                      )}
                    </p>
                  </div>

                  {/* Tag selector */}
                  <select
                    className="select-input"
                    value={item.tag}
                    aria-label={`Select file type for ${item.file.name}`}
                    onChange={(e) => updateTag(item.id, e.target.value)}
                    disabled={loading}
                  >
                    <option value="">Select file type</option>
                    {TAG_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>

                  {/* Remove button */}
                  <button
                    className="btn btn-ghost"
                    type="button"
                    aria-label={`Remove ${item.file.name}`}
                    onClick={() => removeDocument(item.id)}
                    disabled={loading}
                  >
                    Remove
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* ── Progress bar (visible only while loading) ─────────────────────── */}
      {loading && (
        <div className="process-progress-wrap" role="status" aria-live="polite">
          <div className="process-progress-bar">
            <div
              className="process-progress-fill"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <p className="process-progress-label">
            <span className="spinner spinner-sm" aria-hidden="true" />
            {progressIdx < documents.length
              ? <>Analysing <strong>{progressLabel}</strong> ({progressIdx + 1}/{documents.length})</>
              : "Finalising your passport…"
            }
          </p>
        </div>
      )}

      {/* ── WhatsApp ─────────────────────────────────────────────────────── */}
      <section className="whatsapp-panel" aria-labelledby="whatsapp-heading">
        <h2 id="whatsapp-heading">WhatsApp payment messages <span className="tag-unverified">Unverified</span></h2>
        <textarea
          className="text-area"
          rows={5}
          placeholder="Paste payment-related messages here. They will be marked as UNVERIFIED in the passport."
          value={whatsappText}
          onChange={(e) => setWhatsappText(e.target.value)}
        />
      </section>

      {/* ── Actions ──────────────────────────────────────────────────────── */}
      <div className="action-row">
        <button
          className="btn btn-primary btn-large"
          type="button"
          disabled={!canGenerate}
          onClick={handleGenerate}
        >
          {loading
            ? <LoadingSpinner label="Generating Passport" />
            : "Generate Passport"
          }
        </button>
        <button
          className="btn btn-secondary"
          type="button"
          onClick={handleUseDemo}
          disabled={loading}
        >
          Open Demo Result
        </button>
        <button
          className="btn btn-ghost"
          type="button"
          onClick={handleResetUploads}
          disabled={loading}
        >
          Reset uploads
        </button>
        {!user && authReady && (
          <button
            className="btn btn-primary"
            type="button"
            onClick={signInWithGoogle}
            disabled={loading}
          >
            Sign in with Google
          </button>
        )}
        <p className="status-text" aria-live="polite">
          {documents.length === 0
            ? "Upload at least one file to continue."
            : taggedCount === 0
              ? "Tag at least one file to continue."
              : !user && authReady
                ? `Ready — ${taggedCount} tagged document${taggedCount !== 1 ? "s" : ""} will be analysed. Sign in to save results.`
                : canGenerate
                  ? `Ready — ${taggedCount} tagged document${taggedCount !== 1 ? "s" : ""} will be analysed.`
                  : "Generating…"
          }
        </p>
      </div>

      {errorMessage && (
        <div className="error-banner" role="alert">
          <p>{errorMessage}</p>
          {recoverySessionId && (
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => navigate("/result", { state: { sessionId: recoverySessionId } })}
            >
              Check results
            </button>
          )}
        </div>
      )}
    </section>
  );
}

export default UploadPage;
