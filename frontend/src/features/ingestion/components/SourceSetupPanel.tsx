import { inputClass } from '../../../components/ui';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type SourceSetupPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function SourceSetupPanel({ wizard }: SourceSetupPanelProps) {
  const steps = [
    {
      step: '1',
      title: 'Choose source',
      body: wizard.selectedFile ? wizard.selectedFile.name : 'CSV upload is the current MVP path.',
    },
    {
      step: '2',
      title: 'Preview schema',
      body: wizard.preview.headers.length > 0 ? `${wizard.preview.headers.length} columns detected.` : 'No preview yet.',
    },
    {
      step: '3',
      title: 'Clean and profile',
      body: 'The backend preserves the raw file, writes a cleaned artifact, and returns quality metrics.',
    },
  ];

  return (
    <>
      <div className="grid gap-4 md:grid-cols-[1fr_1.2fr]">
        <label className="space-y-2">
          <span className="text-xs uppercase tracking-[0.25em] text-slate-400">Dataset name</span>
          <input
            value={wizard.datasetName}
            onChange={(event) => wizard.setDatasetName(event.target.value)}
            className={inputClass}
            placeholder="Quarterly Sales Upload"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs uppercase tracking-[0.25em] text-slate-400">CSV file</span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={wizard.handleFileChange}
            className="block w-full cursor-pointer rounded-2xl border border-dashed border-white/15 bg-white/5 px-4 py-3 text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-cyan-400 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950 hover:border-cyan-300/40"
          />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {steps.map((item) => (
          <div key={item.step} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-400 text-sm font-bold text-slate-950">
                {item.step}
              </div>
              <h3 className="text-sm font-semibold text-white">{item.title}</h3>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{item.body}</p>
          </div>
        ))}
      </div>
    </>
  );
}
