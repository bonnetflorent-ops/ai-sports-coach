import { test, expect } from '@playwright/test';

/**
 * Tests du flux d'authentification.
 *
 * Prérequis :
 * - Backend FastAPI en cours d'exécution sur localhost:8000
 * - Supabase configuré avec les migrations exécutées
 *
 * Lancer : npx playwright test e2e/auth.spec.ts
 */

test.describe('Inscription', () => {
  test('affiche le formulaire d\'inscription', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/register');
    await expect(page.getByRole('heading', { name: /inscri/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/mot de passe/i)).toBeVisible();
  });

  test('valide les champs requis', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/register');
    // Soumettre sans remplir
    await page.getByRole('button', { name: /inscri/i }).click();
    // Vérifier que les erreurs de validation apparaissent
    await expect(page.getByText(/requis|obligatoire|valide/i).first()).toBeVisible();
  });

  test('inscription réussie redirige vers onboarding', async ({ page }) => {
    const testEmail = `test-${Date.now()}@example.com`;
    await page.goto('http://localhost:3000/auth/register');
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/mot de passe/i, { exact: false }).first().fill('Test123!@#');
    await page.getByRole('button', { name: /inscri/i }).click();

    // Attendre la redirection (onboarding ou dashboard)
    await page.waitForURL(/onboarding|dashboard/, { timeout: 10000 });
  });
});

test.describe('Connexion', () => {
  test('affiche le formulaire de connexion', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/login');
    await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/mot de passe/i)).toBeVisible();
  });

  test('email invalide affiche une erreur', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/login');
    await page.getByLabel(/email/i).fill('pas-une-adresse-valide');
    await page.getByLabel(/mot de passe/i, { exact: false }).first().fill('test');
    await page.getByRole('button', { name: /connexion/i }).click();
    // L'API devrait retourner une erreur
    await expect(page.getByText(/erreur|invalide|incorrect/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('redirection après connexion vers dashboard', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/mot de passe/i, { exact: false }).first().fill('Test123!@#');
    await page.getByRole('button', { name: /connexion/i }).click();

    // Vérifier qu'on arrive sur une page protégée
    await page.waitForURL(/dashboard|onboarding/, { timeout: 10000 });
  });
});

test.describe('Protection des routes', () => {
  test('dashboard redirige vers login si non authentifié', async ({ page }) => {
    // S'assurer qu'aucun token n'est stocké
    await page.evaluate(() => localStorage.clear());
    await page.goto('http://localhost:3000/dashboard');
    // Devrait rediriger vers login
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5000 });
  });

  test('profile redirige vers login si non authentifié', async ({ page }) => {
    await page.evaluate(() => localStorage.clear());
    await page.goto('http://localhost:3000/profile');
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5000 });
  });
});
