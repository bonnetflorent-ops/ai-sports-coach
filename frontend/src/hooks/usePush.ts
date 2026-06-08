'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '@/lib/api';

/**
 * Hook de gestion des Web Push notifications.
 *
 * Vérifie si le navigateur supporte les push notifications,
 * expose l'état de permission actuel, et fournit les fonctions
 * pour s'abonner / se désabonner.
 *
 * Usage :
 *   const { permission, subscribed, subscribe, unsubscribe } = usePush();
 */
export function usePush() {
  const [permission, setPermission] = useState<NotificationPermission>(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      return Notification.permission;
    }
    return 'default';
  });
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [supported] = useState(() => {
    return (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      'PushManager' in window
    );
  });

  // Vérifie l'abonnement existant au montage
  useEffect(() => {
    if (!supported) return;

    // Vérifie si déjà abonné
    async function checkSubscription() {
      try {
        const sw = await navigator.serviceWorker.ready;
        const sub = await sw.pushManager.getSubscription();
        setSubscribed(!!sub);
      } catch {
        setSubscribed(false);
      }
    }
    checkSubscription();
  }, [supported]);

  const subscribe = useCallback(async () => {
    if (!supported) {
      console.warn('Push API non supportée');
      return false;
    }

    setLoading(true);
    try {
      // 1. Demander la permission (si pas encore accordée)
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== 'granted') {
        setLoading(false);
        return false;
      }

      // 2. Récupérer la clé publique VAPID depuis le backend
      const { public_key } = await apiFetch<{ public_key: string }>(
        '/api/push/vapid-public-key',
      );

      // 3. S'abonner via le Service Worker
      const sw = await navigator.serviceWorker.ready;
      const subscription = await sw.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key) as BufferSource,
      });

      // 4. Envoyer la souscription au backend
      await apiFetch('/api/push/subscribe', {
        method: 'POST',
        body: JSON.stringify(subscription.toJSON()),
      });

      setSubscribed(true);
      setLoading(false);
      return true;
    } catch (err) {
      console.error("Erreur lors de l'abonnement push:", err);
      setLoading(false);
      return false;
    }
  }, [supported]);

  const unsubscribe = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Supprimer la souscription côté navigateur
      const sw = await navigator.serviceWorker.ready;
      const sub = await sw.pushManager.getSubscription();
      if (sub) {
        await sub.unsubscribe();
      }

      // 2. Informer le backend
      try {
        await apiFetch('/api/push/subscribe', { method: 'DELETE' });
      } catch {
        // Ignorer l'erreur côté backend — le navigateur est déjà désabonné
      }

      setSubscribed(false);
      setLoading(false);
      return true;
    } catch (err) {
      console.error('Erreur lors du désabonnement push:', err);
      setLoading(false);
      return false;
    }
  }, []);

  return { supported, permission, subscribed, loading, subscribe, unsubscribe };
}

/**
 * Convertit une clé VAPID base64 en Uint8Array
 * (format requis par l'API PushManager.subscribe).
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}
