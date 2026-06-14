import { routes, type VercelConfig } from '@vercel/config/v1';

export const config: VercelConfig = {
  buildCommand: 'npm run build',
  framework: 'nextjs',
  installCommand: 'npm install',
  rewrites: [
    routes.rewrite('/api/(.*)', 'https://pwa-api.srv780916.hstgr.cloud/api/$1'),
  ],
  headers: [
    routes.cacheControl('/static/(.*)', { public: true, maxAge: '1 week', immutable: true }),
  ],
  crons: [],
};
