"use client";

import { useRef, useState } from "react";
import { marked } from "marked";

const QUICK_PROMPTS = [
  {
    label: "Japan Trip",
    text: "Plan a complete 7 days Japan trip from Bangladesh including flights, hotels and sightseeing under 2 lakhs.",
  },
  {
    label: "Dubai Trip",
    text: "Plan a 5 days Dubai trip from Dhaka with flights, hotels and sightseeing.",
  },
  {
    label: "Thailand Trip",
    text: "Plan a 7 days Thailand trip from Bangladesh with budget hotels and sightseeing.",
  },
  {
    label: "Global Flights",
    text: "Give me all country flight info.",
  },
];

// Point this at your FastAPI/LangGraph backend.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/travel";

export default function Home() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [resultHtml, setResultHtml] = useState("");
  const [rawResult, setRawResult] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [error, setError] = useState("");
  const [showResult, setShowResult] = useState(false);
  const pdfRef = useRef(null);

  function setPrompt(text) {
    setInput(text);
  }

  async function sendMessage() {
    const message = input.trim();
    if (!message || loading) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, thread_id: threadId }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || "The travel API returned an error.");
      }

      const reply = data.answer ?? data.reply ?? data.result ?? data.message ?? "";

      setRawResult(reply);
      setResultHtml(marked.parse(reply));
      setThreadId(data.thread_id ?? threadId);
      setShowResult(true);
    } catch (err) {
      setError(
        `Something went wrong while generating your plan: ${err.message}. Please check the API connection and try again.`
      );
    } finally {
      setLoading(false);
    }
  }

  async function copyResult() {
    if (!rawResult) return;
    try {
      await navigator.clipboard.writeText(rawResult);
    } catch {
      setError("Couldn't copy the result to your clipboard.");
    }
  }

  async function downloadPDF() {
    if (!pdfRef.current) return;
    const html2pdf = (await import("html2pdf.js")).default;
    html2pdf()
      .set({
        margin: 10,
        filename: "tripmate-ai-travel-plan.pdf",
        html2canvas: { scale: 2 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      })
      .from(pdfRef.current)
      .save();
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      sendMessage();
    }
  }

  return (
    <>
      <div className="page-bg">
        <div className="gradient-circle circle-1"></div>
        <div className="gradient-circle circle-2"></div>
        <div className="gradient-circle circle-3"></div>
      </div>

      <main className="app-container">
        <section className="hero-section">
          <div className="badge">
            ✈️ TripMate AI — A Multi-Agent Travel Planner with LangGraph
          </div>

          <h1>Plan Your Perfect Trip with AI</h1>

          <p>
            Search flights, discover hotels, and generate a complete travel
            itinerary using a multi-agent LangGraph system.
          </p>
        </section>

        <section className="planner-card">
          <div className="card-header">
            <div>
              <h2>Where do you want to go?</h2>
              <p>
                Example: Plan a complete 7 days Japan trip from Bangladesh
                under 2 lakhs.
              </p>
            </div>

            <div className="status-pill">
              <span className="status-dot"></span>
              Online
            </div>
          </div>

          <div className="input-area">
            <textarea
              id="userInput"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs..."
            />

            <button id="sendBtn" onClick={sendMessage} disabled={loading}>
              {!loading ? (
                <span id="btnText">Generate Plan</span>
              ) : (
                <span id="btnLoader" className="loader"></span>
              )}
            </button>
          </div>

          <div className="quick-prompts">
            {QUICK_PROMPTS.map((qp) => (
              <button key={qp.label} onClick={() => setPrompt(qp.text)}>
                {qp.label}
              </button>
            ))}
          </div>
        </section>

        {showResult && (
          <section id="resultSection" className="result-section">
            <div className="result-header">
              <div>
                <h2>Your AI Travel Plan</h2>
                <p id="threadInfo">Thread ID: {threadId ?? "-"}</p>
              </div>

              <div className="result-actions">
                <button className="copy-btn" onClick={copyResult}>
                  Copy
                </button>

                <button className="download-btn" onClick={downloadPDF}>
                  Download PDF
                </button>
              </div>
            </div>

            <div id="pdfContent" className="pdf-content" ref={pdfRef}>
              <h1 className="pdf-title">AI Travel Plan</h1>
              <div
                id="resultBox"
                className="result-box"
                dangerouslySetInnerHTML={{ __html: resultHtml }}
              />
            </div>
          </section>
        )}

        {error && (
          <section id="errorBox" className="error-box">
            {error}
          </section>
        )}
      </main>

      <footer>
        Built with FastAPI, LangGraph, Groq, PostgreSQL, Tavily and
        AviationStack
      </footer>
    </>
  );
}
