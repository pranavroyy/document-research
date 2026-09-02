import { useEffect, useState } from "react";
import { api } from "./api/client";

type DocumentItem = {
  id: number;
  filename: string;
  title: string | null;
  authors: string[] | string | null;
  abstract: string | null;
  page_count: number | null;
  created_at: string;
};

type Source = {
  source_number: number;
  chunk_id: number | null;
  document_id: number;
  filename: string | null;
  page_number: number | null;
  chunk_index: number | null;
  content_preview: string;
};

type Intent = {
  route: string;
  entity?: string | null;
  operation?: string | null;
  confidence: number;
};

type Retrieval = {
  mode: string;
  reranking: boolean;
  top_k: number;
};

function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [intent, setIntent] = useState<Intent | null>(null);
  const [retrieval, setRetrieval] = useState<Retrieval | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchDocuments = async () => {
    const res = await api.get("/documents");
    setDocuments(res.data);
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const toggleDocument = (id: number) => {
    setSelectedDocumentIds((prev) =>
      prev.includes(id) ? prev.filter((docId) => docId !== id) : [...prev, id]
    );
  };

  const formatAuthors = (authors: DocumentItem["authors"]) => {
    if (!authors) return "Authors not detected";

    if (Array.isArray(authors)) {
      return authors.length > 0 ? authors.join(", ") : "Authors not detected";
    }

    return authors;
  };

  const uploadDocument = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      await api.post("/documents/upload", formData);
      setFile(null);
      await fetchDocuments();
    } catch (error) {
      console.error(error);
      alert("Upload failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const askQuestionStreaming = async () => {
    if (!question.trim()) return;

    try {
      setLoading(true);
      setAnswer("");
      setSources([]);
      setIntent(null);
      setRetrieval(null);

      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          top_k: 5,
          document_ids:
            selectedDocumentIds.length > 0 ? selectedDocumentIds : null,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Streaming request failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const rawEvent of events) {
          const lines = rawEvent.split("\n");

          const eventLine = lines.find((line) => line.startsWith("event: "));
          const dataLine = lines.find((line) => line.startsWith("data: "));

          if (!eventLine || !dataLine) continue;

          const event = eventLine.replace("event: ", "").trim();
          const data = JSON.parse(dataLine.replace("data: ", ""));

          if (event === "intent") {
            setIntent(data);
          }

          if (event === "retrieval") {
            setRetrieval(data);
          }

          if (event === "token") {
            setAnswer((prev) => prev + data);
          }

          if (event === "sources") {
            setSources(data);
          }

          if (event === "done") {
            setLoading(false);
          }
        }
      }
    } catch (error) {
      console.error(error);
      alert("Question failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              AI Research Assistant
            </h1>
            <p className="text-sm text-slate-400">
              Query research papers using metadata extraction, intent routing,
              semantic search, and local LLMs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-300">
              Ollama
            </span>
            <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-sm text-indigo-300">
              pgvector
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
        <aside className="space-y-6">
          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-xl">
            <h2 className="mb-2 text-lg font-semibold">Upload Document</h2>
            <p className="mb-4 text-sm text-slate-400">
              Upload a PDF to parse, extract metadata, chunk, embed, and index.
            </p>

            <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950 p-6 text-center hover:border-slate-500">
              <span className="text-sm text-slate-300">
                {file ? file.name : "Choose a PDF file"}
              </span>
              <span className="mt-2 text-xs text-slate-500">
                PDF files only
              </span>
              <input
                className="hidden"
                type="file"
                accept="application/pdf"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>

            <button
              onClick={uploadDocument}
              disabled={!file || loading}
              className="mt-4 w-full rounded-xl bg-indigo-500 px-4 py-2 font-medium text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            >
              {loading ? "Processing..." : "Upload & Index"}
            </button>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Indexed Documents</h2>
              <span className="text-xs text-slate-500">
                {selectedDocumentIds.length > 0
                  ? `${selectedDocumentIds.length} selected`
                  : "All searchable"}
              </span>
            </div>

            <p className="mb-3 text-xs text-slate-500">
              Select documents to restrict the assistant. If none selected, all
              documents are searched.
            </p>

            {documents.length === 0 ? (
              <p className="text-sm text-slate-400">
                No documents uploaded yet.
              </p>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => {
                  const selected = selectedDocumentIds.includes(doc.id);

                  return (
                    <button
                      key={doc.id}
                      onClick={() => toggleDocument(doc.id)}
                      className={`w-full rounded-xl border p-3 text-left transition ${
                        selected
                          ? "border-indigo-500 bg-indigo-500/10"
                          : "border-slate-800 bg-slate-950 hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-slate-100">
                            {doc.title || doc.filename}
                          </p>

                          <p className="mt-1 truncate text-xs text-slate-400">
                            {formatAuthors(doc.authors)}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {doc.page_count
                              ? `${doc.page_count} pages`
                              : `Document #${doc.id}`}
                          </p>
                        </div>

                        <span
                          className={`mt-0.5 rounded-full px-2 py-0.5 text-xs ${
                            selected
                              ? "bg-indigo-500 text-white"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {selected ? "Selected" : "Select"}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        </aside>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Ask a Question</h2>
            <p className="text-sm text-slate-400">
              The assistant streams answers live and shows sources after
              completion.
            </p>
          </div>

          <textarea
            rows={5}
            className="w-full resize-none rounded-xl border border-slate-700 bg-slate-950 p-4 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-indigo-500"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Try: summarize this paper, who are the authors, compare their methods, what accuracy did DBSCAN achieve?"
          />

          <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
            <button
              onClick={askQuestionStreaming}
              disabled={loading || !question.trim()}
              className="rounded-xl bg-indigo-500 px-5 py-2 font-medium text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
            >
              {loading ? "Thinking..." : "Ask Assistant"}
            </button>

            <p className="text-xs text-slate-500">
              {selectedDocumentIds.length > 0
                ? `${selectedDocumentIds.length} selected document(s)`
                : "Searching all documents"}
            </p>
          </div>

          {answer && (
            <div className="mt-8 space-y-6">
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
                <div className="mb-4 flex flex-wrap gap-2">
                  {intent && (
                    <div className="inline-flex rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
                      Route: {intent.route}
                      {intent.entity ? ` · ${intent.entity}` : ""}
                      {intent.operation ? ` · ${intent.operation}` : ""}
                      {typeof intent.confidence === "number"
                        ? ` · ${(intent.confidence * 100).toFixed(0)}%`
                        : ""}
                    </div>
                  )}

                  {retrieval && (
                    <div className="inline-flex rounded-full border border-emerald-700 bg-emerald-950 px-3 py-1 text-xs text-emerald-300">
                      Retrieval: {retrieval.mode}
                      {retrieval.reranking ? " + Reranker" : ""}
                      {" · "}
                      Top {retrieval.top_k}
                    </div>
                  )}
                </div>

                <h3 className="mb-3 text-lg font-semibold">Answer</h3>
                <p className="whitespace-pre-wrap leading-7 text-slate-200">
                  {answer}
                  {loading && (
                    <span className="ml-1 inline-block animate-pulse text-indigo-300">
                      ▍
                    </span>
                  )}
                </p>
              </div>

              {sources.length > 0 && (
                <div>
                  <h3 className="mb-3 text-lg font-semibold">Sources</h3>
                  <div className="space-y-3">
                    {sources.map((source) => (
                      <div
                        key={`${source.document_id}-${
                          source.chunk_id ?? source.source_number
                        }`}
                        className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                      >
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-300">
                            Source {source.source_number}
                          </span>
                          <span className="text-xs text-slate-500">
                            {source.filename ??
                              `Document ${source.document_id}`}{" "}
                            ·{" "}
                            {source.page_number
                              ? `Page ${source.page_number}`
                              : "Page unknown"}{" "}
                            ·{" "}
                            {source.chunk_index !== null
                              ? `Chunk ${source.chunk_index}`
                              : "Metadata"}
                          </span>
                        </div>

                        <p className="text-sm leading-6 text-slate-300">
                          {source.content_preview}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;