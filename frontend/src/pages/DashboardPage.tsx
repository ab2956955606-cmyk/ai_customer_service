import { RefreshCcw } from 'lucide-react';
import { StatsOverview } from '../api/client';
import AgentTrace from '../components/AgentTrace';
import Charts from '../components/Charts';
import StatCards from '../components/StatCards';

type Props = {
  stats: StatsOverview | null;
  onRefresh: () => void;
};

function DashboardPage({ stats, onRefresh }: Props) {
  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <span className="badge border-teal-200 bg-teal-50 text-ocean">Escalation {(stats?.escalation_rate ?? 0) * 100}%</span>
          <span className="badge border-amber-200 bg-amber-50 text-ember">Approval {(stats?.approval_rate ?? 0) * 100}%</span>
        </div>
        <button type="button" className="btn" onClick={onRefresh} title="Refresh">
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
      </div>
      <StatCards stats={stats} />
      <Charts categories={stats?.category_breakdown ?? []} priorities={stats?.priority_breakdown ?? []} />
      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-ink">Recent Runs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Run</th>
                <th className="px-4 py-3">Ticket</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Steps</th>
                <th className="px-4 py-3">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(stats?.recent_runs ?? []).map((run) => (
                <tr key={run.id}>
                  <td className="px-4 py-3 font-medium text-ink">#{run.id}</td>
                  <td className="px-4 py-3 text-slate-600">#{run.ticket_id}</td>
                  <td className="px-4 py-3 text-slate-600">{run.status}</td>
                  <td className="px-4 py-3 text-slate-600">{run.agents_run.length}</td>
                  <td className="px-4 py-3 text-slate-600">{run.total_latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <AgentTrace events={stats?.latest_trace_preview ?? []} />
    </div>
  );
}

export default DashboardPage;
