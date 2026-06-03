import { routes, type VercelConfig } from '@vercel/config/v1';

export const config: VercelConfig = {
  buildCommand: 'npm run build',
  framework: 'nextjs',
  installCommand: 'npm install',
  rewrites: [
    routes.rewrite('/api/(.*)', 'https://api.coach-sportif.app/$1'),
  ],
  headers: [
    routes.cacheControl('/static/(.*)', { public: true, maxAge: '1 week', immutable: true }),
  ],
  crons: [],
};
