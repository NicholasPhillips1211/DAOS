import type { Dispatch, SetStateAction } from 'react';

export type WorkspaceWorkflowContext = {
  apiBase: string;
  commentEmail: string;
  setError: Dispatch<SetStateAction<string | null>>;
  setStatus: Dispatch<SetStateAction<string>>;
  workspaceIdNumber: number;
};
