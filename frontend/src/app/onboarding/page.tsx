'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { OnboardingFlow } from '@/components/onboarding/OnboardingFlow';

export default function OnboardingPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.replace('/auth/login');
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return null;

  return <OnboardingFlow />;
}
