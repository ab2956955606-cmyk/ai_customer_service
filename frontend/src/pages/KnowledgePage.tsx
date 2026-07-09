import { FormEvent, useEffect, useState } from 'react';
import { RefreshCcw, Search } from 'lucide-react';
import { api, Citation, KnowledgeDocument } from '../api/client';
import RagAnswerPanel from '../components/RagAnswerPanel';

function KnowledgePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [question, setQuestion] = useState('How can I cancel my subscription?');
  const [answer, setAnswer] = useState('');
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);

  function load() {
    api.documents().then(setDocuments);
  }

  useEffect(() => {
    load();
  }, []);

  async function ask(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const payload = await api.askRag(question);
      setAnswer(payload.answer);
      setCitations(payload.citations);
    } finally {
      setLoading(false);
    }
  }

  async function reindex() {
    const payload = await api.reindex();
    setDocuments(payload.documents);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
      <section className="panel p-4">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-ink">Knowledge Documents</h2>
          <button type="button" className="btn" onClick={reindex} title="Reindex">
            <RefreshCcw className="h-4 w-4" aria-hidden="true" />
            Reindex
          </button>
        </div>
        <div className="grid gap-3">
          {documents.map((doc) => (
            <article key={doc.id} className="border border-slate-200 p-3" style={{ borderRadius: 8 }}>
              <p className="text-sm font-medium text-ink">{doc.title}</p>
              <p className="mt-1 text-xs text-slate-500">{doc.source}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="grid content-start gap-4">
        <form className="panel p-4" onSubmit={ask}>
          <label className="grid gap-1 text-sm font-medium text-slate-700">
            Question
            <textarea className="input min-h-28 resize-y" value={question} onChange={(event) => setQuestion(event.target.value)} />
          </label>
          <button type="submit" className="btn btn-primary mt-3" disabled={loading}>
            <Search className="h-4 w-4" aria-hidden="true" />
            {loading ? 'Searching' : 'Ask RAG'}
          </button>
        </form>
        <RagAnswerPanel answer={answer} citations={citations} />
      </div>
    </div>
  );
}

export default KnowledgePage;
