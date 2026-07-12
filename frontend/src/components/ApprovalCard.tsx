import { Check, X } from 'lucide-react';
import { PendingAction } from '../api/client';
import { useI18n } from '../i18n';

type Props = {
  action: PendingAction;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  busy: boolean;
};

function ApprovalCard({ action, onApprove, onReject, busy }: Props) {
  const { t, label } = useI18n();
  return (
    <article className="panel p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-semibold text-ink">{label(action.action_type)}</h2>
            <span className="badge border-amber-200 bg-amber-50 text-ember">{t('common.risk')}: {label(action.risk_level)}</span>
            <span className="badge border-slate-200 bg-slate-50 text-slate-600">{label(action.status)}</span>
          </div>
          <p className="mt-2 text-sm text-slate-600">{action.ticket_subject ?? `${t('common.ticket')} ${action.ticket_id}`}</p>
        </div>
        {action.status === 'pending' && (
          <div className="flex gap-2">
            <button type="button" className="btn btn-primary" onClick={() => onApprove(action.id)} disabled={busy} title={t('approvals.approve')}>
              <Check className="h-4 w-4" aria-hidden="true" />
              {t('approvals.approve')}
            </button>
            <button type="button" className="btn btn-danger" onClick={() => onReject(action.id)} disabled={busy} title={t('approvals.reject')}>
              <X className="h-4 w-4" aria-hidden="true" />
              {t('approvals.reject')}
            </button>
          </div>
        )}
      </div>
      <pre className="mt-4 overflow-auto bg-slate-950 p-3 text-xs text-slate-100" style={{ borderRadius: 8 }}>
        {JSON.stringify(action.payload_json, null, 2)}
      </pre>
    </article>
  );
}

export default ApprovalCard;
