import { useState, useEffect, useRef } from "react";
import {
  sendQuestion,
  getDocuments,
  uploadFile,
  triggerIngest,
  deleteDocument,
} from "./api";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);

  const fileInputRef = useRef(null);
  const chatFileInputRef = useRef(null);

  useEffect(() => {
    fetchDocumentList();
  }, []);

  async function fetchDocumentList() {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (err) {
      console.warn("Could not load document list:", err);
    }
  }

  async function handleFileUpload(file) {
    if (!file) return;
    setUploading(true);
    setStatusMessage("");
    setError("");

    try {
      const res = await uploadFile(file);
      setStatusMessage(`Uploaded "${res.filename}". Starting ingestion...`);
      await fetchDocumentList();

      // Automatically trigger ingestion for the uploaded document
      setIngesting(true);
      const ingestRes = await triggerIngest();
      setStatusMessage(
        `Ingested ${ingestRes.files_processed || 1} file(s) (${ingestRes.chunks_created || 0} chunks). Ready to chat!`
      );
      await fetchDocumentList();
    } catch (err) {
      setError(err.message || "File upload or ingestion failed.");
    } finally {
      setUploading(false);
      setIngesting(false);
    }
  }

  async function handleManualIngest() {
    setIngesting(true);
    setStatusMessage("");
    setError("");

    try {
      const res = await triggerIngest();
      setStatusMessage(
        `Ingestion complete: ${res.files_processed} files processed, ${res.chunks_created} chunks indexed.`
      );
      await fetchDocumentList();
    } catch (err) {
      setError(err.message || "Ingestion failed.");
    } finally {
      setIngesting(false);
    }
  }

  async function handleDelete(filename) {
    if (!window.confirm(`Delete ${filename} and remove its indexed knowledge?`))
      return;
    try {
      await deleteDocument(filename);
      setStatusMessage(`Deleted "${filename}".`);
      await fetchDocumentList();
    } catch (err) {
      setError(err.message || "Failed to delete file.");
    }
  }

  async function handleSend(event) {
    event.preventDefault();

    const userQuestion = question.trim();
    if (!userQuestion || loading) return;

    // If an image was attached in chat, upload and ingest it first
    let attachedName = "";
    if (selectedFile) {
      attachedName = selectedFile.name;
      setLoading(true);
      try {
        await uploadFile(selectedFile);
        await triggerIngest();
        await fetchDocumentList();
      } catch (uploadErr) {
        console.warn("Chat attachment upload warning:", uploadErr);
      }
      setSelectedFile(null);
    }

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userQuestion,
        attachment: attachedName,
      },
    ]);

    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const data = await sendQuestion(userQuestion);

      const answer =
        typeof data === "string"
          ? data
          : data.answer ??
            data.response ??
            data.result ??
            JSON.stringify(data, null, 2);

      const sources =
        typeof data === "object" && data !== null
          ? data.sources ?? []
          : [];

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: String(answer),
          sources: Array.isArray(sources) ? sources : [],
        },
      ]);
    } catch (err) {
      setError(err.message || "Please try again after some time.");
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setMessages([]);
    setError("");
    setQuestion("");
    setSelectedFile(null);
  }

  function getSourceName(source) {
    if (typeof source === "string") {
      return source;
    }

    if (source && typeof source === "object") {
      const name = source.source || source.filename || source.name || "Document";
      const details = [];

      if (source.page_number) {
        details.push(`Page ${source.page_number}`);
      }
      if (source.sheet_name) {
        details.push(`Sheet: ${source.sheet_name}`);
      }
      if (source.row_number) {
        details.push(`Row ${source.row_number}`);
      }

      if (details.length > 0) {
        return `${name} (${details.join(", ")})`;
      }

      return name;
    }

    return String(source);
  }

  function getFileIcon(filename) {
    const ext = filename.split(".").pop().toLowerCase();
    if (["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"].includes(ext)) {
      return "🖼️";
    }
    if (ext === "pdf") return "📄";
    if (["xlsx", "xls", "csv"].includes(ext)) return "📊";
    if (["docx", "doc"].includes(ext)) return "📝";
    return "📎";
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">D</div>
          <div>
            <h2>DocuMind AI</h2>
            <p>Knowledge Assistant</p>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={handleNewChat}
          type="button"
        >
          <span>+</span> New Chat
        </button>

        <div className="sidebar-section">
          <div className="section-header-row">
            <p className="sidebar-heading">KNOWLEDGE FILES</p>
            <button
              className="refresh-btn"
              onClick={fetchDocumentList}
              title="Refresh document list"
              type="button"
            >
              ↻
            </button>
          </div>

          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.docx,.xlsx,.csv,.txt"
            onChange={(e) => {
              if (e.target.files?.[0]) {
                handleFileUpload(e.target.files[0]);
                e.target.value = "";
              }
            }}
          />

          <button
            className="upload-btn"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || ingesting}
          >
            {uploading ? "Uploading..." : "↑ Upload Document / Image"}
          </button>

          <button
            className="ingest-btn"
            type="button"
            onClick={handleManualIngest}
            disabled={uploading || ingesting}
            title="Index all files in uploads into vector store"
          >
            {ingesting ? "Indexing Chunks..." : "⚡ Re-Index / Ingest All"}
          </button>

          <div className="documents-list">
            {documents.length === 0 ? (
              <p className="no-docs-text">No uploaded files yet.</p>
            ) : (
              documents.map((doc, idx) => (
                <div key={idx} className="doc-item">
                  <span className="doc-icon">{getFileIcon(doc.filename)}</span>
                  <div className="doc-info" title={doc.filename}>
                    <span className="doc-name">{doc.filename}</span>
                    <span className="doc-size">{doc.size_kb} KB</span>
                  </div>
                  <button
                    className="doc-delete-btn"
                    onClick={() => handleDelete(doc.filename)}
                    title="Delete document"
                    type="button"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="status-indicator" />
          <div>
            <strong>Multimodal OCR RAG</strong>
            <small>Vision AI + OpenSource OCR</small>
          </div>
        </div>
      </aside>

      <main className="chat-area">
        <header className="topbar">
          <div>
            <h3>Document & Image Assistant</h3>
            <p>Accurate retrieval from images, charts, PDFs, and spreadsheets</p>
          </div>

          <div className="connection-status">
            <span className="status-dot" />
            AI Assistant Active
          </div>
        </header>

        {statusMessage && (
          <div className="status-banner">
            <span>ℹ️</span> {statusMessage}
            <button type="button" onClick={() => setStatusMessage("")}>
              ✕
            </button>
          </div>
        )}

        <section className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">✦</div>

              <h1>Chat with your documents & images</h1>

              <p>
                Ask questions about your uploaded images, infographics,
                spreadsheets, PDFs, or scanned documents.
              </p>

              <div className="suggestion-list">
                <button
                  type="button"
                  onClick={() =>
                    setQuestion("What is in the image or financial statements?")
                  }
                >
                  <span>🖼️</span>
                  What is in the financial statement image?
                  <span className="suggestion-arrow">↗</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Summarize the main points in my documents.")
                  }
                >
                  <span>✧</span>
                  Summarize my documents
                  <span className="suggestion-arrow">↗</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("What is EBITDA according to the financial statements?")
                  }
                >
                  <span>⌕</span>
                  Explain EBITDA from the image
                  <span className="suggestion-arrow">↗</span>
                </button>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div className={`message-row ${message.role}`} key={index}>
              <div className="avatar">
                {message.role === "user" ? "Y" : "D"}
              </div>

              <div className="message-content">
                <strong className="message-author">
                  {message.role === "user" ? "You" : "DocuMind AI"}
                </strong>

                {message.attachment && (
                  <div className="message-attachment">
                    <span>{getFileIcon(message.attachment)}</span> Attached:{" "}
                    <strong>{message.attachment}</strong>
                  </div>
                )}

                <div className="message-bubble">
                  <p>{message.content}</p>
                </div>

                {message.role === "assistant" &&
                  message.sources.length > 0 && (
                    <div className="sources">
                      <strong>📄 Retrieved Sources</strong>

                      <ul>
                        {message.sources.map((source, sourceIndex) => (
                          <li key={sourceIndex}>
                            <span>
                              {getFileIcon(
                                typeof source === "object"
                                  ? source.source || ""
                                  : source
                              )}
                            </span>{" "}
                            {getSourceName(source)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar">D</div>

              <div className="message-content">
                <strong className="message-author">DocuMind AI</strong>

                <div className="message-bubble loading-bubble">
                  <span className="spinner" />
                  Searching documents and images, extracting answer...
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              <strong>Something went wrong</strong>
              <p>{error}</p>
              <button type="button" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          )}
        </section>

        <div className="composer-wrapper">
          {selectedFile && (
            <div className="attachment-chip">
              <span>{getFileIcon(selectedFile.name)}</span>
              <span className="attachment-name">{selectedFile.name}</span>
              <button
                type="button"
                onClick={() => setSelectedFile(null)}
                title="Remove attachment"
              >
                ✕
              </button>
            </div>
          )}

          <form className="input-area" onSubmit={handleSend}>
            <input
              type="file"
              ref={chatFileInputRef}
              style={{ display: "none" }}
              accept=".png,.jpg,.jpeg,.webp,.bmp,.pdf,.docx,.xlsx,.csv"
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />

            <button
              className="attach-button"
              type="button"
              onClick={() => chatFileInputRef.current?.click()}
              title="Attach image or document"
              disabled={loading}
            >
              🖼️
            </button>

            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask anything about your documents or images..."
              disabled={loading}
              aria-label="Your question"
            />

            <button
              className="send-button"
              type="submit"
              disabled={loading || (!question.trim() && !selectedFile)}
            >
              {loading ? "Wait..." : "Send"}
              <span>↑</span>
            </button>
          </form>

          <p className="footer-note">
            DocuMind AI leverages Vision AI and OpenSource OCR to extract text from charts, diagrams, and scanned files.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
