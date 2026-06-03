'use client';

import { useState, FormEvent } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { apiFetch } from '@/lib/api';

interface BugReportProps {
  open: boolean;
  onClose: () => void;
}

export function BugReport({ open, onClose }: BugReportProps) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const capturedUrl = typeof window !== 'undefined' ? window.location.href : '';
  const capturedTimestamp = new Date().toLocaleString('fr-FR');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await apiFetch('/api/chat/feedback', {
        method: 'POST',
        body: JSON.stringify({
          type: 'bug',
          detail: description,
          url: capturedUrl,
          timestamp: capturedTimestamp,
        }),
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setDescription('');
        onClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Signaler un bug</DialogTitle>
          <DialogDescription>
            Décris le problème que tu as rencontré pour aider l&apos;équipe à le corriger.
          </DialogDescription>
        </DialogHeader>

        {success ? (
          <div className="py-8 text-center">
            <p className="text-emerald-400 text-lg mb-2">✅ Merci !</p>
            <p className="text-sm text-slate-400">
              Ton rapport a bien été envoyé.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="bug-description" className="text-sm font-medium text-slate-200">
                  Description du problème
                </label>
                <Textarea
                  id="bug-description"
                  placeholder="Explique ce qui s'est passé..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  rows={4}
                />
              </div>

              <div className="space-y-1.5 text-xs text-slate-500 bg-slate-800/50 rounded-lg p-3">
                <p>
                  <span className="text-slate-400">URL :</span> {capturedUrl}
                </p>
                <p>
                  <span className="text-slate-400">Date :</span> {capturedTimestamp}
                </p>
              </div>

              {error && <p className="text-sm text-red-400">{error}</p>}
            </div>

            <DialogFooter className="mt-6">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                Annuler
              </Button>
              <Button type="submit" disabled={loading || !description.trim()}>
                {loading ? 'Envoi...' : 'Envoyer'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
