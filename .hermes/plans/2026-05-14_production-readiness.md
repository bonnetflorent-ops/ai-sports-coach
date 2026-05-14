# Plan de Préparation Production — AI Sports Coach

> **Pour Hermes :** Utilise subagent-driven-development pour implémenter ce plan phase par phase.

**Objectif :** Transformer le MVP actuel (bot Telegram polling, sans tests, sans monitoring) en une application prête pour un déploiement à 1000+ utilisateurs.

**Architecture cible :** Bot Telegram webhook → FastAPI → pipeline LLM 2 étages (sélecteur + coach) → Supabase. Avec tests complets, monitoring, contrôle des coûts, et résilience.

**Stack technique :** Python 3.11, aiogram 3 (webhooks), FastAPI, DeepSeek V4 (OpenRouter), Supabase, Docker, pytest, structlog

**Contexte :** Revue d'architecture complète du 2026-05-14. 16 problèmes identifiés, classés en 6 phases.

---

## Vue d'ensemble des phases

| Phase | Nom | Impact | Tâches |
|-------|-----|--------|--------|
| 1 | 🔴 Sauvegarde & versionnement | Perte de données | 6 |
| 2 | 🔴 Fondations (tests + résilience) | Stabilité | 10 |
| 3 | 🟡 Scalabilité (webhooks + infra) | Performance | 8 |
| 4 | 🟡 Observabilité | Visibilité | 6 |
| 5 | 🟢 Qualité coaching | Expérience utilisateur | 5 |
| 6 | 🟢 Préparation lancement | Production readiness | 4 |

**Total : 39 tâches**

---

## Phase 1 : Sauvegarde & Versionnement 🔴

> **Pourquoi d'abord :** Le code du moteur de connaissances (`src/engine/`), la couche DB (`src/db/`), et les 2393 lignes de contenu scientifique (`knowledge/`) sont tous UNTRACKED dans git. Un crash VPS = perte totale. Cette phase prend 15 minutes et élimine le risque n°1.

### Task 1.1 : Commiter tout le code non versionné

**Objectif :** Ajouter tous les fichiers untracked au repo Git et les pusher.

**Vérification :**
```bash
cd ~/ai-sports-coach
git status  # Doit montrer uniquement les fichiers à committer
git add knowledge/ scripts/ src/db/ src/engine/knowledge.py src/engine/prompt_builder.py src/engine/selector.py
git add pyproject.toml src/bot/handlers/chat.py src/bot/handlers/start.py src/utils/config.py
git commit -m "feat: moteur de connaissances complet + couche DB + contenu scientifique

- Ajout index.yaml (30 concepts, 7 domaines, 2393 lignes)
- Ajout loader connaissances (knowledge.py)
- Ajout sélecteur LLM (selector.py)
- Ajout prompt builder (prompt_builder.py)
- Ajout couche DB Supabase (users, sessions)
- Ajout schéma SQL initial
- Contenu scientifique : 7 fichiers markdown
- Mise à jour handlers bot + config"

git push origin master
```

**Vérification post-push :**
```bash
git log --oneline -3  # Voir le nouveau commit
git status  # Doit être clean
```

---

### Task 1.2 : Mettre à jour .gitignore

**Objectif :** S'assurer que les fichiers sensibles et générés ne seront jamais commit.

**Fichier :** `.gitignore`

Ajouter les entrées manquantes :
```gitignore
# Fichiers générés
*.egg-info/
__pycache__/
logs/
*.log

# Secrets & config
.env
*.pem
*.key

# IDE
.idea/
.vscode/
*.swp
*.swo

# Dépendances
.venv/
venv/

# Builds
dist/
build/
```

**Vérification :**
```bash
git status --ignored  # Vérifier que .env, logs/, __pycache__ sont bien ignorés
```

---

### Task 1.3 : Vérifier que le .env n'est pas dans l'historique

**Objectif :** Vérifier qu'aucun secret n'a été commité par erreur.

```bash
cd ~/ai-sports-coach
git log --all --full-history -- .env  # Doit être vide
git log --all --full-history --diff-filter=A -- '*.env'  # Doit être vide
```

---

### Task 1.4 : Ajouter un README fonctionnel

**Objectif :** Documenter comment lancer le projet pour un nouveau développeur.

**Fichier :** `README.md` (remplacer le contenu existant)

```markdown
# AI Sports Coach 🏃‍♂️

Assistant d'entraînement IA conversationnel sur Telegram.

## Stack
- **Bot** : aiogram 3 (Telegram)
- **LLM** : DeepSeek V4 via OpenRouter (pipeline 2 étages)
- **Base** : Supabase (PostgreSQL + pgvector)
- **Déploiement** : Docker

## Démarrage rapide

```bash
# 1. Cloner
git clone <repo-url>
cd ai-sports-coach

# 2. Configurer
cp .env.example .env
# Éditer .env avec les vraies clés

# 3. Lancer
pip install .
python -m src.bot.main

# Ou via Docker
docker compose up -d --build
```

## Architecture

Voir `docs/architecture.md` pour l'architecture cible.
Voir `knowledge/index.yaml` pour l'index de la base de connaissances.

## Tests

```bash
pip install ".[dev]"
pytest tests/ -v
```

## Licence

Propriétaire — Tous droits réservés.
```

---

### Task 1.5 : Backuper la base de connaissances

**Objectif :** Créer un backup hors-Supabase du contenu scientifique.

```bash
cd ~/ai-sports-coach
# Vérifier l'intégrité
python3.11 -c "
from src.engine.knowledge import get_all_concepts_for_selector, load_concept
concepts = get_all_concepts_for_selector()
issues = []
for c in concepts:
    for lvl in [1,2,3]:
        content = load_concept(c['id'], lvl)
        if content.startswith('[Concept') or content.startswith('[Niveau'):
            issues.append(f'{c[\"id\"]} level {lvl}: {content}')
if issues:
    print('ISSUES:', issues)
else:
    print(f'✅ All {len(concepts)} concepts loadable at all levels')
"
```

---

### Task 1.6 : Vérifier le backup Git sur GitHub

**Objectif :** Pousser vers le repo GitHub (`bonnetflorent-ops/ai-sports-coach`) et vérifier.

```bash
cd ~/ai-sports-coach
git remote -v  # Vérifier le remote
git push origin master --force-with-lease  # Pusher
```

Le repo doit être visible sur `github.com/bonnetflorent-ops/ai-sports-coach`.

---

## Phase 2 : Fondations (Tests + Résilience) 🔴

> **Pourquoi :** Sans tests, impossible de modifier le code sans tout casser. Sans retry/circuit breaker, toute panne OpenRouter = utilisateurs frustrés. Cette phase crée le filet de sécurité minimal avant d'aller plus loin.

### Task 2.1 : Installer les dépendances de dev

```bash
cd ~/ai-sports-coach
pip install -e ".[dev]"  # pytest + pytest-asyncio
```

### Task 2.2 : Créer la structure de tests

**Créer :** `tests/__init__.py` (fichier vide)
**Créer :** `tests/conftest.py`

```python
# tests/conftest.py
import pytest
import sys
from pathlib import Path

# Ajouter src/ au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

**Créer les répertoires :**
```bash
mkdir -p ~/ai-sports-coach/tests/engine
mkdir -p ~/ai-sports-coach/tests/bot
mkdir -p ~/ai-sports-coach/tests/db
```

---

### Task 2.3 : Test — Parser d'onboarding (_parse_onboarding)

**Objectif :** Tester toutes les variantes du parser d'onboarding pour éviter les régressions silencieuses.

**Créer :** `tests/bot/test_onboarding_parser.py`

```python
"""Tests pour le parser d'onboarding."""
import pytest
from src.bot.handlers.chat import _parse_onboarding


class TestParseOnboarding:
    """Tests pour _parse_onboarding()."""

    def test_parse_complet_cycliste_intermediaire(self):
        """Format standard : numéroté avec toutes les infos."""
        text = (
            "1. Florent\n"
            "2. cyclisme\n"
            "3. intermédiaire\n"
            "4. perdre du poids et faire un granfondo\n"
            "5. 3 créneaux : mardi, jeudi, dimanche\n"
            "6. douleur au genou gauche depuis 2 mois\n"
        )
        result = _parse_onboarding(text, "Florent")
        assert result["name"] == "Florent"
        assert result["sport"] == "cyclisme"
        assert result["level"] == 2
        assert "granfondo" in result.get("goal", "").lower()
        assert "genou" in result.get("blessures", "").lower()

    def test_parse_coureur_debutant(self):
        text = "1. Marie\n2. course à pied\n3. débutant\n4. finir un 10km\n5. 2 créneaux le week-end\n6. RAS"
        result = _parse_onboarding(text, "Marie")
        assert result["name"] == "Marie"
        assert result["sport"] == "running"
        assert result["level"] == 1
        assert "10km" in result.get("goal", "").lower()

    def test_parse_triathlete_expert(self):
        text = "1 Jean\n2 triathlon\n3 expert\n4 Ironman dans 6 mois\n5 8 créneaux\n6 tendinite achille"
        result = _parse_onboarding(text, "Jean")
        assert result["name"] == "Jean"
        assert result["sport"] == "triathlon"
        assert result["level"] == 3
        assert "ironman" in result.get("goal", "").lower()
        assert "tendinite" in result.get("blessures", "").lower()

    def test_parse_sport_velo(self):
        """'vélo' doit être mappé à 'cyclisme'."""
        text = "1. Pierre\n2. vélo\n3. intermédiaire\n4. forme\n5. 3 créneaux\n6. rien"
        result = _parse_onboarding(text, "Pierre")
        assert result["sport"] == "cyclisme"

    def test_parse_fitness_muscu(self):
        """'musculation' doit être mappé à 'fitness'."""
        text = "1. Léa\n2. musculation\n3. débutant\n4. tonification\n5. 4 créneaux\n6. RAS"
        result = _parse_onboarding(text, "Léa")
        assert result["sport"] == "fitness"

    def test_parse_blessures_aucune(self):
        """Les variantes de 'pas de blessure' doivent donner 'Aucune'."""
        for answer in ["non", "aucune", "pas de", "RAS", "rien"]:
            result = _parse_onboarding(
                f"1. X\n2. cyclisme\n3. intermédiaire\n4. test\n5. 3\n6. {answer}", "X"
            )
            assert result["blessures"] == "Aucune", f"Échoué pour: {answer}"

    def test_parse_sans_numeros(self):
        """Réponse sans numérotation explicite."""
        text = "Florent\ncyclisme\nintermédiaire\nêtre en forme\n3 créneaux\npas de blessure"
        result = _parse_onboarding(text, "Florent")
        assert result["sport"] == "cyclisme"
        assert result["level"] == 2

    def test_parse_niveau_avance_confirme(self):
        """Les synonymes de niveau avancé."""
        for mot in ["avancé", "expert", "confirmé"]:
            result = _parse_onboarding(
                f"1. X\n2. running\n3. {mot}\n4. marathon\n5. 5\n6. non", "X"
            )
            assert result["level"] == 3, f"Échoué pour: {mot}"
```

**Vérification :**
```bash
cd ~/ai-sports-coach
python -m pytest tests/bot/test_onboarding_parser.py -v
# Attendu : 8 tests passent
```

---

### Task 2.4 : Test — Parser détails (_parse_details)

**Créer :** `tests/bot/test_details_parser.py`

```python
"""Tests pour le parser des détails optionnels."""
import pytest
from src.bot.handlers.chat import _parse_details


class TestParseDetails:
    def test_parse_poids_taille_age_sexe_email(self):
        text = "75kg 182cm 35 ans homme florent@email.com"
        result = _parse_details(text)
        assert result["weight_kg"] == 75
        assert result["height_cm"] == 182
        assert result["age"] == 35
        assert result["gender"] == "H"
        assert result["email"] == "florent@email.com"

    def test_parse_taille_format_virgule(self):
        """Format 1,77m → 177cm."""
        result = _parse_details("1,77m 65kg")
        assert result["height_cm"] == 177
        assert result["weight_kg"] == 65

    def test_parse_refus(self):
        """L'utilisateur refuse de donner ses infos."""
        for answer in ["non", "plus tard", "non merci", "pas maintenant", "."]:
            assert _parse_details(answer) == {}, f"Échoué pour: {answer}"

    def test_parse_email_typo_gmail(self):
        """Correction des typos d'email."""
        result = _parse_details("test@gmial.com")
        assert result["email"] == "test@gmail.com"

    def test_parse_poids_invalide_ignore(self):
        """Un poids trop bas ou trop haut doit être ignoré."""
        assert "weight_kg" not in _parse_details("15kg")  # Trop léger
        assert "weight_kg" not in _parse_details("300kg")  # Trop lourd

    def test_parse_sexe_feminin(self):
        result = _parse_details("femme 30 ans")
        assert result["gender"] == "F"
```

**Vérification :**
```bash
python -m pytest tests/bot/test_details_parser.py -v
# Attendu : 6 tests passent
```

---

### Task 2.5 : Test — Sélecteur de concepts (mode fallback)

**Objectif :** Tester le fallback mot-clé (la partie la plus critique et déterministe du sélecteur).

**Créer :** `tests/engine/test_selector_fallback.py`

```python
"""Tests pour le fallback mot-clé du sélecteur."""
import pytest
from src.engine.selector import _keyword_fallback, _check_critical


class TestCriticalDetection:
    def test_douleur_detectee(self):
        result = _check_critical("j'ai mal au genou", {"sport": "cyclisme"})
        assert result is not None
        assert "blessures/cyclisme" in result

    def test_pas_de_douleur(self):
        result = _check_critical("comment progresser en vélo", {"sport": "cyclisme"})
        assert result is None

    def test_tendinite_running(self):
        result = _check_critical("j'ai une tendinite au tendon d'achille", {"sport": "running"})
        assert "blessures/running" in result


class TestKeywordFallback:
    def test_fatigue(self):
        result = _keyword_fallback("je suis crevé, pas en forme", {"level": 2})
        assert len(result["concepts"]) > 0
        assert "recuperation" in result["concepts"][0]

    def test_nutrition(self):
        result = _keyword_fallback("quoi manger avant une sortie longue", {"level": 2})
        assert any("nutrition" in c for c in result["concepts"])

    def test_motivation(self):
        result = _keyword_fallback("je suis démotivé, plus envie", {"level": 2})
        assert any("psychologie" in c for c in result["concepts"])

    def test_fallback_ultime(self):
        """Message qui ne match aucune règle → concepts par défaut."""
        result = _keyword_fallback("blablabla xyz", {"level": 1})
        assert len(result["concepts"]) == 2
        assert result["reasoning"].startswith("Fallback ultime")
```

**Vérification :**
```bash
python -m pytest tests/engine/test_selector_fallback.py -v
# Attendu : 7 tests passent
```

---

### Task 2.6 : Test — Prompt builder

**Créer :** `tests/engine/test_prompt_builder.py`

```python
"""Tests pour le prompt builder."""
import pytest
from src.engine.prompt_builder import build_system_prompt, _clean_footnotes


class TestPromptBuilder:
    def test_build_prompt_cycliste_intermediaire(self):
        selection = {
            "concepts": ["physiologie/systemes-energetiques", "planification/gestion-charge"],
            "level": 2,
            "reasoning": "test"
        }
        profile = {
            "name": "Florent", "sport": "cyclisme", "level": 2,
            "goal": "granfondo", "experience": "3 ans",
            "ctl": 80, "tsb": -5, "blessures": "genou gauche"
        }
        prompt = build_system_prompt(selection, profile)
        assert "Florent" in prompt
        assert "cyclisme" in prompt
        assert "granfondo" in prompt
        assert "CTL=80" in prompt
        assert "TSB=-5" in prompt
        assert "genou gauche" in prompt
        assert "SIGLES TECHNIQUES" in prompt  # Règle 5
        assert len(prompt) > 500

    def test_build_prompt_debutant(self):
        selection = {"concepts": ["seances/endurance-fondamentale"], "level": 1}
        profile = {"name": "Marie", "sport": "running", "level": 1, "goal": "10km", "experience": "0 ans"}
        prompt = build_system_prompt(selection, profile)
        assert "Débutant" in prompt or "débutant" in prompt.lower()
        assert "pédagogue" in prompt.lower()

    def test_build_prompt_tsb_bas(self):
        """TSB très négatif → règles de prudence."""
        selection = {"concepts": ["planification/gestion-charge"], "level": 2}
        profile = {"name": "Test", "sport": "cyclisme", "level": 2, "goal": "test", "experience": "1 an", "ctl": 100, "tsb": -25}
        prompt = build_system_prompt(selection, profile)
        assert "TSB < -20" in prompt or "privilégie la récupération" in prompt


class TestCleanFootnotes:
    def test_remove_footnotes(self):
        assert _clean_footnotes("Texte [^1] avec [^2] notes") == "Texte  avec  notes"

    def test_no_footnotes(self):
        assert _clean_footnotes("Texte sans notes") == "Texte sans notes"
```

**Vérification :**
```bash
python -m pytest tests/engine/test_prompt_builder.py -v
# Attendu : 4 tests passent
```

---

### Task 2.7 : Test — Knowledge loader

**Créer :** `tests/engine/test_knowledge.py`

```python
"""Tests pour le loader de connaissances."""
import pytest
from src.engine.knowledge import load_concept, get_all_concepts_for_selector, get_concept_by_id


class TestKnowledgeLoader:
    def test_all_concepts_exist(self):
        concepts = get_all_concepts_for_selector()
        assert len(concepts) >= 30

    def test_load_valid_concept(self):
        content = load_concept("physiologie/systemes-energetiques", 2)
        assert len(content) > 50
        assert not content.startswith("[Concept")

    def test_load_invalid_concept(self):
        content = load_concept("nonexistent/concept", 1)
        assert content.startswith("[Concept introuvable")

    def test_load_invalid_level(self):
        content = load_concept("physiologie/systemes-energetiques", 99)
        assert content.startswith("[Niveau")

    def test_get_concept_metadata(self):
        meta = get_concept_by_id("recuperation/sommeil")
        assert meta is not None
        assert "name" in meta
        assert "domain_name" in meta

    def test_all_domains_have_concepts(self):
        concepts = get_all_concepts_for_selector()
        domains = set(c["domain"] for c in concepts)
        assert len(domains) == 7
        expected = [
            "Physiologie de l'effort", "Planification & périodisation",
            "Séances types par filière énergétique", "Récupération & adaptation",
            "Blessures & prévention", "Nutrition sportive", "Psychologie & mental"
        ]
        for domain in expected:
            assert domain in domains, f"Domaine manquant: {domain}"
```

**Vérification :**
```bash
python -m pytest tests/engine/test_knowledge.py -v
# Attendu : 6 tests passent
```

---

### Task 2.8 : Ajouter retry avec backoff sur les appels LLM

**Objectif :** Si OpenRouter échoue (timeout, rate limit), réessayer avec backoff exponentiel.

**Modifier :** `src/engine/llm.py`

Remplacer le contenu existant par :

```python
"""Client LLM avec retry et circuit breaker."""
import asyncio
import logging
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from src.utils.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None
_failure_count: int = 0
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_RESET_SECONDS = 60


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
            max_retries=0,  # On gère les retries nous-mêmes
        )
    return _client


async def chat(
    messages: list[dict],
    max_retries: int = 2,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    """Envoie une conversation à DeepSeek avec retry + circuit breaker.

    Retry strategy:
    - Tentative 1: immédiate
    - Tentative 2: attendre 2s (backoff)
    - Tentative 3: attendre 4s (backoff)
    - Si circuit breaker ouvert (>5 échecs en 60s) → exception immédiate
    """
    global _failure_count

    if _failure_count >= CIRCUIT_BREAKER_THRESHOLD:
        raise RuntimeError(
            f"Circuit breaker ouvert ({_failure_count} échecs récents). "
            f"Réessaie dans {CIRCUIT_RESET_SECONDS}s."
        )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await get_client().chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _failure_count = 0  # Reset au succès
            return response.choices[0].message.content

        except RateLimitError as e:
            last_error = e
            _failure_count += 1
            wait = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(
                f"Rate limit OpenRouter (tentative {attempt+1}/{max_retries+1}), "
                f"attente {wait}s"
            )
            await asyncio.sleep(wait)

        except APITimeoutError as e:
            last_error = e
            _failure_count += 1
            wait = 2 ** attempt
            logger.warning(
                f"Timeout OpenRouter (tentative {attempt+1}/{max_retries+1}), "
                f"attente {wait}s"
            )
            await asyncio.sleep(wait)

        except APIError as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur API OpenRouter: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
            # Sinon, on sort de la boucle

        except Exception as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur inconnue OpenRouter: {e}", exc_info=True)
            raise  # Erreur inconnue = pas de retry

    # Toutes les tentatives ont échoué
    raise RuntimeError(
        f"Échec après {max_retries+1} tentatives. "
        f"Dernière erreur: {last_error}"
    )
```

**Vérification :**
```bash
cd ~/ai-sports-coach
python -c "from src.engine.llm import get_client; c = get_client(); print('Client OK:', c.base_url)"
```

---

### Task 2.9 : Tracker les tokens réels

**Objectif :** Extraire `usage` de la réponse LLM pour avoir des métriques réelles.

**Modifier :** `src/engine/llm.py` — modifier la fonction `chat` pour retourner aussi les tokens :

```python
async def chat_with_metrics(
    messages: list[dict],
    max_retries: int = 2,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> dict:
    """Comme chat() mais retourne {content, tokens_in, tokens_out, model}."""
    # ... [même logique de retry que chat()] ...
    response = await get_client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    _failure_count = 0
    usage = response.usage
    return {
        "content": response.choices[0].message.content,
        "tokens_in": usage.prompt_tokens if usage else 0,
        "tokens_out": usage.completion_tokens if usage else 0,
        "model": response.model,
    }


# Garder chat() pour compatibilité
async def chat(messages: list[dict], **kwargs) -> str:
    result = await chat_with_metrics(messages, **kwargs)
    return result["content"]
```

**Modifier :** `src/bot/handlers/chat.py` ligne ~217 — utiliser `chat_with_metrics` et sauvegarder les vrais tokens :

```python
# Avant (ligne 217) :
# response = await llm_chat(messages)

# Après :
from src.engine.llm import chat_with_metrics as llm_chat_with_metrics

result = await llm_chat_with_metrics(messages)
response = result["content"]

# Puis dans save_message (lignes 223-245), utiliser les vrais tokens :
# tokens_in=result["tokens_in"],
# tokens_out=result["tokens_out"],
```

---

### Task 2.10 : Lancer tous les tests

```bash
cd ~/ai-sports-coach
python -m pytest tests/ -v --tb=short
# Attendu : 31+ tests passent
```

---

## Phase 3 : Scalabilité (Webhooks + Infra) 🟡

### Task 3.1 : Installer FastAPI et uvicorn

```bash
cd ~/ai-sports-coach
pip install fastapi uvicorn
```

Ajouter à `pyproject.toml` :
```toml
"fastapi",
"uvicorn",
```

---

### Task 3.2 : Créer le serveur FastAPI avec webhook Telegram

**Créer :** `src/api/main.py`

```python
"""Serveur FastAPI — webhook Telegram + health check."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties

from src.utils.config import settings
from src.bot.handlers import start, chat

logger = logging.getLogger(__name__)

# Bot + Dispatcher globaux
bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode="Markdown"),
)
dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(chat.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup/teardown du webhook."""
    webhook_url = f"{settings.webhook_base_url}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook configuré: {webhook_url}")
    yield
    await bot.delete_webhook()
    logger.info("Webhook supprimé")


app = FastAPI(lifespan=lifespan, title="AI Sports Coach API")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint webhook Telegram."""
    try:
        update = types.Update.model_validate(await request.json())
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Erreur webhook: {e}", exc_info=True)
    return Response(status_code=200)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from src.db import check_connection
    db_status = check_connection()
    return {
        "status": "healthy" if db_status["ok"] else "degraded",
        "db": db_status,
        "users": db_status.get("users_count", 0),
    }
```

**Ajouter à :** `src/utils/config.py` le champ `webhook_base_url` :

```python
webhook_base_url: str = os.getenv("WEBHOOK_BASE_URL", "")
```

**Ajouter à :** `.env.example` :
```
WEBHOOK_BASE_URL=https://ton-domaine.com
```

---

### Task 3.3 : Mettre à jour le Dockerfile pour FastAPI

**Modifier :** `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Task 3.4 : Mettre à jour docker-compose.yml avec limites et healthcheck

**Modifier :** `docker-compose.yml`

```yaml
services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### Task 3.5 : Ajouter Traefik ou nginx comme reverse proxy (optionnel)

Pour la production, le webhook doit être accessible en HTTPS. Sur le VPS Hostinger, utiliser Traefik déjà en place.

**Ajouter les labels Traefik dans docker-compose.yml :**
```yaml
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ai-coach.rule=Host(`coach.ton-domaine.com`)"
      - "traefik.http.routers.ai-coach.entrypoints=websecure"
      - "traefik.http.routers.ai-coach.tls.certresolver=letsencrypt"
```

---

### Task 3.6 : Ajouter un script de déploiement

**Créer :** `scripts/deploy.sh`

```bash
#!/bin/bash
set -e
echo "🚀 Déploiement AI Sports Coach..."

cd "$(dirname "$0")/.."

# Vérifier qu'on n'a pas 2 instances
if pgrep -f "src.bot.main" > /dev/null 2>&1 || pgrep -f "src.api.main" > /dev/null 2>&1; then
    echo "⚠️  Instance existante détectée, arrêt..."
    docker compose stop 2>/dev/null || true
    pkill -f "src.bot.main" 2>/dev/null || true
    pkill -f "src.api.main" 2>/dev/null || true
    sleep 2
fi

# Tests
echo "🧪 Tests..."
python -m pytest tests/ -q --tb=short

# Build + déploiement
echo "🐳 Build Docker..."
docker compose build --no-cache

echo "🔄 Redémarrage..."
docker compose up -d

# Vérification
sleep 3
echo "📊 Status..."
docker compose ps
docker compose logs --tail=5

# Health check
echo "🏥 Health check..."
curl -s http://localhost:8000/health | python -m json.tool

echo "✅ Déploiement terminé !"
```

```bash
chmod +x ~/ai-sports-coach/scripts/deploy.sh
```

---

### Task 3.7 : Connection pooling Supabase

**Objectif :** Limiter le nombre de connexions concurrentes à Supabase.

**Modifier :** `src/db/__init__.py` — ajouter un pool config :

```python
from supabase import create_client, Client, ClientOptions

def get_supabase() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
            options=ClientOptions(
                postgrest_client_timeout=10,
                storage_client_timeout=10,
            ),
        )
    return _anon_client
```

---

### Task 3.8 : Ajouter un semaphore pour les appels DB concurrents

**Modifier :** `src/db/__init__.py` :

```python
import asyncio

_db_semaphore = asyncio.Semaphore(10)  # Max 10 appels DB concurrents

async def run_db(fn, *args, **kwargs):
    """Exécute une fonction DB synchrone avec semaphore."""
    async with _db_semaphore:
        return await asyncio.to_thread(fn, *args, **kwargs)
```

Puis dans `chat.py`, remplacer `asyncio.to_thread(get_or_create_user, ...)` par `run_db(get_or_create_user, ...)`.

---

## Phase 4 : Observabilité 🟡

### Task 4.1 : Installer structlog pour les logs structurés

```bash
pip install structlog
```

### Task 4.2 : Remplacer le logging standard par structlog

**Créer :** `src/utils/logging_setup.py`

```python
"""Configuration structlog pour AI Sports Coach."""
import structlog
import logging


def setup_logging():
    """Configure structlog avec sortie JSON pour la production."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()  # JSONRenderer() en prod
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # Réduire le bruit des logs externes
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
```

**Modifier :** `src/bot/main.py` — appeler `setup_logging()` au démarrage.

---

### Task 4.3 : Ajouter des métriques de coût par utilisateur

**Créer :** `src/engine/cost_tracker.py`

```python
"""Tracking des coûts LLM par utilisateur."""
from collections import defaultdict
import time

# Coût par million de tokens (prix OpenRouter mai 2026)
MODEL_COSTS_PER_M = {
    "deepseek/deepseek-v4-pro": {"input": 0.55, "output": 2.19},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
}

_user_costs: dict[int, float] = defaultdict(float)
_user_message_count: dict[int, int] = defaultdict(int)
_daily_reset: float = time.time()


def track_cost(telegram_id: int, model: str, tokens_in: int, tokens_out: int):
    """Enregistre le coût d'un appel LLM pour un utilisateur."""
    costs = MODEL_COSTS_PER_M.get(model, {"input": 0.55, "output": 2.19})
    cost_eur = (
        (tokens_in / 1_000_000) * costs["input"]
        + (tokens_out / 1_000_000) * costs["output"]
    )
    _user_costs[telegram_id] += cost_eur
    _user_message_count[telegram_id] += 1
    return cost_eur


def get_user_cost(telegram_id: int) -> dict:
    """Retourne les stats de coût pour un utilisateur."""
    return {
        "total_cost_eur": round(_user_costs.get(telegram_id, 0), 4),
        "message_count": _user_message_count.get(telegram_id, 0),
    }
```

---

### Task 4.4 : Ajouter un quota quotidien par utilisateur

**Modifier :** `src/bot/handlers/chat.py` — ajouter au début de `handle_message()` :

```python
from src.engine.cost_tracker import get_user_cost

# Vérifier le quota
costs = get_user_cost(user_id)
DAILY_COST_LIMIT = 0.50  # 50 centimes par jour max
if costs["total_cost_eur"] > DAILY_COST_LIMIT:
    await message.answer(
        "Tu as atteint ta limite de coaching pour aujourd'hui 🔄 "
        "Reviens demain pour continuer !"
    )
    return
```

---

### Task 4.5 : Ajouter l'endpoint /metrics

**Ajouter à :** `src/api/main.py` :

```python
@app.get("/metrics")
async def metrics():
    """Endpoint de métriques pour le monitoring."""
    from src.engine.cost_tracker import _user_costs, _user_message_count
    return {
        "active_users": len(_user_message_count),
        "total_cost_eur": round(sum(_user_costs.values()), 2),
        "top_users_by_cost": sorted(
            [{"id": uid, "cost": round(c, 4)} for uid, c in _user_costs.items()],
            key=lambda x: x["cost"], reverse=True
        )[:10],
    }
```

---

### Task 4.6 : Ajouter une alerte quand OpenRouter est down

**Créer un cron job Hermes** (après le déploiement) pour ping le health check toutes les 5 minutes :

```python
# Via le cronjob tool :
cronjob(
    action="create",
    name="ai-coach-health-check",
    schedule="*/5 * * * *",
    prompt="Vérifie la santé du bot AI Sports Coach : curl -s http://localhost:8000/health. Si le status n'est pas 'healthy', alerte immédiatement via send_message.",
    deliver="telegram:1552465326",
    enabled_toolsets=["terminal", "web"],
    no_agent=False,
)
```

---

## Phase 5 : Qualité du Coaching 🟢

### Task 5.1 : Ajouter un système de feedback 👍/👎

**Objectif :** Permettre aux utilisateurs de donner un feedback sur les réponses du coach.

**Créer :** `src/bot/handlers/feedback.py`

```python
from aiogram import Router, types
from aiogram.filters import Command
from src.db.sessions import save_feedback  # À créer

router = Router(name="feedback")

@router.message(Command("feedback"))
async def cmd_feedback(message: types.Message):
    """Guide l'utilisateur pour donner son feedback."""
    await message.answer(
        "Comment évalues-tu ma dernière réponse ?\n"
        "👍 — Utile et pertinent\n"
        "👎 — Pas utile ou incorrect"
    )
```

Puis ajouter le router dans `main.py`.

---

### Task 5.2 : Étoffer le contenu des connaissances (couches fines)

**Objectif :** Certains concepts n'ont que 6 lignes par couche. Viser 15-25 lignes minimum.

**Priorité :**
1. `planification/modeles-periodisation` (layer1: 7-12 = 6 lignes) → viser 15+
2. `planification/gestion-charge` (layer1: 29-33 = 5 lignes) → viser 15+
3. `seances/endurance-fondamentale` (layer1: 7-10 = 4 lignes) → viser 15+

Pour chaque concept :
- Ajouter 1-2 paragraphes d'explication concrète
- Ajouter 1 exemple pratique
- Ajouter 1 piège/misconception à éviter

---

### Task 5.3 : Uniformiser le format des fichiers de connaissance

**Problème :** Certains fichiers commencent par `# Titre H1`, d'autres directement par `##`. À uniformiser.

```bash
cd ~/ai-sports-coach/knowledge/domains
# Vérifier le format du header
for f in *.md; do echo "=== $f ==="; head -3 "$f"; echo; done
```

Tous les fichiers doivent commencer par :
```markdown
# Titre du Domaine

## 1. Concepts Fondamentaux (Modèle à 3 Couches)
```

---

### Task 5.4 : Résoudre les doublons nutrition

**Problème :** La nutrition apparaît dans deux endroits :
- `recuperation-adaptation.md` §1.2 — Nutrition de récupération
- `nutrition-sportive.md` — Domaine dédié

Ces contenus se chevauchent partiellement. À fusionner ou créer des renvois clairs.

---

### Task 5.5 : Ajouter un message d'accueil avec mention de confidentialité

**Modifier :** `src/bot/handlers/start.py` — ajouter après le message onboarding :

```python
# Mention RGPD dans le message onboarding
(
    f"...\n\n"
    f"🔒 *Confidentialité* : Tes données d'entraînement restent privées. "
    f"Pas de revente, pas de partage. Conformément au RGPD, tu peux demander "
    f"l'accès ou la suppression de tes données à tout moment (/rgpd)."
)
```

---

## Phase 6 : Préparation Lancement 🟢

### Task 6.1 : Écrire le plan de rollback

**Créer :** `docs/rollback.md`

```markdown
# Procédure de Rollback

## En cas de problème post-déploiement

```bash
cd ~/ai-sports-coach

# 1. Revenir au commit précédent
git log --oneline -3  # Trouver le commit stable
git revert <commit-id>

# 2. Redéployer la version stable
docker compose down
docker compose up -d --build

# 3. Vérifier
curl http://localhost:8000/health
docker compose logs --tail=20
```

## Contacts d'urgence
- OpenRouter status : https://status.openrouter.ai
- Supabase status : https://status.supabase.com
- Support VPS Hostinger : tableau de bord Hostinger
```

---

### Task 6.2 : Ajouter un fichier CHANGELOG.md

```markdown
# Changelog

## [0.2.0] — 2026-05-14

### Added
- Tests unitaires (parser onboarding, sélecteur, prompt builder, knowledge loader)
- Retry + circuit breaker sur les appels OpenRouter
- Tracking des tokens et coûts réels
- Endpoint /health et /metrics
- FastAPI avec webhooks Telegram

### Changed
- Passage du polling aux webhooks
- Docker avec limites de ressources et healthcheck
- Logging structuré (structlog)

### Fixed
- Tous les fichiers non versionnés commités
- .gitignore mis à jour

## [0.1.0] — 2026-05-13

### Added
- Bot MVP avec onboarding et chat
- Pipeline LLM 2 étages (sélecteur + coach)
- Base connaissances (30 concepts, 7 domaines)
- Schéma Supabase + RLS
```

---

### Task 6.3 : Checklist pre-lancement

**Créer :** `docs/pre-launch-checklist.md`

```markdown
# Checklist Pre-Lancement

## Tests
- [ ] `pytest tests/ -v` → tous les tests passent
- [ ] Test manuel du bot Telegram avec un vrai compte
- [ ] Test onboarding complet (6 questions + détails)
- [ ] Test question coaching (3 échanges minimum)
- [ ] Test détection douleur (critical path)

## Infrastructure
- [ ] Docker build + up sans erreur
- [ ] `curl /health` retourne `{"status": "healthy"}`
- [ ] `curl /metrics` retourne des métriques
- [ ] Webhook HTTPS accessible depuis internet
- [ ] Logs visibles (`docker compose logs`)

## Base de données
- [ ] `check_connection()` retourne OK
- [ ] RLS fonctionnel (tester isolation entre 2 utilisateurs)
- [ ] Backup Supabase activé (dashboard Supabase)

## Coûts
- [ ] Quota quotidien par utilisateur configuré
- [ ] Budget OpenRouter défini + alerte activée
- [ ] Prix estimé par utilisateur/mois documenté

## Sécurité
- [ ] `.env` jamais dans git (vérifié)
- [ ] HTTPS actif sur le webhook
- [ ] RLS testé (utilisateur A ne voit pas données utilisateur B)
- [ ] Mention RGPD dans le message d'accueil

## Monitoring
- [ ] Health check cron job actif (toutes les 5 min)
- [ ] Alertes configurées si /health != healthy
```

---

### Task 6.4 : Tests d'intégration — scénario complet

**Créer :** `tests/integration/test_full_flow.py`

```python
"""Test d'intégration du flux complet (hors LLM réel)."""
import pytest
from src.engine.selector import _keyword_fallback
from src.engine.prompt_builder import build_system_prompt
from src.engine.knowledge import load_concept


@pytest.mark.integration
class TestFullFlow:
    """Simule un échange complet (avec fallback, pas de vrai LLM)."""

    def test_question_entrainement(self):
        """Flow : message → sélecteur → prompt builder."""
        message = "Je veux progresser en vélo, comment organiser mes semaines ?"
        profile = {
            "name": "Florent", "sport": "cyclisme", "level": 2,
            "goal": "granfondo", "experience": "3 ans",
            "ctl": 80, "tsb": -5
        }

        # Étape 1 : Sélecteur (fallback)
        selection = _keyword_fallback(message, profile)
        assert len(selection["concepts"]) > 0

        # Étape 2 : Prompt builder
        prompt = build_system_prompt(selection, profile)
        assert len(prompt) > 500
        assert "Florent" in prompt
        assert "cyclisme" in prompt

        # Étape 3 : Vérifier que les connaissances se chargent
        for concept_id in selection["concepts"]:
            content = load_concept(concept_id, selection["level"])
            assert not content.startswith("[Concept"), f"Échec chargement: {concept_id}"
```

---

## Récapitulatif

| Phase | Tâches | Temps estimé | Impact |
|-------|--------|-------------|--------|
| 1. Sauvegarde | 6 | 15 min | 🛡️ Perte de données |
| 2. Fondations | 10 | 2-3h | 🧪 Stabilité |
| 3. Scalabilité | 8 | 3-4h | 📈 Performance |
| 4. Observabilité | 6 | 1-2h | 👁️ Visibilité |
| 5. Qualité | 5 | 2-3h | 💬 Expérience |
| 6. Lancement | 4 | 1h | 🚀 Production |
| **Total** | **39** | **~12h** | |

---

## Prochaine étape

Après validation de ce plan, l'exécution se fait via `subagent-driven-development` — un subagent frais par tâche avec review en 2 étapes (spec compliance + code quality).

**Prêt à exécuter ? Commande : "Exécute la Phase 1"**
