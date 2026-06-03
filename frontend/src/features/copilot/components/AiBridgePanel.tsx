import { cardClass } from '../../../components/ui';

export function AiBridgePanel() {
  return (
    <section className={cardClass}>
      <p className="text-xs uppercase tracking-[0.35em] text-amber-200/90">Local LLM Bridge</p>
      <h3 className="mt-2 text-2xl font-semibold text-white">LM Studio-compatible by design</h3>
      <p className="mt-3 text-sm leading-6 text-slate-300">
        Point the backend at a local OpenAI-style endpoint such as LM Studio. If it is unavailable, the app still
        produces a usable automation plan from workspace signals.
      </p>
      <div className="mt-4 space-y-3 text-sm text-slate-200">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          Backend endpoint: <span className="text-cyan-200">POST /api/v1/automation/generate</span>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          Expected model server: <span className="text-amber-100">http://localhost:1234/v1</span>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          Output format: <span className="text-emerald-100">JSON plan with triggers, actions, and next steps</span>
        </div>
      </div>
    </section>
  );
}
