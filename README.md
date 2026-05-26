# postoaklabs.com

[![Deploy postoaklabs.com](https://github.com/PostOakLabs/postoaklabs/actions/workflows/deploy.yml/badge.svg)](https://github.com/PostOakLabs/postoaklabs/actions/workflows/deploy.yml)

Source for **[postoaklabs.com](https://postoaklabs.com)** — institutional advisory and interactive intelligence tools for payments engineers, treasury teams, and compliance professionals.

`🏛️ Institutional Advisory` &nbsp;`⛓️ Blockchain & DLT` &nbsp;`💳 A2A Payments` &nbsp;`📡 Zero APIs` &nbsp;`💻 Static HTML`

---

## What's on the site

- **A2A payment infrastructure** — strategy, workflow, rail comparison, ISO 20022 integration, and TMMF settlement modeling
- **Enterprise blockchain advisory** — architecture guidance and worked examples across Besu, Canton, Corda, and Hyperledger Fabric
- **Stablecoin & CBDC strategy** — MiCA / GENIUS Act issuer readiness, tokenized RWA compliance, cross-border settlement
- **Regulatory intelligence** — DORA, Basel IV, FAPI, CFPB 1033, EU AI Act, FATF sanctions, KYB/AML, VASP Travel Rule
- **Agentic payment policy (AP2)** — mandate builder, guardrail designer, BaaS infrastructure policy, AML rule builder
- **Interactive demos** — 35+ browser-based tools covering FX netting, fraud risk, nostro optimization, embedded lending, VRP sweep logic, and more

---

## Repository layout

```
postoaklabs/
├── index.html              ← Homepage
├── *.html                  ← Site pages (A2A, blockchain, advisory, glossary, …)
├── demos/                  ← 35+ self-contained interactive tools
├── sitemap.xml             ← XML sitemap
├── robots.txt              ← Crawler directives
├── llms.txt                ← LLM-readable site summary
├── manifest.json           ← PWA manifest
├── .htaccess               ← HTTPS, 301 redirects, security headers
├── .github/                ← CI workflow + link-checker script
├── .htmlvalidate.json      ← HTML validation ruleset
└── .deployignore           ← Paths excluded from DreamHost upload
```

---

## Deploy pipeline

Every push to `main` validates and deploys automatically.

| Trigger | Result |
|---|---|
| Push to `main` | Validate → deploy |
| Pull request to `main` | Validate only |
| Manual run (Actions → *Run workflow*) | Validate → deploy |

Steps: secrets check → SSH key install → connectivity test → rsync dry run → rsync live deploy → smoke test.

The deploy is additive only (`rsync` without `--delete`) — files on the server but absent from this repo are left untouched.

---

## Editing the site

```bash
# Edit files, then:
git add -A
git commit -m "describe the change"
git push origin main
```

Preview locally: open `.html` files in a browser, or `python3 -m http.server`.

---

## Validation

Both checks run before every deploy and must pass.

**HTML** — [`html-validate`](https://html-validate.org/) with the ruleset in [`.htmlvalidate.json`](.htmlvalidate.json). Errors on broken markup only; not a style or accessibility linter.

**Internal links** — [`.github/scripts/check-links.py`](.github/scripts/check-links.py) verifies every internal `href`/`src` resolves to a real file. External links are listed but never fail the build.

Run locally:

```bash
npx --yes html-validate@9 "**/*.html"
python3 .github/scripts/check-links.py
```

---

## One-time deployment setup

<details>
<summary>Expand for SSH key + DreamHost secret configuration</summary>

### 1. Enable shell access on the DreamHost user

In the DreamHost panel: **Websites → Manage Users → edit the user → set account type to "Shell".**
rsync requires SSH/shell access — SFTP-only will not work.

### 2. Generate a deploy key pair

```bash
ssh-keygen -t ed25519 -f dreamhost_deploy -C "github-actions-deploy" -N ""
```

### 3. Add the public key to DreamHost

Append `dreamhost_deploy.pub` to `~/.ssh/authorized_keys` on the server, or paste it into the SSH-key field in the panel.

### 4. Add five repository secrets

**Settings → Secrets and variables → Actions → New repository secret:**

| Secret | Value |
|---|---|
| `DH_SSH_KEY` | Full contents of the private key file `dreamhost_deploy` |
| `DH_SSH_USER` | DreamHost shell username |
| `DH_SSH_HOST` | DreamHost server hostname (visible in panel under Manage Users) |
| `DH_WEB_ROOT` | Absolute path to the web root, e.g. `/home/USERNAME/postoaklabs.com` |
| `DH_SITE_URL` | Full site URL, e.g. `https://postoaklabs.com` |

Once secrets exist, the next push to `main` deploys automatically.

### Manual deploy fallback

If GitHub Actions is unavailable, upload everything except paths in [`.deployignore`](.deployignore) to the DreamHost web root via any SFTP client.

</details>

---

## Links

- [postoaklabs.com](https://postoaklabs.com) — live site
- [Post Oak Labs](https://postoaklabs.com) — institutional advisory
- [AINumbers.co](https://ainumbers.co) — fintech intelligence suite (sister property)

---

&copy; Post Oak Labs. All rights reserved.
