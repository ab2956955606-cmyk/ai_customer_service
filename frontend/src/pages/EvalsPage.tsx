import { useEffect, useState } from 'react';
import { Play, RefreshCcw } from 'lucide-react';
import { api, EvalLocale, EvalPayload } from '../api/client';
import EvalResults from '../components/EvalResults';
import { useI18n } from '../i18n';

type Props = {
  onChanged: () => void;
  deepSeekApiKey: string | null;
};

function EvalsPage({ onChanged, deepSeekApiKey }: Props) {
  const { t, locale } = useI18n();
  const [evalLocale, setEvalLocale] = useState<EvalLocale>(locale);
  const [payload, setPayload] = useState<EvalPayload | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setPayload(await api.latestEvals(evalLocale));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t('evals.loadFailed'));
    }
  }

  useEffect(() => {
    void load();
  }, [evalLocale]);

  async function run() {
    setRunning(true);
    setError(null);
    try {
      const response = await api.runEvals(evalLocale, deepSeekApiKey);
      setPayload(response);
      onChanged();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t('evals.runFailed'));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div
          className="inline-flex h-10 items-center border border-slate-200 bg-slate-50 p-1"
          style={{ borderRadius: 8 }}
          role="group"
          aria-label={t('evals.datasetLanguage')}
        >
          {(['zh', 'en'] as EvalLocale[]).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setEvalLocale(option)}
              disabled={running}
              className={`h-8 min-w-20 px-3 text-xs font-medium transition ${
                evalLocale === option ? 'bg-white text-ocean shadow-sm' : 'text-slate-500 hover:text-slate-900'
              }`}
              style={{ borderRadius: 6 }}
              aria-pressed={evalLocale === option}
            >
              {option === 'zh' ? t('evals.languageZh') : t('evals.languageEn')}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap justify-end gap-2">
        <button type="button" className="btn" onClick={load} title={t('evals.refresh')}>
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          {t('common.refresh')}
        </button>
        <button type="button" className="btn btn-primary" onClick={run} disabled={running} title={t('evals.run')}>
          <Play className="h-4 w-4" aria-hidden="true" />
          {running ? t('evals.running') : t('evals.run')}
        </button>
        </div>
      </div>
      {error && <div className="panel border-rose-200 bg-rose-50 p-3 text-sm text-rosewood">{error}</div>}
      <EvalResults payload={payload} />
    </div>
  );
}

export default EvalsPage;
