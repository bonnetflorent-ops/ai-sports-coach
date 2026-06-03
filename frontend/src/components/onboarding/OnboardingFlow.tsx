'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Phase1Form } from './Phase1Form';
import { Phase2Form } from './Phase2Form';
import { ParQForm } from './ParQForm';

const TOTAL_STEPS = 3;

const STEP_CONFIG = [
  { step: 1, title: 'Profil sportif', label: 'Étape 1/3', Form: Phase1Form },
  { step: 2, title: 'Infos complémentaires', label: 'Étape 2/3', Form: Phase2Form },
  { step: 3, title: 'Questionnaire santé', label: 'Étape 3/3', Form: ParQForm },
];

export function OnboardingFlow() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);

  const config = STEP_CONFIG[currentStep];
  const progressPercent = ((currentStep + 1) / TOTAL_STEPS) * 100;

  function handleStepComplete() {
    if (currentStep < TOTAL_STEPS - 1) {
      setCurrentStep(currentStep + 1);
    }
  }

  function handleSkip() {
    if (currentStep < TOTAL_STEPS - 1) {
      setCurrentStep(currentStep + 1);
    }
  }

  function handleOnboardingComplete() {
    // Update localStorage to mark onboarding as completed
    const stored = localStorage.getItem('user');
    if (stored) {
      try {
        const user = JSON.parse(stored);
        user.onboarding_completed = true;
        localStorage.setItem('user', JSON.stringify(user));
      } catch {
        // ignore parse errors
      }
    }
    router.push('/');
  }

  const FormComponent = config.Form;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          {/* Step indicator */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">
              {config.label}
            </span>
            <span className="text-xs text-slate-500">
              {currentStep + 1}/{TOTAL_STEPS}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <CardTitle className="text-xl text-center text-slate-50 mt-3">
            {config.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {currentStep === 0 && (
            <Phase1Form onSuccess={handleStepComplete} />
          )}
          {currentStep === 1 && (
            <Phase2Form onSuccess={handleStepComplete} onSkip={handleSkip} />
          )}
          {currentStep === 2 && (
            <ParQForm onSuccess={handleOnboardingComplete} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
