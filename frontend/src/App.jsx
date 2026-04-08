import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from 'react-markdown'

const API_URL = import.meta.env.VITE_API_URL || "https://upsc-rag-assistant.onrender.com";


// ── PDF Upload Component ──────────────────────────────────────────────────────
function UploadPanel({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus("Uploading and processing... this may take 2-3 minutes.");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setStatus(`✅ Ingested "${data.filename}" — ${data.pages} pages, ${data.chunks} chunks`);
      setFile(null);
      onUploadSuccess();
    } catch (e) {
      setStatus(`❌ Error: ${e.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={styles.uploadPanel}>
      <div style={styles.uploadTitle}>📄 Upload a PDF</div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input
          type="file"
          accept=".pdf"
          onChange={e => setFile(e.target.files[0])}
          style={styles.fileInput}
        />
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{ ...styles.sendBtn, padding: "8px 16px", height: 36, fontSize: 13 }}
        >
          {uploading ? "Processing..." : "Upload"}
        </button>
      </div>
      {status && <div style={styles.uploadStatus}>{status}</div>}
    </div>
  );
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
function Skeleton() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
      <div style={styles.avatar}>🤖</div>
      <div style={styles.bubble("assistant")}>
        <p style={{ opacity: 0.7, margin: "0 0 8px 0", fontSize: 13, fontWeight: 500 }}>
          🔍 Searching document...
        </p>
        <div style={{ display: "flex", gap: 4, alignItems: "center", height: 12 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ ...styles.skeletonDot, animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Single chat bubble ────────────────────────────────────────────────────────
function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 12 }}>
      {!isUser && <div style={styles.avatar}>🤖</div>}
      <div style={styles.bubble(msg.role)}>
        {isUser ? (
          <p style={{ margin: 0 }}>{msg.content}</p>
        ) : (
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        )}
        {msg.pages?.length > 0 && (
          <div style={styles.pages}>📄 Source pages: {msg.pages.join(", ")}</div>
        )}
      </div>
      {isUser && <div style={styles.avatar}>👤</div>}
    </div>
  );
}

// ── Suggested prompts ───────────────────────────────────────────────────────
const SUGGESTED = [
  "What topics does this document cover?",
  "What type of questions are in this document?",
  "Summarize the key concepts in this document.",
  "Give me 3 important facts from this document.",
];

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem("upsc_chat_history");
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Persist chat to localStorage
  useEffect(() => {
    localStorage.setItem("upsc_chat_history", JSON.stringify(messages));
  }, [messages]);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-focus input on mount
  useEffect(() => { inputRef.current?.focus(); }, []);

  const sendMessage = useCallback(async (questionOverride) => {
    const question = (typeof questionOverride === "string" ? questionOverride : input).trim();
    if (!question || loading) return;

    const userMsg = { role: "user", content: question };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          history: messages.slice(-6).map(m => ({ role: m.role, content: m.content })),
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Server error");
      }
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.answer,
        pages: data.source_pages,
      }]);
    } catch (e) {
      setError(e.message || "Failed to reach the server.");
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, loading, messages]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem("upsc_chat_history");
    inputRef.current?.focus();
  };

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <div style={styles.headerTitle}>📚 UPSC RAG Assistant</div>
          <div style={styles.headerSub}>Ask anything about your study document</div>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat} style={styles.clearBtn}>🗑 Clear Chat</button>
        )}
      </div>

      {/* Upload Panel */}
      <UploadPanel onUploadSuccess={() => console.log("Upload done")} />

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <div style={{ fontSize: 48 }}>📖</div>
            <div style={styles.emptyTitle}>Ready to help you study!</div>
            <div style={styles.emptyHint}>Upload a PDF and click a suggestion, or type your own question.</div>
            <div style={styles.suggestions}>
              {SUGGESTED.map((s, i) => (
                <button
                  key={i}
                  style={styles.chip}
                  onClick={() => sendMessage(s)}
                  disabled={loading}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => <Bubble key={i} msg={msg} />)}
        {loading && <Skeleton />}
        {error && <div style={styles.error}>⚠️ {error}</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={styles.inputRow}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question… (Enter to send, Shift+Enter for new line)"
          rows={2}
          style={styles.textarea}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()} style={styles.sendBtn}>
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  page: {
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    maxWidth: 760,
    margin: "0 auto",
    background: "#f5f7fb",
  },
  header: {
    background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
    color: "#fff",
    padding: "16px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  },
  headerTitle: { fontSize: 18, fontWeight: 700, letterSpacing: 0.3 },
  headerSub: { fontSize: 12, opacity: 0.65, marginTop: 2 },
  clearBtn: {
    background: "rgba(255,255,255,0.1)",
    border: "1px solid rgba(255,255,255,0.2)",
    color: "#fff",
    borderRadius: 8,
    padding: "6px 12px",
    cursor: "pointer",
    fontSize: 13,
  },
  uploadPanel: {
    background: "#fff",
    borderBottom: "1px solid #e5e7eb",
    padding: "12px 16px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  uploadTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: "#374151",
  },
  fileInput: {
    fontSize: 13,
    color: "#374151",
  },
  uploadStatus: {
    fontSize: 12,
    color: "#6b7280",
    marginTop: 4,
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 16px",
    display: "flex",
    flexDirection: "column",
  },
  bubble: (role) => ({
    maxWidth: "78%",
    padding: "12px 16px",
    borderRadius: role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    background: role === "user" ? "linear-gradient(135deg, #667eea, #764ba2)" : "#fff",
    color: role === "user" ? "#fff" : "#1a1a2e",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
    fontSize: 14,
    lineHeight: 1.6,
  }),
  avatar: {
    width: 32,
    height: 32,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 16,
    margin: "0 8px",
    flexShrink: 0,
    alignSelf: "flex-end",
  },
  pages: {
    marginTop: 10,
    fontSize: 11,
    color: "#888",
    borderTop: "1px solid #eee",
    paddingTop: 8,
  },
  skeletonDot: {
    width: 8,
    height: 8,
    background: "#ccc",
    borderRadius: "50%",
    animation: "shimmer 1.5s infinite",
  },
  empty: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    padding: 40,
    opacity: 0.6,
    marginTop: 60,
  },
  emptyTitle: { fontSize: 20, fontWeight: 600, marginTop: 12, color: "#1a1a2e" },
  emptyHint: { fontSize: 14, color: "#555", marginTop: 8 },
  suggestions: {
    display: "flex",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 20,
    justifyContent: "center",
  },
  chip: {
    padding: "9px 16px",
    borderRadius: 20,
    border: "1.5px solid #667eea",
    background: "rgba(102,126,234,0.07)",
    color: "#4f46e5",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    transition: "all 0.18s ease",
    fontFamily: "inherit",
  },
  inputRow: {
    display: "flex",
    gap: 10,
    padding: "12px 16px",
    background: "#fff",
    borderTop: "1px solid #e5e7eb",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    resize: "none",
    padding: "10px 14px",
    borderRadius: 12,
    border: "1px solid #d1d5db",
    fontSize: 14,
    fontFamily: "inherit",
    outline: "none",
    lineHeight: 1.5,
    background: "#f9fafb",
  },
  sendBtn: {
    padding: "10px 22px",
    background: "linear-gradient(135deg, #667eea, #764ba2)",
    color: "#fff",
    border: "none",
    borderRadius: 12,
    fontWeight: 600,
    cursor: "pointer",
    fontSize: 14,
    height: 44,
    opacity: 1,
  },
  error: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#dc2626",
    padding: "10px 14px",
    borderRadius: 10,
    fontSize: 13,
    marginBottom: 12,
  },
};
