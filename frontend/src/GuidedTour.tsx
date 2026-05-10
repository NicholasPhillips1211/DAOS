import { useEffect, useRef } from 'react';
import { TourStep } from './useGuidedTour';

type GuidedTourProps = {
  isActive: boolean;
  currentStep: TourStep | undefined;
  currentStepIndex: number;
  totalSteps: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
};

export function GuidedTour({
  isActive,
  currentStep,
  currentStepIndex,
  totalSteps,
  onNext,
  onPrev,
  onSkip,
}: GuidedTourProps) {
  const highlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !currentStep?.target) {
      if (highlightRef.current) {
        highlightRef.current.style.display = 'none';
      }
      return;
    }

    const targetElement = document.getElementById(currentStep.target);
    if (!targetElement || !highlightRef.current) return;

    const rect = targetElement.getBoundingClientRect();
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scrollLeft = window.scrollX || document.documentElement.scrollLeft;

    highlightRef.current.style.display = 'block';
    highlightRef.current.style.top = `${rect.top + scrollTop - 8}px`;
    highlightRef.current.style.left = `${rect.left + scrollLeft - 8}px`;
    highlightRef.current.style.width = `${rect.width + 16}px`;
    highlightRef.current.style.height = `${rect.height + 16}px`;

    const handleScroll = () => {
      if (!targetElement || !highlightRef.current) return;
      const newRect = targetElement.getBoundingClientRect();
      const newScrollTop = window.scrollY || document.documentElement.scrollTop;
      const newScrollLeft = window.scrollX || document.documentElement.scrollLeft;

      highlightRef.current.style.top = `${newRect.top + newScrollTop - 8}px`;
      highlightRef.current.style.left = `${newRect.left + newScrollLeft - 8}px`;
      highlightRef.current.style.width = `${newRect.width + 16}px`;
      highlightRef.current.style.height = `${newRect.height + 16}px`;
    };

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, [isActive, currentStep]);

  if (!isActive) return null;

  return (
    <>
      {/* Dark overlay mask */}
      <div className="fixed inset-0 z-40 bg-black/70 pointer-events-auto" onClick={onSkip} />

      {/* Highlight box around target element */}
      <div
        ref={highlightRef}
        className="fixed z-40 border-2 border-cyan-400 rounded-lg shadow-[0_0_0_9999px_rgba(0,0,0,0.7)] pointer-events-none transition-all duration-300"
      />

      {/* Tutorial popup */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 max-w-lg w-full mx-4">
        <div className="rounded-2xl border border-cyan-400/60 bg-slate-900 shadow-2xl p-8 backdrop-blur">
          {/* Progress indicator */}
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs uppercase tracking-widest text-cyan-300">
              Step {currentStepIndex + 1} of {totalSteps}
            </div>
            <div className="flex gap-1">
              {Array.from({ length: totalSteps }).map((_, i) => (
                <div
                  key={i}
                  className={`h-2 w-2 rounded-full transition-colors ${
                    i === currentStepIndex ? 'bg-cyan-400' : i < currentStepIndex ? 'bg-emerald-400' : 'bg-slate-600'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Title and description */}
          <h2 className="text-2xl font-bold text-white mb-3">{currentStep?.title}</h2>
          <p className="text-slate-300 text-base leading-relaxed mb-6">{currentStep?.description}</p>

          {/* Navigation buttons */}
          <div className="flex gap-3">
            <button
              onClick={onPrev}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 rounded-lg border border-slate-500 text-sm font-medium text-slate-300 hover:border-slate-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              ← Previous
            </button>

            <button
              onClick={onSkip}
              className="px-4 py-2 rounded-lg border border-slate-500 text-sm font-medium text-slate-300 hover:border-slate-400 hover:text-white transition"
            >
              Skip Tour
            </button>

            <button
              onClick={onNext}
              className="ml-auto px-6 py-2 rounded-lg bg-cyan-500 text-slate-950 text-sm font-semibold hover:bg-cyan-400 transition"
            >
              {currentStepIndex === totalSteps - 1 ? 'Finish' : 'Next →'}
            </button>
          </div>

          {/* Helpful tip */}
          <p className="text-xs text-slate-500 mt-6 text-center">
            💡 Hover over buttons throughout the app to see quick explanations
          </p>
        </div>
      </div>
    </>
  );
}
