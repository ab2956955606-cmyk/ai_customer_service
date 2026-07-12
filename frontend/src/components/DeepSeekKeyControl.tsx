import { FormEvent, useEffect, useState } from 'react';
import { Eye, EyeOff, KeyRound, X } from 'lucide-react';
import { useI18n } from '../i18n';

type Props = {
  configured: boolean;
  onSave: (apiKey: string) => void;
  onClear: () => void;
};

function DeepSeekKeyControl({ configured, onSave, onClear }: Props) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!open) return undefined;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') closeDialog();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  function closeDialog() {
    setDraft('');
    setVisible(false);
    setOpen(false);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const apiKey = draft.trim();
    if (!apiKey) return;
    onSave(apiKey);
    closeDialog();
  }

  function clear() {
    onClear();
    closeDialog();
  }

  return (
    <>
      <button
        type="button"
        className={`btn h-9 ${configured ? 'border-teal-300 bg-teal-50 text-ocean' : ''}`}
        onClick={() => setOpen(true)}
        title={configured ? t('deepseek.enabled') : t('deepseek.disabled')}
        aria-label={configured ? t('deepseek.enabled') : t('deepseek.disabled')}
      >
        <KeyRound className="h-4 w-4" aria-hidden="true" />
        <span>{t('deepseek.button')}</span>
        <span className={`h-2 w-2 rounded-full ${configured ? 'bg-teal-600' : 'bg-slate-300'}`} aria-hidden="true" />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/40 p-4 sm:items-center"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeDialog();
          }}
        >
          <section
            className="panel w-full max-w-md p-5 shadow-xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="deepseek-key-title"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="deepseek-key-title" className="text-base font-semibold text-ink">{t('deepseek.title')}</h2>
                <p className="mt-1 text-sm leading-5 text-slate-500">{t('deepseek.description')}</p>
              </div>
              <button type="button" className="btn h-9 w-9 shrink-0 p-0" onClick={closeDialog} title={t('deepseek.cancel')}>
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>

            <form className="mt-5 grid gap-4" onSubmit={submit}>
              <label className="grid gap-1 text-sm font-medium text-slate-700">
                {t('deepseek.keyLabel')}
                <div className="relative">
                  <input
                    className="input pr-11"
                    type={visible ? 'text' : 'password'}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    placeholder={t('deepseek.placeholder')}
                    autoComplete="off"
                    autoFocus
                    spellCheck={false}
                    data-1p-ignore
                    data-lpignore="true"
                    maxLength={512}
                  />
                  <button
                    type="button"
                    className="absolute right-1 top-1 flex h-8 w-8 items-center justify-center text-slate-500 hover:text-slate-900"
                    onClick={() => setVisible((value) => !value)}
                    title={visible ? t('deepseek.hide') : t('deepseek.show')}
                    aria-label={visible ? t('deepseek.hide') : t('deepseek.show')}
                  >
                    {visible ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
                  </button>
                </div>
              </label>

              <div className="flex flex-wrap justify-end gap-2">
                {configured && (
                  <button type="button" className="btn btn-danger" onClick={clear}>{t('deepseek.clear')}</button>
                )}
                <button type="button" className="btn" onClick={closeDialog}>{t('deepseek.cancel')}</button>
                <button type="submit" className="btn btn-primary" disabled={!draft.trim()}>{t('deepseek.save')}</button>
              </div>
            </form>
          </section>
        </div>
      )}
    </>
  );
}

export default DeepSeekKeyControl;
