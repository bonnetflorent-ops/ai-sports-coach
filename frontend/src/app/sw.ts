/// <reference lib="webworker" />
import { defaultCache } from '@serwist/next/worker';
import type { PrecacheEntry, SerwistGlobalConfig } from 'serwist';
import { CacheFirst, ExpirationPlugin, Serwist } from 'serwist';

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

// Extension du type NotificationOptions pour supporter vibrate + actions
type PushNotificationOptions = NotificationOptions & {
  vibrate?: number[];
  actions?: { action: string; title: string }[];
};

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  // Page de fallback hors-ligne (servie quand une navigation échoue)
  precacheOptions: {
    navigateFallback: '/offline.html',
  },
  runtimeCaching: [
    ...defaultCache,
    // Cache agressif des icônes PWA (rarement modifiées, critiques pour l'UX hors-ligne)
    {
      matcher: /\/icons\/.*\.png$/i,
      handler: new CacheFirst({
        cacheName: 'pwa-icons',
        plugins: [
          new ExpirationPlugin({
            maxEntries: 16,
            maxAgeSeconds: 90 * 24 * 60 * 60, // 90 jours
            maxAgeFrom: 'last-used',
          }),
        ],
      }),
    },
  ],
});

// ── Push notification handling ───────────────────────────────────────
self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  const title = data.title || 'Coach Sportif';
  const options: PushNotificationOptions = {
    body: data.body || '',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    data: data.url || '/',
    vibrate: [200, 100, 200],
  };
  if (data.url) {
    options.actions = [{ action: 'open', title: 'Voir' }];
  }
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      const existing = clients.find((c) => c.url.includes(url));
      if (existing) {
        existing.focus();
      } else {
        self.clients.openWindow(url);
      }
    }),
  );
});

serwist.addEventListeners();
