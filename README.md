# postoaklabs.com

Source for the **Post Oak Labs** website — a static HTML site for a specialist
consulting firm in tokenized payment infrastructure, stablecoin strategy, CBDC
integration, and institutional blockchain advisory.

The site is hand-authored static HTML (no build step, no framework). This repo
adds version control and an automated deploy pipeline to DreamHost.

---

## How deployment works

Every push to `main` runs the [`Deploy postoaklabs.com`](.github/workflows/deploy.yml)
workflow:

1. **Validate** — checks HTML and internal links (see *Validation gates* below).
2. **Deploy** — if validation passes, the site is published to DreamHost over
   SSH with `rsync`.

| Trigger | What happens |
|---|---|
| Push to `main` | Validate, then deploy |
| Pull request to `main` | Validate only — no deploy |
| Manual run (Actions tab -> *Run workflow*) | Validate, then deploy |

The deploy step **only adds and overwrites files** — it never deletes anything
already on the server (`rsync` runs without `--delete`), so assets that live on
the server but not in this repo are left untouched.

---

## Repository layout

Tracked in this repo (this is the deployable website):

```
*.html                 18 site pages (index, a2a-*, example-*, faq, glossary, …)
demos/                 Interactive demo pages (live at postoaklabs.com/demos/)
sitemap.xml            XML sitemap
sitemap.html           Human-readable sitemap page
robots.txt             Crawler directives
llms.txt               LLM-readable site summary
manifest.json          PWA-lite web app manifest
.htaccess              Apache config — HTTPS, 301 redirects, security headers
.github/               CI workflow + the link-checker script
.htmlvalidate.json     HTML validation ruleset
.deployignore          Paths rsync excludes from the DreamHost upload
```

Deliberately **not** tracked (kept local via [`.gitignore`](.gitignore)) —
internal material that is not part of the public website:

- Internal working docs (`*.md` audit reports, handover notes, deploy logs)
- `Partners/` — source for the separate-domain partner sites
- `address-forge/` — a standalone Python project
- `erratatoolsatainumbers/`, `toolsnowatainumbers/` — historical tool archives
- `_archive_pre_sweep_2026-05-11/` — a rollback snapshot

These files stay in the working folder untouched; git simply does not track them.

---

## Deployment setup (one-time)

The deploy job authenticates to DreamHost with an SSH key. Set this up once.

### 1. Enable shell access on the DreamHost user

In the DreamHost panel: **Websites -> Manage Users -> edit the user -> set the
account type to "Shell".** `rsync` needs SSH/shell access (SFTP-only will not
work).

### 2. Generate a deploy key pair

On any machine:

```bash
ssh-keygen -t ed25519 -f dreamhost_deploy -C "github-actions-deploy" -N ""
```

This produces `dreamhost_deploy` (private key) and `dreamhost_deploy.pub`
(public key).

### 3. Add the public key to DreamHost

Append the contents of `dreamhost_deploy.pub` to `~/.ssh/authorized_keys` on the
DreamHost server (or paste it into the SSH-key field for the user in the panel).

### 4. Add four repository secrets

In GitHub: **Settings -> Secrets and variables -> Actions -> New repository
secret.** Add:

| Secret | Value |
|---|---|
| `DREAMHOST_SSH_KEY` | The full contents of the **private** key file `dreamhost_deploy` |
| `DREAMHOST_HOST` | The DreamHost server hostname (Panel -> Manage Users shows it, e.g. `iad1-shared-xxxxx.dreamhost.com`) |
| `DREAMHOST_USER` | The DreamHost shell username |
| `DREAMHOST_PATH` | Absolute path to the web root, e.g. `/home/USERNAME/postoaklabs.com` |

Once the secrets exist, the next push to `main` deploys automatically. If a
secret is missing, the deploy job fails early with a clear message.

---

## Editing the site

```bash
# edit HTML files locally, then:
git add -A
git commit -m "Describe the change"
git push origin main
```

The push triggers validation and, on success, deployment. Watch progress in the
repo's **Actions** tab.

To preview locally, open the `.html` files directly in a browser, or serve the
folder: `python3 -m http.server`.

---

## Validation gates

Both checks run before every deploy and must pass.

**HTML validation** — [`html-validate`](https://html-validate.org/) with the
ruleset in [`.htmlvalidate.json`](.htmlvalidate.json). The ruleset is
intentionally tight: it errors only on genuinely broken markup (mismatched or
stray tags, duplicate `id`/attributes) and warns on questionable element
nesting. It is not a style or accessibility linter.

**Internal links** — [`.github/scripts/check-links.py`](.github/scripts/check-links.py)
verifies every internal `href`/`src` resolves to a real file. External links are
listed but never fail the build.

Run them locally before pushing:

```bash
npx --yes html-validate@11 "**/*.html"
python3 .github/scripts/check-links.py
```

### Known pending links

The link checker maintains a `KNOWN_PENDING` set in
[`.github/scripts/check-links.py`](.github/scripts/check-links.py) for links
that are intentionally suppressed so the gate stays green while a content or
asset decision is pending. Each entry has an inline comment explaining why it
is suppressed.

**Current suppressions:**

| Target | Reason |
|---|---|
| `favicon.svg`, `favicon.ico`, `favicon-32.png`, `favicon-64.png` | Favicon assets exist on the live DreamHost server but are not committed to the repo. Confirm they are present and add them, then remove these entries. |
| `pilot-framework.pdf` | Linked from `a2a-engagement-roadmap.html`; the PDF does not exist in the repo yet. |
| `meridian-capital-advisory.html` | Old partner page that 301-redirects via `.htaccess` to `https://meridiancapital.me/`. Better to link directly. |

To add a new suppression: append the bare path string (e.g. `"my-missing-file.pdf"`) to the `KNOWN_PENDING` set and add a comment explaining the pending decision. To resolve a suppression: fix the underlying issue (add the file, update the link, or remove the reference), then delete the `KNOWN_PENDING` entry.

---

## Manual deploy fallback

If GitHub Actions is unavailable, the site can still be uploaded by hand: copy
everything except the paths listed in [`.deployignore`](.deployignore) to the
DreamHost web root via the file manager or any SFTP client.

---

&copy; Post Oak Labs. All rights reserved.
