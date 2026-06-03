import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type IngestionWizardHeaderProps = {
  wizard: IngestionWizardViewModel;
};

export function IngestionWizardHeader({ wizard }: IngestionWizardHeaderProps) {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/90">Ingestion Wizard</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">Upload a CSV and preview the path to insight</h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-300">
          Step through upload, schema preview, and a suggested SQL query before you hand the dataset off to dashboards
          or automation.
        </p>
      </div>
      <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
        {getSummaryLabel(wizard)}
      </div>
    </div>
  );
}

function getSummaryLabel(wizard: IngestionWizardViewModel): string {
  if (wizard.loadingWorkspaceSummary) {
    return 'Loading workspace summary...';
  }
  if (wizard.workspaceSummary) {
    const count = wizard.workspaceSummary.dataset_count;
    return `${count} dataset${count === 1 ? '' : 's'} in workspace`;
  }
  if (wizard.loadingDatasets) {
    return 'Loading recent datasets...';
  }
  return `${wizard.datasets.length} recent dataset${wizard.datasets.length === 1 ? '' : 's'}`;
}
