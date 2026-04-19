import { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import { parseDocuments } from "../services/api";
import { createDemoResult, normalizeParseResponse } from "../services/transformResult";

const TAG_OPTIONS = ["UPI Screenshot", "Utility Bill", "Receipt"];

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function UploadPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [whatsappText, setWhatsappText] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const onDrop = (acceptedFiles) => {
    const mapped = acceptedFiles.map((file, index) => ({
      id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${index}`,
      file,
      tag: ""
    }));

    setDocuments((current) => [...current, ...mapped]);
    setErrorMessage("");
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png", ".webp"],
      "application/pdf": [".pdf"]
    }
  });

  const taggedCount = useMemo(() => documents.filter((item) => item.tag).length, [documents]);

  const canGenerate = taggedCount >= 3 && !loading;

  const updateTag = (id, tag) => {
    setDocuments((current) =>
      current.map((item) => {
        if (item.id !== id) return item;
        return {
          ...item,
          tag
        };
      })
    );
  };

  const removeDocument = (id) => {
    setDocuments((current) => current.filter((item) => item.id !== id));
  };

  const goToResult = (result) => {
    window.localStorage.setItem("kamaaiproof-last-result", JSON.stringify(result));
    navigate("/result", { state: { result } });
  };

  const handleGenerate = async () => {
    if (!canGenerate) return;

    const formData = new FormData();
    const metadata = documents.map((item) => ({
      id: item.id,
      filename: item.file.name,
      mimeType: item.file.type,
      tag: item.tag
    }));

    documents.forEach((item) => {
      formData.append("files", item.file, item.file.name);
    });

    formData.append("metadata", JSON.stringify(metadata));
    formData.append("whatsappText", whatsappText);

    setLoading(true);
    setErrorMessage("");

    try {
      const payload = await parseDocuments(formData);
      const result = normalizeParseResponse(payload, documents, whatsappText);
      goToResult(result);
    } catch (error) {
      const backendMessage =
        error?.response?.data?.message ||
        "We could not process your files right now. Please check your connection or try clearer images.";
      setErrorMessage(backendMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleUseDemo = () => {
    const result = createDemoResult(documents, whatsappText);
    goToResult(result);
  };

  return (
    <section className="upload-page">
      <div className="panel-heading-row">
        <h1>Upload documents and generate your Work Passport</h1>
        <p>Minimum requirement: 3 tagged files</p>
      </div>

      <div {...getRootProps()} className={`dropzone ${isDragActive ? "active" : ""}`}>
        <input {...getInputProps()} />
        <p className="dropzone-title">Drag and drop images or PDFs here</p>
        <p className="dropzone-subtitle">Supported formats: JPG, PNG, WEBP, PDF</p>
      </div>

      <section className="documents-panel" aria-labelledby="uploaded-files-heading">
        <h2 id="uploaded-files-heading">Uploaded files</h2>

        {documents.length === 0 ? (
          <p className="helper-text">No files uploaded yet.</p>
        ) : (
          <ul className="document-list">
            {documents.map((item) => (
              <li key={item.id} className="document-item">
                <div>
                  <p className="document-name">{item.file.name}</p>
                  <p className="document-meta">{formatFileSize(item.file.size)}</p>
                </div>

                <select
                  className="select-input"
                  value={item.tag}
                  onChange={(event) => updateTag(item.id, event.target.value)}
                >
                  <option value="">Select file type</option>
                  {TAG_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>

                <button className="btn btn-ghost" type="button" onClick={() => removeDocument(item.id)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="whatsapp-panel" aria-labelledby="whatsapp-heading">
        <h2 id="whatsapp-heading">WhatsApp payment messages (Unverified)</h2>
        <textarea
          className="text-area"
          rows={6}
          placeholder="Paste payment-related messages here. They will be marked as UNVERIFIED."
          value={whatsappText}
          onChange={(event) => setWhatsappText(event.target.value)}
        />
      </section>

      <div className="action-row">
        <button className="btn btn-primary" type="button" disabled={!canGenerate} onClick={handleGenerate}>
          {loading ? <LoadingSpinner label="Generating Passport" /> : "Generate Passport"}
        </button>
        <button className="btn btn-secondary" type="button" onClick={handleUseDemo} disabled={loading}>
          Open Demo Result
        </button>
        <p className="status-text">Tagged files: {taggedCount}/3</p>
      </div>

      {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
    </section>
  );
}

export default UploadPage;
