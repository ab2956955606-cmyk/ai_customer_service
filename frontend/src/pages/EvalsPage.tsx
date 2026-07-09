import { useEffect, useState } from 'react';
import { Play, RefreshCcw } from 'lucide-react';
import { api, EvalPayload } from '../api/client';
import EvalResults from '../components/EvalResults';

type Props = {
  onChanged: () => void;
};

function EvalsPage({ onChanged }: Props) {
  const [payload, setPayload] = useState<EvalPayload | null>(null);
  const [running, setRunning] = useState(false);

  function load() {
    api.latestEvals().then(setPayload);
  }

  useEffect(() => {
    load();
  }, []);

  async function run() {
    setRunning(true);
    try {
      const response = await api.runEvals();
      setPayload(response);
      onChanged();
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap justify-end gap-2">
        <button type="button" className="btn" onClick={load} title="Refresh latest eval">
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
        <button type="button" className="btn btn-primary" onClick={run} disabled={running} title="Run eval">
          <Play className="h-4 w-4" aria-hidden="true" />
          {running ? 'Running' : 'Run eval'}
        </button>
      </div>
      <EvalResults payload={payload} />
    </div>
  );
}

export default EvalsPage;
