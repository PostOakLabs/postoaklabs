# postoaklabs.com

[![Deploy postoaklabs.com](https://github.com/PostOakLabs/postoaklabs/actions/workflows/deploy.yml/badge.svg)](https://github.com/PostOakLabs/postoaklabs/actions/workflows/deploy.yml)

Source for **[postoaklabs.com](https://postoaklabs.com)** — the website for Post Oak Labs, a specialist advisory firm in tokenized payment infrastructure, stablecoin strategy, CBDC integration, and institutional blockchain.

Hand-authored static HTML. No build step, no framework, no JavaScript dependencies.

---

## Deployment

Every push to `main` validates and deploys automatically via GitHub Actions.

| Trigger | Result |
|---|---|
| Push to `main` | Validate → deploy |
| Pull request to `main` | Validate only |
| Manual run (Actions → *Run workflow*) | Validate → deploy |

The deploy step is additive only (`rsync` without `--delete`) — files on the server but not in this repo are left untouched.

---

## Repository layout

```
*.html                 Site pages
demos/                 Interactive demo pages
sitemap.xml            XML sitemap
sitemap.html           Human-readable sitemap
robots.txt             Crawler directives
llms.txt               LLM-readable site summary
manifest.json          PWA manifest
.htaccess              Apache config — HTTPS, redirects, security headers
.github/               CI workflow + link-checker script
.htmlvalidate.json     HTML validation ruleset
.deployignore          Paths excluded from the DreamHost upload
```

---

## One-time deployment setup

The pipeline authenticates to DreamHost with an SSH key. Do this once per repo.

### 1. Enable shell access on the DreamHost user

In the DreamHost panel: **Websites → Manage Users → edit the user → set account type to "Shell".**
rsync requires SSH/shell access — SFTP-only will not work.

### 2. Generate a deploy key pair

```bash
ssh-keygen -t ed25519 -f dreamhost_deploy -C "github-actions-deploy" -N ""
```

This produces `dreamhost_deploy` (private key) and `dreamhost_deploy.pub` (public key).

### 3. Add the public key to DreamHost

Append `dreamhost_deploy.pub` to `~/.ssh/authorized_keys` on the DreamHost server, or paste it into the SSH-key field in the panel.

### 4. Add five repository secrets

**Settings → Secrets and variables → Actions → New repository secret:**

| Secret | Value |
|---|---|
| `DH_SSH_KEY` | Full contents of the private key file `dreamhost_deploy` |
| `DH_SSH_USER` | DreamHost shell username |
| `DH_SSH_HOST` | DreamHost server hostname (visible in panel under Manage Users) |
| `DH_WEB_ROOT` | Absolute path to the web root, e.g. `/home/USERNAME/postoaklabs.com` |
| `DH_SITE_URL` | Full site URL, e.g. `https://postoaklabs.com` |

Once secrets exist, the next push to `main` deploys automatically. If a secret is missing the deploy job fails early with a clear error message.

---

## Editing the site

```bash
# Edit HTML files, then:
git add -A
git commit -m "describe the change"
git push origin main
```

To preview locally: open `.html` files directly in a browser, or `python3 -m http.server`.

---

## Validation

Both checks run before every deploy and must pass.

**HTML validation** — [`html-validate`](https://html-validate.org/) with the ruleset in [`.htmlvalidate.json`](.htmlvalidate.json). Errors on broken markup only (mismatched tags, duplicate IDs); not a style or accessibility linter.

**Internal links** — [`.github/scripts/check-links.py`](.github/scripts/check-links.py) verifies every internal `href`/`src` resolves to a real file. External links are listed but never fail the build.

Run locally before pushing:

```bash
npx --yes html-validate@9 "**/*.html"
python3 .github/scripts/check-links.py
```

---

## Manual deploy fallback

If GitHub Actions is unavailable, upload everything except paths listed in [`.deployignore`](.deployignore) to the DreamHost web root via the file manager or any SFTP client.

---

&copy; Post Oak Labs. All rights reserved.
