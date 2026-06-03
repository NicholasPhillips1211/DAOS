import { useState } from 'react';
import { HomeView } from './HomeView';
import { GuidedTour } from './GuidedTour';
import { WorkspaceControlRoom } from './features/workspace/pages/WorkspaceControlRoom';
import { useGuidedTour } from './useGuidedTour';

type AppProps = {
  initialWorkspaceVisible?: boolean;
};

export default function App({ initialWorkspaceVisible = false }: AppProps) {
  const [showWorkspace, setShowWorkspace] = useState(initialWorkspaceVisible);
  const tour = useGuidedTour();

  return (
    <>
      {!showWorkspace ? (
        <HomeView
          onStartTour={() => {
            setShowWorkspace(true);
            tour.startTour();
          }}
          onEnterWorkspace={() => setShowWorkspace(true)}
        />
      ) : (
        <WorkspaceControlRoom onExitWorkspace={() => setShowWorkspace(false)} />
      )}

      <GuidedTour
        isActive={tour.isTourActive}
        currentStep={tour.currentStep}
        currentStepIndex={tour.currentStepIndex}
        totalSteps={tour.totalSteps}
        onNext={tour.nextStep}
        onPrev={tour.prevStep}
        onSkip={tour.skipTour}
      />
    </>
  );
}
