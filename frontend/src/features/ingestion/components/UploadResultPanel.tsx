import { WorkflowState } from '../../../components/ui';
import { wizardStages } from '../constants';
import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type UploadResultPanelProps = {
  wizard: IngestionWizardViewModel;
};

export function UploadResultPanel({ wizard }: UploadResultPanelProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm uppercase tracking-[0.25em] text-slate-300">Upload result</h3>
        <span className="rounded-full border border-white/10 bg-slate-950/60 px-3 py-1 text-xs text-slate-300">
          {wizard.uploadResult ? 'Ready for analysis' : 'Waiting for upload'}
        </span>
      </div>
      {wizard.uploadResult ? (
        <div className="mt-4 space-y-3 text-sm text-slate-200">
          <div className="rounded-xl border border-emerald-300/20 bg-emerald-400/10 p-3">
            <p className="font-medium text-emerald-100">{wizard.uploadResult.dataset_name} uploaded successfully</p>
            <p className="mt-1 text-emerald-50/80">
              Quality score: {wizard.uploadResult.quality_score}% - {wizard.uploadResult.row_count} rows -{' '}
              {wizard.uploadResult.rejected_rows} rejected
            </p>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-emerald-50/70">
              Job #{wizard.uploadResult.job_id} - {wizard.uploadResult.status}
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-slate-950/60 p-3 text-slate-300">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Next move</p>
            <p className="mt-2 leading-6">
              Use the query template above, then create a dashboard from the uploaded dataset or feed it into the
              automation planner.
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <WorkflowState
            variant="info"
            title="Waiting for an upload"
            description="Upload a CSV to see row counts, quality score, and storage details here."
            action={
              <p className="text-xs uppercase tracking-[0.2em] text-amber-50/80">
                Current stage: {wizardStages[wizard.currentStageIndex]?.label}
              </p>
            }
          />
        </div>
      )}
    </div>
  );
}
