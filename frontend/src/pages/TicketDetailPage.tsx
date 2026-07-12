import { AgentEvent, Citation, PendingAction, Ticket, TicketDetail } from '../api/client';
import AgentTrace from '../components/AgentTrace';
import { useI18n } from '../i18n';

type Props = {
  detail: TicketDetail | null;
  fallback?: {
    ticket: Ticket;
    events: AgentEvent[];
    pending_actions: PendingAction[];
    citations: Citation[];
  } | null;
};

const tone: Record<string, string> = {
  resolved: 'border-teal-200 bg-teal-50 text-ocean',
  escalated: 'border-rose-200 bg-rose-50 text-rosewood',
  pending_approval: 'border-amber-200 bg-amber-50 text-ember'
};

function TicketDetailPage({ detail, fallback }: Props) {
  const { t, label } = useI18n();
  const ticket = detail?.ticket ?? fallback?.ticket ?? null;
  const events = detail?.events ?? fallback?.events ?? [];
  const actions = detail?.pending_actions ?? fallback?.pending_actions ?? [];
  const citations = fallback?.citations ?? events.flatMap((event) => event.citations ?? []);

  if (!ticket) {
    return (
      <section className="panel p-4">
        <p className="text-sm text-slate-500">{t('ticket.select')}</p>
      </section>
    );
  }

  return (
    <div className="grid gap-4">
      <section className="panel p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">{ticket.subject}</h2>
            <p className="mt-1 text-sm text-slate-500">{ticket.customer_email ?? t('common.unknownCustomer')}</p>
          </div>
          <span className={`badge ${tone[ticket.status] ?? 'border-slate-200 bg-slate-50 text-slate-600'}`}>{label(ticket.status)}</span>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-700">{ticket.description}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="badge border-slate-200 bg-slate-50 text-slate-600">{label(ticket.category)}</span>
          <span className="badge border-slate-200 bg-slate-50 text-slate-600">{label(ticket.priority ?? 'normal')}</span>
          <span className="badge border-slate-200 bg-slate-50 text-slate-600">{t('common.risk')}: {label(ticket.risk_level ?? 'low')}</span>
        </div>
      </section>

      <section className="panel p-4">
        <h2 className="text-sm font-semibold text-ink">{t('ticket.finalResponse')}</h2>
        <p className="mt-3 text-sm leading-6 text-slate-700">{ticket.final_response ?? t('ticket.noResponse')}</p>
        {citations.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {citations.map((citation, index) => (
              <span key={`${citation.title}-${index}`} className="badge border-amber-200 bg-amber-50 text-ember">
                {citation.title}
              </span>
            ))}
          </div>
        )}
      </section>

      {actions.length > 0 && (
        <section className="panel p-4">
          <h2 className="text-sm font-semibold text-ink">{t('ticket.pendingActions')}</h2>
          <div className="mt-3 grid gap-3">
            {actions.map((action) => (
              <div key={action.id} className="border border-slate-200 p-3" style={{ borderRadius: 8 }}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ink">{label(action.action_type)}</span>
                  <span className="badge border-amber-200 bg-amber-50 text-ember">{label(action.status)}</span>
                </div>
                <pre className="mt-2 overflow-auto text-xs text-slate-600">{JSON.stringify(action.payload_json, null, 2)}</pre>
              </div>
            ))}
          </div>
        </section>
      )}

      <AgentTrace events={events} />
    </div>
  );
}

export default TicketDetailPage;
