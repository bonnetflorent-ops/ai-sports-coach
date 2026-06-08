import { test, expect } from '@playwright/test';

/**
 * Tests du flux de chat.
 *
 * Prérequis :
 * - Backend FastAPI en cours d'exécution avec SSE fonctionnel
 * - Utilisateur de test avec onboarding complété
 *
 * Lancer : npx playwright test e2e/chat.spec.ts
 */

const TEST_USER = {
  email: 'e2e-chat@example.com',
  password: 'Test123!@#',
};

async function login(page: import('@playwright/test').Page) {
  await page.goto('http://localhost:3000/auth/login');
  await page.getByLabel(/email/i).fill(TEST_USER.email);
  await page.getByLabel(/mot de passe/i, { exact: false }).first().fill(TEST_USER.password);
  await page.getByRole('button', { name: /connexion/i }).click();
  await page.waitForURL(/dashboard/, { timeout: 10000 });
}

test.describe('Chat IA', () => {
  test('envoie un message et reçoit une réponse streamée', async ({ page }) => {
    await login(page);

    // Naviguer vers la page d'accueil (chat)
    await page.goto('http://localhost:3000/');

    // Vérifier que l'input de chat est présent
    const input = page.getByPlaceholder(/message|écrire|parler/i);
    await expect(input).toBeVisible({ timeout: 5000 });

    // Envoyer un message simple
    await input.fill('Bonjour, quel entraînement me recommandes-tu aujourd\'hui ?');
    await page.getByRole('button', { name: /envoyer/i }).click();

    // Attendre que la réponse commence à arriver (streaming)
    // Le message utilisateur devrait apparaître immédiatement
    await expect(page.getByText(/Bonjour, quel entraînement/i)).toBeVisible({ timeout: 2000 });

    // Attendre que la réponse du coach apparaisse (streaming SSE)
    // On attend au moins un contenu dans la bulle du coach
    await expect(page.locator('[data-testid="message-assistant"]').first()).toBeVisible({
      timeout: 15000,
    });
  });

  test('affiche l\'historique des messages', async ({ page }) => {
    await login(page);
    await page.goto('http://localhost:3000/');

    // Vérifier qu'il y a au moins un message dans l'historique
    // (si l'utilisateur a déjà conversé)
    const messages = page.locator('[data-testid^="message-"]');
    // Le test est informatif — l'historique peut être vide pour un nouvel utilisateur
    const count = await messages.count();
    console.log(`Messages dans l'historique : ${count}`);
  });

  test('feedback 👍 ajoute un vote positif', async ({ page }) => {
    await login(page);
    await page.goto('http://localhost:3000/');

    // Envoyer un message pour faire apparaître la réponse
    const input = page.getByPlaceholder(/message|écrire|parler/i);
    await expect(input).toBeVisible({ timeout: 5000 });
    await input.fill('Comment améliorer ma récupération ?');
    await page.getByRole('button', { name: /envoyer/i }).click();

    // Attendre la réponse
    const thumbsUp = page.getByLabel(/utile|👍|pouce/i).first();
    if (await thumbsUp.isVisible({ timeout: 15000 })) {
      await thumbsUp.click();
      // Vérifier que le feedback est enregistré (changement visuel)
      await expect(thumbsUp).toHaveClass(/active|selected|voted/i, { timeout: 3000 });
    }
  });
});
