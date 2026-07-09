import { useEffect, useState } from 'react';
import { RefreshCcw } from 'lucide-react';
import { api, PendingAction } from '../api/client';
import ApprovalCard from '../components/ApprovalCard';

type Props = {
  onChanged: () => void;
};

function ApprovalsPage({ onChanged }: Props) {
  const [actions, setActions] = useState<PendingAction[]>([]);
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    api.approvals().then(setActions);
  }

  useEffect(() => {
    load();
  }, []);

  async function decide(id: number, decision: 'approve' | 'reject') {
    setBusyId(id);
    try {
      if (decision === 'approve') {
        await api.approve(id);
      } else {
        await api.reject(id);
      }
      load();
      onChanged();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex justify-end">
        <button type="button" className="btn" onClick={load} title="Refresh approvals">
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
      </div>
      <div className="grid gap-3">
        {actions.map((action) => (
          <ApprovalCard
            key={action.id}
            action={action}
            busy={busyId === action.id}
            onApprove={(actionId) => decide(actionId, 'approve')}
            onReject={(actionId) => decide(actionId, 'reject')}
          />
        ))}
        {actions.length === 0 && (
          <section className="panel p-4">
            <p className="text-sm text-slate-500">No approval records yet.</p>
          </section>
        )}
      </div>
    </div>
  );
}

export default ApprovalsPage;
