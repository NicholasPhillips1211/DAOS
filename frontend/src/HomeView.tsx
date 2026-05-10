import { Tooltip } from './Tooltip';

type HomeViewProps = {
  onStartTour: () => void;
  onEnterWorkspace: () => void;
};

export function HomeView({ onStartTour, onEnterWorkspace }: HomeViewProps) {
  return (
    <main className="relative min-h-screen overflow-hidden text-slate-100">
      {/* Background gradients */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="absolute right-[-5rem] top-20 h-80 w-80 rounded-full bg-amber-300/15 blur-3xl" />
        <div className="absolute bottom-[-6rem] left-1/3 h-96 w-96 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>

      <section className="relative mx-auto w-full max-w-7xl px-6 py-8 lg:px-10 lg:py-16">
        {/* Hero Section */}
        <div className="rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-slate-950/80 to-slate-950/50 p-8 md:p-12 lg:p-16 shadow-[0_30px_120px_rgba(0,0,0,0.35)] backdrop-blur-xl mb-12">
          <div className="max-w-3xl">
            <p className="text-xs uppercase tracking-[0.5em] text-cyan-200/90">Welcome to DAOS</p>
            <h1 className="mt-4 text-5xl md:text-6xl font-bold tracking-tight text-white">
              Move From Data To Decisions
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-300 max-w-2xl">
              DAOS is an intelligent workspace for data teams. Ingest, explore, automate, and share insights—all in one place. No more juggling separate tools.
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Tooltip content="Start a step-by-step walkthrough of DAOS features">
                <button
                  onClick={onStartTour}
                  className="px-8 py-4 rounded-full bg-cyan-500 text-slate-950 font-semibold hover:bg-cyan-400 transition shadow-lg hover:shadow-xl"
                >
                  ✨ Take the Tour
                </button>
              </Tooltip>

              <Tooltip content="Jump directly into your workspace">
                <button
                  onClick={onEnterWorkspace}
                  className="px-8 py-4 rounded-full border-2 border-cyan-400/60 bg-white/5 text-white font-semibold hover:bg-white/10 transition"
                >
                  Enter Workspace →
                </button>
              </Tooltip>
            </div>
          </div>
        </div>

        {/* Key Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {/* Ingestion */}
          <div
            id="ingestion-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">📥</div>
            <h3 className="text-xl font-semibold text-white mb-2">Data Ingestion</h3>
            <p className="text-sm text-slate-300 leading-6">
              Upload CSV files, connect live databases, or sync APIs. Your data is versioned, auditable, and immediately available for analysis.
            </p>
            <Tooltip content="View all ingestion options" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>

          {/* Analysis */}
          <div
            id="analysis-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">Explore & Analyze</h3>
            <p className="text-sm text-slate-300 leading-6">
              Write SQL queries, build interactive dashboards, and generate visualizations. All backed by a lakehouse that scales with your data.
            </p>
            <Tooltip content="Try the SQL editor" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>

          {/* Automation */}
          <div
            id="automation-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="text-xl font-semibold text-white mb-2">AI Automation</h3>
            <p className="text-sm text-slate-300 leading-6">
              Describe what you want automated. DAOS generates an actionable plan with triggers, actions, and next steps.
            </p>
            <Tooltip content="Generate your first automation plan" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>

          {/* Collaboration */}
          <div
            id="collaboration-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">💬</div>
            <h3 className="text-xl font-semibold text-white mb-2">Collaborate</h3>
            <p className="text-sm text-slate-300 leading-6">
              Comment, share dashboards, and approve workflows. Built-in audit trails ensure accountability and compliance.
            </p>
            <Tooltip content="Invite team members" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>

          {/* Governance */}
          <div
            id="governance-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">🔐</div>
            <h3 className="text-xl font-semibold text-white mb-2">Governance</h3>
            <p className="text-sm text-slate-300 leading-6">
              Role-based access control, data lineage, and compliance tracking. Enterprise-ready from day one.
            </p>
            <Tooltip content="Configure governance policies" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>

          {/* Recommendations */}
          <div
            id="recommendations-section"
            className="rounded-2xl border border-white/10 bg-slate-950/65 p-6 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur hover:border-white/20 transition"
          >
            <div className="text-3xl mb-3">💡</div>
            <h3 className="text-xl font-semibold text-white mb-2">Smart Recommendations</h3>
            <p className="text-sm text-slate-300 leading-6">
              DAOS learns from your workspace and suggests next steps: missing metrics, quality issues, or optimization opportunities.
            </p>
            <Tooltip content="View personalized suggestions" position="bottom">
              <button className="mt-4 text-xs text-cyan-300 hover:text-cyan-200 font-medium">
                Learn more →
              </button>
            </Tooltip>
          </div>
        </div>

        {/* Quick Start Section */}
        <div className="rounded-2xl border border-white/10 bg-slate-950/65 p-8 md:p-10 shadow-[0_24px_90px_rgba(0,0,0,0.25)] backdrop-blur">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-6">Get Started In 3 Steps</h2>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500 text-slate-950 font-bold text-lg">
                1
              </div>
              <h3 className="font-semibold text-white">Upload Your Data</h3>
              <p className="text-sm text-slate-300">
                Use the ingestion feature to upload a CSV file, connect a database, or sync an API. Your data is immediately available.
              </p>
            </div>

            <div className="space-y-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500 text-slate-950 font-bold text-lg">
                2
              </div>
              <h3 className="font-semibold text-white">Explore Your Data</h3>
              <p className="text-sm text-slate-300">
                Write a SQL query, preview the schema, or generate visualizations. See patterns and anomalies at a glance.
              </p>
            </div>

            <div className="space-y-3">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500 text-slate-950 font-bold text-lg">
                3
              </div>
              <h3 className="font-semibold text-white">Share Insights</h3>
              <p className="text-sm text-slate-300">
                Create a dashboard, share it with your team, and set up automation for recurring tasks. Done!
              </p>
            </div>
          </div>

          <div className="mt-10 pt-8 border-t border-white/10 flex flex-col sm:flex-row gap-4 items-center justify-between">
            <p className="text-slate-400 text-sm">
              💬 Have questions? Our guided tour walks you through every feature.
            </p>
            <Tooltip content="See the full walkthrough">
              <button
                onClick={onStartTour}
                className="px-6 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition border border-white/20"
              >
                Start the Tour
              </button>
            </Tooltip>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-slate-400">
          <p>
            Built on FastAPI, React, and PostgreSQL. Local LLM ready.{' '}
            <Tooltip content="See the documentation">
              <a href="#" className="text-cyan-300 hover:text-cyan-200">
                Learn more
              </a>
            </Tooltip>
          </p>
        </footer>
      </section>
    </main>
  );
}
