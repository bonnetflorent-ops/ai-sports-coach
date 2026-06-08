// Génère les icônes PWA à partir d'un SVG source
// Usage : node scripts/generate-icons.mjs

import sharp from 'sharp';
import { writeFileSync } from 'fs'; // eslint-disable-line @typescript-eslint/no-unused-vars
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const iconsDir = join(__dirname, '..', 'public', 'icons');

// Icône SVG : un cercle dynamique représentant un athlète en mouvement
// Design épuré, thème bleu sportif
const svgIcon = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 512 512" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e40af"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#60a5fa"/>
      <stop offset="100%" stop-color="#93c5fd"/>
    </linearGradient>
  </defs>

  <!-- Fond : cercle arrondi -->
  <rect width="512" height="512" rx="112" fill="url(#bg)"/>

  <!-- Figure athlète stylisée : "C" abstrait avec barre de progression -->
  <!-- Arc principal (corps en mouvement) -->
  <path d="M170 380 C 130 340, 120 250, 180 200 C 220 170, 280 170, 310 200
           C 340 230, 340 280, 310 310 C 280 340, 240 340, 220 320"
        stroke="white" stroke-width="36" stroke-linecap="round" stroke-linejoin="round" fill="none"/>

  <!-- Jambe avant (extension dynamique) -->
  <path d="M280 290 L 350 370" stroke="white" stroke-width="36" stroke-linecap="round" fill="none"/>

  <!-- Tête -->
  <circle cx="210" cy="170" r="30" fill="url(#accent)"/>

  <!-- Barres de progression (coaching/data) -->
  <rect x="80" y="430" width="40" height="24" rx="12" fill="white" opacity="0.5"/>
  <rect x="132" y="410" width="40" height="44" rx="12" fill="white" opacity="0.7"/>
  <rect x="184" y="390" width="40" height="64" rx="12" fill="white" opacity="0.9"/>
  <rect x="236" y="370" width="40" height="84" rx="12" fill="white"/>
</svg>
`;

// SVG simplifié pour favicon (juste un "C" stylisé sportif)
const svgFavicon = `
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e40af"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
  </defs>
  <rect width="32" height="32" rx="7" fill="url(#bg)"/>
  <path d="M11 22 C9 20, 8 15, 11 12 C14 10, 17 12, 18 14 C19 16, 18 19, 16 20"
        stroke="white" stroke-width="2.5" stroke-linecap="round" fill="none"/>
  <circle cx="14" cy="11" r="3" fill="white"/>
</svg>
`;

const appleTouchSvg = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 512 512" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <!-- Fond sombre avec padding pour iOS -->
  <rect width="512" height="512" rx="100" fill="url(#bg)"/>
  <!-- Icône centrée plus petite -->
  <g transform="translate(56, 56) scale(0.78)">
    <!-- Fond -->
    <rect width="512" height="512" rx="112" fill="url(#bg2)"/>
    <!-- Arc -->
    <path d="M170 380 C 130 340, 120 250, 180 200 C 220 170, 280 170, 310 200
             C 340 230, 340 280, 310 310 C 280 340, 240 340, 220 320"
          stroke="white" stroke-width="36" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <!-- Jambe -->
    <path d="M280 290 L 350 370" stroke="white" stroke-width="36" stroke-linecap="round" fill="none"/>
    <!-- Tête -->
    <circle cx="210" cy="170" r="30" fill="#60a5fa"/>
    <!-- Barres -->
    <rect x="80" y="430" width="40" height="24" rx="12" fill="white" opacity="0.5"/>
    <rect x="132" y="410" width="40" height="44" rx="12" fill="white" opacity="0.7"/>
    <rect x="184" y="390" width="40" height="64" rx="12" fill="white" opacity="0.9"/>
    <rect x="236" y="370" width="40" height="84" rx="12" fill="white"/>
  </g>
</svg>
`;

async function generate() {
  // Générer les icônes principales
  const sizes = {
    'icon-192.png': 192,
    'icon-512.png': 512,
  };

  for (const [filename, size] of Object.entries(sizes)) {
    const svg = svgIcon(size);
    await sharp(Buffer.from(svg))
      .resize(size, size)
      .png()
      .toFile(join(iconsDir, filename));
    console.log(`✓ ${filename} (${size}x${size})`);
  }

  // Apple Touch Icon (180x180, fond sombre pour iOS)
  const appleSvg = appleTouchSvg(180);
  await sharp(Buffer.from(appleSvg))
    .resize(180, 180)
    .png()
    .toFile(join(iconsDir, 'apple-touch-icon.png'));
  console.log('✓ apple-touch-icon.png (180x180)');

  // Favicon
  const favicon32 = await sharp(Buffer.from(svgFavicon)).resize(32, 32).png().toBuffer();
  // Écrire en PNG (les navigateurs modernes supportent favicon.png)
  await sharp(Buffer.from(svgFavicon))
    .resize(32, 32)
    .png()
    .toFile(join(iconsDir, 'favicon.png'));
  console.log('✓ favicon.png (32x32)');

  // Écrire le favicon.ico (juste le 32x32 en PNG — la plupart des navigateurs l'acceptent)
  const faviconPath = join(__dirname, '..', 'public', 'favicon.ico');
  await sharp(favicon32).toFile(faviconPath);
  console.log('✓ favicon.ico (32x32)');

  console.log('\nToutes les icônes générées avec succès !');
}

generate().catch(err => {
  console.error('Erreur:', err);
  process.exit(1);
});
