import React, { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const API_BASE = window.location.hostname === "localhost" && window.location.port === "3001"
    ? "http://localhost:8001/api/v1"   // Local development
    : "/api/v1";                        // Docker (proxied through nginx)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- File Upload ---
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadStatus({ type: "error", message: "Only PDF files are supported" });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const data = await response.json();
      setUploadStatus({
        type: "success",
        message: `✅ "${data.filename}" uploaded — ${data.chunk_count} chunks indexed`,
      });
    } catch (err) {
      setUploadStatus({ type: "error", message: `❌ ${err.message}` });
    } finally {
      setIsUploading(false);
      fileInputRef.current.value = "";
    }
  };

  // --- Ask Question (Streaming) ---
  const handleSend = async () => {
    const question = input.trim();
    if (!question || isLoading) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsLoading(true);

    // Add empty assistant message that we'll stream into
    setMessages((prev) => [...prev, { role: "assistant", text: "", sources: [] }]);

    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, collection: "default", top_k: 8 }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Query failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep incomplete line in buffer

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7);
          } else if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (eventType === "sources") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1].sources = data.sources || [];
                return updated;
              });
            } else if (eventType === "token") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1].text += data.token;
                return updated;
              });
            }
          }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].text = `❌ Error: ${err.message}`;
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>📄 DocQA</h1>
        <p>Upload documents and ask questions — powered by local AI</p>
      </header>

      {/* Upload Bar */}
      <div className="upload-bar">
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          ref={fileInputRef}
          id="file-upload"
          hidden
        />
        <label htmlFor="file-upload" className="upload-button">
          {isUploading ? "⏳ Processing..." : "📎 Upload PDF"}
        </label>
        {uploadStatus && (
          <span className={`upload-status ${uploadStatus.type}`}>
            {uploadStatus.message}
          </span>
        )}
      </div>

      {/* Chat Messages */}
      <div className="chat-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>👋 Upload a PDF and start asking questions!</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-bubble">
              <p>{msg.text || (isLoading && i === messages.length - 1 ? "⏳ Thinking..." : "")}</p>

              {/* Show sources for assistant messages */}
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <details>
                    <summary>📚 Sources ({msg.sources.length} chunks)</summary>
                    {msg.sources.map((src, j) => (
                      <div key={j} className="source-chunk">
                        <span className="score">Score: {src.score}</span>
                        <span className="filename">{src.metadata?.filename}</span>
                        <p>{src.text}</p>
                      </div>
                    ))}
                  </details>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="input-bar">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          rows={1}
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default App;