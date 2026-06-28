# Model Alive — Master TODO (Class-Leading)

> Goal: En kusursuz LLM model lifecycle pre-flight ürünü.
> Rule: Her phase bitmeden sonrakine geçme. Her madde CI'da test edilebilir olmalı.

---

## PHASE 0 — SHIP WHAT WE HAVE (BLOCKER) 🔴

- [ ] **0.1** Commit all local v0.3.0 changes
- [ ] **0.2** Push to GitHub `main`
- [ ] **0.3** Publish PyPI `0.3.0`
- [ ] **0.4** GitHub Release `v0.3.0` + tag
- [ ] **0.5** PyPI README / project links doğrula
- [ ] **0.6** `pip install modelalive` smoke test (fresh venv)
- [ ] **0.7** GitHub Action `Ahaozandaburada/modelalive@v0.3.0` test workflow

---

## PHASE 1 — REGISTRY: TAM KAPSAM & DOĞRULUK 🟠

### 1A — Provider tam liste
- [ ] **1.1** Anthropic: resmi deprecation tablosunun %100'ü (active + retired + deprecated)
- [ ] **1.2** OpenAI: deprecations sayfasının tamamı (50+ model)
- [ ] **1.3** Google: Gemini deprecations tam tablo (embedding, imagen, veo dahil)
- [ ] **1.4** Groq: model list + deprecation (varsa)
- [ ] **1.5** Mistral: model retirement docs
- [ ] **1.6** AWS Bedrock: model ID mapping (Anthropic/OpenAI farklı isimler)
- [ ] **1.7** Azure OpenAI: deployment name vs model ID mapping
- [ ] **1.8** Together / Fireworks / Cerebras — top 3 aggregator

### 1B — Alias & platform mapping
- [ ] **1.9** `aliases` genişlet: `-latest`, `-preview`, dated snapshot alias'ları
- [ ] **1.10** Bedrock model ID → canonical API ID crosswalk
- [ ] **1.11** OpenRouter model slug → provider canonical ID
- [ ] **1.12** Fine-tuned prefix: `ft:`, `ft:gpt-4o-mini:...` normalize kuralları
- [ ] **1.13** Organization-scoped model IDs (OpenAI project models)

### 1C — Otomasyon & doğruluk
- [ ] **1.14** `scripts/refresh_sources.py` → otomatik scrape + diff PR (sadece checked_at değil)
- [ ] **1.15** Anthropic doc parser (tablo → JSON)
- [ ] **1.16** OpenAI doc parser
- [ ] **1.17** Google doc parser
- [ ] **1.18** CI: live doc vs registry diff fail (drift detection)
- [ ] **1.19** Her model kaydına `announcement_date`, `verified_by` alanı
- [ ] **1.20** Public `registry/CHANGELOG.md` — her model değişikliği loglanır
- [ ] **1.21** Replacement zinciri: otomatik graph validation (DAG, cycle yok)
- [ ] **1.22** `status: deprecated` + geçmiş `retired_at` → CI auto-fail (zaten var, genişlet)

---

## PHASE 2 — CORE SDK: KUSURSUZ DEVELOPER UX 🟠

### 2A — Python SDK
- [ ] **2.1** `ensure()` — production default; dokümante et
- [ ] **2.2** `resolve()` — multi-hop + breaking_changes merge hedef modelden
- [ ] **2.3** `strict_unknown=True` default via env `MODELALIVE_STRICT=1`
- [ ] **2.4** `warn_days=7` — N gün içinde ölecek modellerde uyar/raise
- [ ] **2.5** `ModelExpiringSoonError` exception
- [ ] **2.6** Context manager: `with modelalive.gate("model-id") as safe_id:`
- [ ] **2.7** Decorator: `@modelalive.require_alive("model-id")`
- [ ] **2.8** TypedDict / Protocol for AliveResult (IDE autocomplete)
- [ ] **2.9** `py.typed` marker (PEP 561)
- [ ] **2.10** Remote registry URL override (`MODELALIVE_REGISTRY_URL`)

### 2B — Multi-language SDK
- [ ] **2.11** `npm install modelalive` — TypeScript SDK
- [ ] **2.12** Go module `github.com/.../modelalive`
- [ ] **2.13** Rust crate (opsiyonel, agent ecosystem için)
- [ ] **2.14** OpenAPI spec → auto-generate clients

### 2C — Integration helpers
- [ ] **2.15** LangChain callback / wrapper
- [ ] **2.16** OpenAI Python SDK pre-hook örneği
- [ ] **2.17** Anthropic Python SDK pre-hook örneği
- [ ] **2.18** LiteLLM integration patch veya plugin
- [ ] **2.19** Bifrost / gateway middleware örneği

---

## PHASE 3 — HTTP API: CLASS STANDARD 🟡

- [ ] **3.1** OpenAPI 3.1 spec export (`/openapi.json`)
- [ ] **3.2** `GET /v1/alive` — response headers: `X-Model-Status`, `X-Replacement`
- [ ] **3.3** `POST /v1/ensure` (body + query)
- [ ] **3.4** `GET /v1/expiring?days=30` — yakında ölecek modeller
- [ ] **3.5** `GET /v1/models/{id}` — tek model detay
- [ ] **3.6** ETag / If-None-Match caching (registry version hash)
- [ ] **3.7** Rate limiting middleware (self-host config)
- [ ] **3.8** Request ID tracing
- [ ] **3.9** Structured JSON error schema (RFC 7807 problem+json)
- [ ] **3.10** API version negotiation (`Accept-Version: v1`)
- [ ] **3.11** Webhook: "model expiring in N days" subscription (design)
- [ ] **3.12** Hosted deploy (Fly.io) — **para katmanından önce bile public endpoint**
- [ ] **3.13** Status page (status.modelalive.dev)
- [ ] **3.14** Health: registry age warning if >7 days stale

---

## PHASE 4 — CI/CD & GÜVEN GATE 🟡

- [ ] **4.1** GitHub Action v1 — pin version, strict-unknown default option
- [ ] **4.2** GitHub Action: `models-from-env` (MODEL_ID env)
- [ ] **4.3** GitHub Action: matrix — check all models in config file
- [ ] **4.4** `modelalive scan` — repo içinde hardcoded model ID tara (grep + AST)
- [ ] **4.5** Pre-commit hook (`pre-commit-config.yaml`)
- [ ] **4.6** GitLab CI template
- [ ] **4.7** CircleCI orb
- [ ] **4.8** `modelalive.toml` config — projede kullanılan model listesi
- [ ] **4.9** Dependabot-style PR: "your config uses retired model X"
- [ ] **4.10** SBOM / lockfile integration (which models in prod)

---

## PHASE 5 — TEST & KALITE 🟡

- [ ] **5.1** 50+ unit tests (şu an 24)
- [ ] **5.2** Property-based tests (Hypothesis) — random model IDs, dates
- [ ] **5.3** Registry snapshot golden files
- [ ] **5.4** Live doc integration tests (mark nightly, not PR)
- [ ] **5.5** API contract tests (schemathesis)
- [ ] **5.6** Performance: 10K check/s benchmark
- [ ] **5.7** Memory: registry load <5ms cached
- [ ] **5.8** Fuzz: malformed model IDs, unicode, injection
- [ ] **5.9** Coverage ≥95%
- [ ] **5.10** mypy strict mode clean

---

## PHASE 6 — DOKÜMANTASYON & TRUST 🟢

- [ ] **6.1** docs.modelalive.dev (MkDocs / Docusaurus)
- [ ] **6.2** Quickstart: 60 saniyede çalışır
- [ ] **6.3** "Accuracy policy" sayfası — yanlış bilgi prosedürü
- [ ] **6.4** Provider contribution guide
- [ ] **6.5** Model ekleme PR template
- [ ] **6.6** Comparison page: vs Bifrost alias, vs provider docs, vs language-models npm
- [ ] **6.7** Security.md + responsible disclosure
- [ ] **6.8** SOC2-ready data handling doc (hosted API için)

---

## PHASE 7 — DAĞITIM & MARKA 🟢

- [ ] **7.1** Domain: modelalive.dev
- [ ] **7.2** GitHub org: `modelalive/modelalive` (transfer)
- [ ] **7.3** Hacker News launch post
- [ ] **7.4** Twitter/X thread — June 2026 deprecation wave
- [ ] **7.5** Anthropic/OpenAI community forum post
- [ ] **7.6** "Awesome modelalive" integrations list
- [ ] **7.7** PyPI + npm download badges
- [ ] **7.8** Logo + brand identity

---

## PHASE 8 — MONETIZATION (SONRA) ⚪

- [ ] **8.1** Hosted API tier: free 100/mo, pay-per-check
- [ ] **8.2** API keys + Stripe
- [ ] **8.3** x402 micropayment
- [ ] **8.4** Enterprise SLA + private registry
- [ ] **8.5** Webhook alerts ($/ay)

---

## DEFINITION OF DONE — "KLASMANIN EN İYİSİ"

Ürün ancak şu 10 kriterin **hepsi** sağlandığında "kusursuz" sayılır:

1. ✅ 3 major provider %95+ model coverage
2. ✅ Registry drift CI — doc değişince otomatik PR
3. ✅ `ensure()` + `scan` + GitHub Action — zero-config CI gate
4. ✅ Python + TypeScript SDK, typed, py.typed
5. ✅ Public hosted API + OpenAPI + status page
6. ✅ 50+ tests, 95% coverage, nightly live doc check
7. ✅ `<24 saat` deprecation announcement → registry update SLA
8. ✅ Accuracy policy + public changelog
9. ✅ LangChain / LiteLLM / OpenAI SDK integration examples
10. ✅ Dünya `pip install` ve `api.modelalive.dev` ile erişebilir

---

## ŞİMDİ NE YAPILIYOR (sıra)

```
PHASE 0 (bugün)  → PHASE 1A (3 gün) → PHASE 2A (2 gün) → PHASE 4 (1 gün) → PHASE 3 (2 gün)
```

Hosted API + para = Phase 8 (Phase 0–5 bitince).
