import type { IngestionWizardViewModel } from '../hooks/useIngestionWizard';

type UploadControlsProps = {
  wizard: IngestionWizardViewModel;
};

export function UploadControls({ wizard }: UploadControlsProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <button
        type="submit"
        disabled={!wizard.canUpload || wizard.uploading}
        className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {wizard.uploading ? 'Uploading for cleaning...' : 'Upload and clean dataset'}
      </button>
      <span className="self-center text-sm text-slate-400">
        Uploads are stored raw, cleaned, and profiled automatically by the backend.
      </span>
    </div>
  );
}
