'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

/**
 * Bannière d'installation PWA.
 *
 * Capture l'événement beforeinstallprompt et affiche une bannière
 * avec un bouton "Installer l'app".
 */
export function PwaInstallBanner() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function onInstall(e: Event) {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setVisible(true);
    }

    // Déjà installée ?
    if (window.matchMedia('(display-mode: standalone)').matches) return;

    window.addEventListener('beforeinstallprompt', onInstall);
    return () => window.removeEventListener('beforeinstallprompt', onInstall);
  }, []);

  const handleInstall = useCallback(async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setVisible(false);
    }
    setDeferredPrompt(null);
  }, [deferredPrompt]);

  const handleDismiss = useCallback(() => {
    setVisible(false);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed bottom-20 left-4 right-4 z-50 flex items-center justify-between gap-3 rounded-xl bg-slate-800/95 border border-slate-700 p-4 shadow-lg backdrop-blur md:bottom-4 md:left-1/2 md:right-auto md:max-w-md md:-translate-x-1/2">
      <div className="flex items-center gap-3 min-w-0">
        <div className="shrink-0 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-400">
          <Download className="h-5 w-5 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-100">Installer Coach Sportif</p>
          <p className="text-xs text-slate-400 truncate">
            Accès rapide et mode hors-ligne
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="text-slate-400 hover:text-slate-200"
          onClick={handleDismiss}
        >
          Plus tard
        </Button>
        <Button
          size="sm"
          className="bg-blue-600 hover:bg-blue-500"
          onClick={handleInstall}
        >
          Installer
        </Button>
      </div>
    </div>
  );
}

/** Type pour l'événement beforeinstallprompt (non standard). */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}
