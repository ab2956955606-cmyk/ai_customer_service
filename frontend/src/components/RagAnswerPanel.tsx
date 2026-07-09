import { Citation } from '../api/client';

type Props = {
  answer: string;
  citations: Citation[];
};

function RagAnswerPanel({ answer, citations }: Props) {
  return (
    <section className="panel p-4">
      <h2 className="text-sm font-semibold text-ink">Answer</h2>
      <p className="mt-3 text-sm leading-6 text-slate-700">{answer || 'No answer yet.'}</p>
      <div className="mt-4 grid gap-3">
        {citations.map((citation) => (
          <article key={citation.title} className="border border-slate-200 p-3" style={{ borderRadius: 8 }}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-ink">{citation.title}</p>
              <span className="badge border-teal-200 bg-teal-50 text-ocean">{citation.score.toFixed(2)}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{citation.snippet}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default RagAnswerPanel;
