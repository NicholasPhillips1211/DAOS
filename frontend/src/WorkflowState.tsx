import type { ReactNode } from 'react';

type WorkflowStateVariant = 'loading' | 'empty' | 'error' | 'success' | 'info';

type WorkflowStateProps = {
  variant: WorkflowStateVariant;
  title: string;
  description: string;
  action?: ReactNode;
};

const variantClasses: Record<WorkflowStateVariant, string> = {
  loading: 'border-cyan-300/20 bg-cyan-400/10 text-cyan-50',
  empty: 'border-white/10 bg-white/5 text-slate-200',
  error: 'border-rose-300/20 bg-rose-400/10 text-rose-50',
  success: 'border-emerald-300/20 bg-emerald-400/10 text-emerald-50',
  info: 'border-amber-300/20 bg-amber-400/10 text-amber-50',
};

const badgeClasses: Record<WorkflowStateVariant, string> = {
  loading: 'text-cyan-100',
  empty: 'text-slate-300',
  error: 'text-rose-100',
  success: 'text-emerald-100',
  info: 'text-amber-100',
};

export function WorkflowState({ variant, title, description, action }: WorkflowStateProps) {
  return (
    <div className={`rounded-2xl border p-4 ${variantClasses[variant]}`} aria-live={variant === 'loading' ? 'polite' : undefined}>
      <p className={`text-xs uppercase tracking-[0.2em] ${badgeClasses[variant]}`}>{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-200">{description}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}