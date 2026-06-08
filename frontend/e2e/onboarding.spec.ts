import { test, expect } from '@playwright/test';

/**
 * Tests du flux d'onboarding.
 *
 * Prérequis :
 * - Backend FastAPI en cours d'exécution
 * - Un utilisateur de test déjà enregistré (token stocké dans localStorage)
 *
 * Lancer : npx playwright test e2e/onboarding.spec.ts
 */

const TEST_USER = {
  email: 'e2e-onboarding@example.com',
  password: 'Test123!@#',
};

// Helper : s'authentifier et stocker le token
async function login(page: import('@playwright/test').Page) {
  await page.goto('http://localhost:3000/auth/login');
  await page.getByLabel(/email/i).fill(TEST_USER.email);
  await page.getByLabel(/mot de passe/i, { exact: false }).first().fill(TEST_USER.password);
  await page.getByRole('button', { name: /connexion/i }).click();
  await page.waitForURL(/onboarding|dashboard/, { timeout: 10000 });
}

test.describe('Flux onboarding', () => {
  test('parcourt les 3 phases d\'onboarding', async ({ page }) => {
    // Ce test nécessite un compte frais (sans onboarding complété)
    await login(page);

    // Si on arrive sur le dashboard, l'onboarding est déjà fait
    const url = page.url();
    if (url.includes('dashboard')) {
      test.skip(true, 'Onboarding déjà complété pour cet utilisateur');
      return;
    }

    // Phase 1 : Informations de base (sport, niveau)
    await expect(page.getByText(/sport|niveau|expérience/i).first()).toBeVisible({ timeout: 5000 });

    // Sélectionner un sport
    const sportButton = page.getByText(/cyclisme|course|triathlon|fitness/i).first();
    if (await sportButton.isVisible()) {
      await sportButton.click();
      await page.getByRole('button', { name: /suivant|continuer/i }).click();
    }

    // Phase 2 : Objectifs
    await expect(page.getByText(/objectif|but|souhaites/i).first()).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: /suivant|continuer/i }).click();

    // Phase 3 : PAR-Q (questionnaire de santé)
    await expect(page.getByText(/santé|médical|PAR-Q/i).first()).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: /terminer|finaliser|commencer/i }).click();

    // Vérifier qu'on arrive sur le dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });
});
