import { useState, useCallback } from 'react';

export type TourStep = {
  id: string;
  title: string;
  description: string;
  target?: string;
  action?: () => void;
};

const TOUR_STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to DAOS',
    description: 'DAOS is your intelligent DataOps workspace. Let me show you how to get started.',
  },
  {
    id: 'ingestion',
    title: 'Data Ingestion',
    description: 'Upload CSV files, connect databases, or sync data sources. Your data lands in a versioned, auditable repository.',
    target: 'ingestion-section',
  },
  {
    id: 'analysis',
    title: 'Analyze & Explore',
    description: 'Write SQL queries, create visualizations, and build dashboards. All backed by a lakehouse that makes your data queryable.',
    target: 'analysis-section',
  },
  {
    id: 'automation',
    title: 'AI-Powered Automation',
    description: 'Generate automation plans using AI. Describe what you want, and DAOS suggests triggers, actions, and next steps.',
    target: 'automation-section',
  },
  {
    id: 'collaboration',
    title: 'Collaborate & Share',
    description: 'Comment, share dashboards, and track changes. Built-in governance ensures accountability and compliance.',
    target: 'collaboration-section',
  },
  {
    id: 'recommendations',
    title: 'Get Recommendations',
    description: 'DAOS learns from your workspace and suggests next steps: missing metrics, data quality issues, or optimization opportunities.',
    target: 'recommendations-section',
  },
];

export function useGuidedTour() {
  const [isTourActive, setIsTourActive] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedTourOnce, setCompletedTourOnce] = useState(false);

  const currentStep = TOUR_STEPS[currentStepIndex];

  const startTour = useCallback(() => {
    setIsTourActive(true);
    setCurrentStepIndex(0);
  }, []);

  const nextStep = useCallback(() => {
    if (currentStepIndex < TOUR_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      endTour();
    }
  }, [currentStepIndex]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  }, [currentStepIndex]);

  const endTour = useCallback(() => {
    setIsTourActive(false);
    setCompletedTourOnce(true);
  }, []);

  const skipTour = useCallback(() => {
    endTour();
  }, [endTour]);

  return {
    isTourActive,
    currentStep,
    currentStepIndex,
    totalSteps: TOUR_STEPS.length,
    completedTourOnce,
    startTour,
    nextStep,
    prevStep,
    endTour,
    skipTour,
    allSteps: TOUR_STEPS,
  };
}
