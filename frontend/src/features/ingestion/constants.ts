import type { WizardStageConfig } from './types';

export const wizardStages: WizardStageConfig[] = [
  { id: 'choose', label: 'Choose source', detail: 'Pick a CSV and name the dataset.' },
  { id: 'preview', label: 'Preview schema', detail: 'Check headers and sample rows before upload.' },
  { id: 'upload', label: 'Upload and profile', detail: 'Persist the file and generate quality metrics.' },
  { id: 'query', label: 'Run analysis', detail: 'Use the suggested SQL against the virtual table.' },
  { id: 'dashboard', label: 'Prepare delivery', detail: 'Turn the query result into a dashboard draft.' },
];
