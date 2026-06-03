import { FormEvent, useState } from 'react';
import { createCommentRecord, createShareRecord } from '../api';
import type { CommentRecord, DashboardRecord, ShareRecord } from '../../../types/domain';
import type { WorkspaceWorkflowContext } from './workflowTypes';

type CollaborationWorkflowContext = WorkspaceWorkflowContext & {
  dashboards: DashboardRecord[];
};

export function useCollaborationWorkflow({
  apiBase,
  commentEmail,
  dashboards,
  setError,
  setStatus,
  workspaceIdNumber,
}: CollaborationWorkflowContext) {
  const [commentMessage, setCommentMessage] = useState('Revenue panel should include a MoM trend.');
  const [comments, setComments] = useState<CommentRecord[]>([]);
  const [shareEmail, setShareEmail] = useState('stakeholder@daos.local');
  const [sharePermission, setSharePermission] = useState('view');
  const [shares, setShares] = useState<ShareRecord[]>([]);
  const [commentLoading, setCommentLoading] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);

  async function postComment(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!validateWorkspaceId()) {
      return;
    }

    setError(null);
    setCommentLoading(true);
    try {
      const record = await createCommentRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        resource_type: 'dashboard',
        resource_id: dashboards[0]?.id ?? 1,
        user_email: commentEmail,
        message: commentMessage,
      });
      setComments((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Comment added by ${record.user_email}`);
      setCommentMessage('');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to post comment');
    } finally {
      setCommentLoading(false);
    }
  }

  async function createShare(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!validateWorkspaceId()) {
      return;
    }

    setError(null);
    setShareLoading(true);
    try {
      const record = await createShareRecord(apiBase, commentEmail, {
        workspace_id: workspaceIdNumber,
        resource_type: 'dashboard',
        resource_id: dashboards[0]?.id ?? 1,
        target_email: shareEmail,
        permission: sharePermission,
      });
      setShares((previous) => [record, ...previous].slice(0, 6));
      setStatus(`Shared dashboard with ${record.target_email}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Failed to create share');
    } finally {
      setShareLoading(false);
    }
  }

  function validateWorkspaceId(): boolean {
    if (Number.isFinite(workspaceIdNumber)) {
      return true;
    }
    setError('Workspace ID must be a number.');
    return false;
  }

  return {
    commentLoading,
    commentMessage,
    comments,
    createShare,
    postComment,
    setCommentMessage,
    setShareEmail,
    setSharePermission,
    shareEmail,
    shareLoading,
    sharePermission,
    shares,
  };
}
