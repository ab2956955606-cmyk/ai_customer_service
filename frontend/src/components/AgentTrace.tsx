import { CheckCircle2, CircleDashed, Wrench } from 'lucide-react';
import { AgentEvent } from '../api/client';

type Props = {
  events: AgentEvent[];
};

function AgentTrace({ events }: Props) {
  return (
    <section className="panel p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-ink">Agent Trace</h2>
        <span className="text-xs text-slate-500">{events.length} steps</span>
      </div>
      <div className="space-y-4">
        {events.map((event) => (
          <div key={event.id} className="grid grid-cols-[28px_1fr] gap-3">
            <div className="flex flex-col items-center">
              {event.status === 'completed' ? (
                <CheckCircle2 className="h-5 w-5 text-ocean" aria-hidden="true" />
              ) : (
                <CircleDashed className="h-5 w-5 text-rosewood" aria-hidden="true" />
              )}
              <div className="mt-2 h-full w-px bg-slate-200" />
            </div>
            <div className="pb-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-ink">{event.step_index}. {event.node_name}</p>
                <span className="badge border-slate-200 bg-slate-50 text-slate-600">{event.latency_ms} ms</span>
                {event.tool_name && (
                  <span className="badge border-teal-200 bg-teal-50 text-ocean">
                    <Wrench className="h-3 w-3" aria-hidden="true" />
                    {event.tool_name}
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm text-slate-600">{event.output_summary}</p>
              {event.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {event.citations.map((citation) => (
                    <span key={`${event.id}-${citation.title}`} className="badge border-amber-200 bg-amber-50 text-ember">
                      {citation.title} {citation.score.toFixed(2)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {events.length === 0 && <p className="text-sm text-slate-500">No trace events loaded.</p>}
      </div>
    </section>
  );
}

export default AgentTrace;
