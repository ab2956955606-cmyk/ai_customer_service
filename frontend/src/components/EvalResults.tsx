import { EvalPayload } from '../api/client';

type Props = {
  payload: EvalPayload | null;
};

const metricLabels: Record<string, string> = {
  routing_accuracy: 'Routing',
  escalation_accuracy: 'Escalation',
  unsafe_action_block_rate: 'Unsafe block',
  approval_gate_accuracy: 'Approval gate',
  citation_presence_rate: 'Citations',
  average_latency_ms: 'Avg latency'
};

function EvalResults({ payload }: Props) {
  const metrics = payload?.metrics ?? {};
  return (
    <div className="grid gap-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        {Object.entries(metrics).map(([key, value]) => (
          <section key={key} className="panel p-4">
            <p className="text-xs font-medium uppercase text-slate-500">{metricLabels[key] ?? key}</p>
            <p className="mt-2 text-2xl font-semibold text-ink">{key.includes('latency') ? `${value} ms` : value}</p>
          </section>
        ))}
      </div>

      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-ink">Eval Results</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Route</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(payload?.results ?? []).map((result) => (
                <tr key={result.id}>
                  <td className="px-4 py-3 font-medium text-ink">{result.id}</td>
                  <td className="px-4 py-3 text-slate-600">{result.actual_route}</td>
                  <td className="px-4 py-3 text-slate-600">{result.actual_category}</td>
                  <td className="px-4 py-3 text-slate-600">{result.actual_priority}</td>
                  <td className="px-4 py-3 text-slate-600">{result.latency_ms} ms</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${result.passed ? 'border-teal-200 bg-teal-50 text-ocean' : 'border-rose-200 bg-rose-50 text-rosewood'}`}>
                      {result.passed ? 'passed' : 'failed'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default EvalResults;
