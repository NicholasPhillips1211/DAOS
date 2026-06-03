import type { ReactNode } from 'react';
import { cardClass, inputClass, Tooltip } from '../../../components/ui';
import type { WorkspaceWorkflow } from '../hooks/useWorkspaceWorkflow';

type CollaborationPanelProps = {
  workflow: WorkspaceWorkflow;
};

export function CollaborationPanel({ workflow }: CollaborationPanelProps) {
  const {
    commentEmail,
    commentLoading,
    commentMessage,
    comments,
    createShare,
    postComment,
    setCommentEmail,
    setCommentMessage,
    setShareEmail,
    setSharePermission,
    shareEmail,
    shareLoading,
    sharePermission,
    shares,
  } = workflow;

  return (
    <section className={cardClass}>
      <p className="text-xs uppercase tracking-[0.35em] text-emerald-200/90">Collaboration</p>
      <h3 className="mt-2 text-xl font-semibold text-white">Comments and sharing</h3>
      <div className="mt-4 grid gap-4">
        <form className="space-y-3" onSubmit={postComment}>
          <input
            value={commentEmail}
            onChange={(event) => setCommentEmail(event.target.value)}
            className={inputClass}
            placeholder="User email"
          />
          <textarea
            value={commentMessage}
            onChange={(event) => setCommentMessage(event.target.value)}
            className={`${inputClass} min-h-24 resize-y`}
            placeholder="Comment message"
          />
          <Tooltip content="Add a comment to foster team collaboration on dashboards">
            <button
              type="submit"
              disabled={commentLoading}
              className="rounded-full bg-emerald-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {commentLoading ? 'Posting...' : 'Post comment'}
            </button>
          </Tooltip>
        </form>

        <form className="space-y-3" onSubmit={createShare}>
          <input
            value={shareEmail}
            onChange={(event) => setShareEmail(event.target.value)}
            className={inputClass}
            placeholder="Target email"
          />
          <select
            value={sharePermission}
            onChange={(event) => setSharePermission(event.target.value)}
            className={inputClass}
          >
            <option value="view">view</option>
            <option value="edit">edit</option>
          </select>
          <Tooltip content="Share this dashboard with a team member">
            <button
              type="submit"
              disabled={shareLoading}
              className="rounded-full bg-amber-300 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {shareLoading ? 'Sharing...' : 'Share dashboard'}
            </button>
          </Tooltip>
        </form>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <RecentList title="Recent Comments" emptyLabel="No comments yet." hasItems={comments.length > 0}>
          {comments.map((item) => (
            <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
              <p className="font-medium text-white">{item.user_email}</p>
              <p className="mt-1 text-slate-400">{item.message}</p>
            </li>
          ))}
        </RecentList>
        <RecentList title="Recent Shares" emptyLabel="No shares yet." hasItems={shares.length > 0}>
          {shares.map((item) => (
            <li key={item.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
              <p className="font-medium text-white">{item.target_email}</p>
              <p className="mt-1 text-slate-400">Permission: {item.permission}</p>
            </li>
          ))}
        </RecentList>
      </div>
    </section>
  );
}

function RecentList({
  children,
  emptyLabel,
  hasItems,
  title,
}: {
  children: ReactNode;
  emptyLabel: string;
  hasItems: boolean;
  title: string;
}) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.25em] text-slate-400">{title}</p>
      <ul className="mt-3 space-y-2 text-sm text-slate-200">
        {!hasItems ? <li className="text-slate-400">{emptyLabel}</li> : null}
        {children}
      </ul>
    </div>
  );
}
