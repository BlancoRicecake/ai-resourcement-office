# AI Resourcement Office

AI Resourcement Office is a download-first directory for AI worker packages.

- Web directory: https://aigent-office.com/
- Repository: https://github.com/BlancoRicecake/ai-resourcement-office

The project does not host or run agents for users. It shares reusable packages
that help users set up AI workers in their own environment with their own API
keys, tools, cloud accounts, and security policies.

## v0.1 Goal

- Publish a simple web directory for AI worker packages.
- Define a repeatable bundle standard.
- Start with 4 seed workers:
  - Review Analysis Worker
  - SEO/GEO Brief Worker
  - Proposal Draft Worker
  - Legal Docs Draft Worker

## Core Principle

AI Resourcement Office provides setup packages, not hosted execution.

Users are responsible for:

- Local setup
- API keys
- Model usage fees
- Cloud/server fees
- MCP permissions
- Security review
- Output verification

## Project Structure

```txt
docs/
  Strategy and operating standards

site/
  Static web MVP

templates/
  Reusable bundle package templates

seed-bundles/
  v0.1 seed worker and bundle specifications
```

## Open the Web MVP

Open `site/index.html` in a browser.

## Deployment

The site is deployed on Vercel at https://aigent-office.com/.

Production deploys are handled by GitHub Actions in
`.github/workflows/deploy-vercel.yml`. Every push to `main` deploys to the
existing Vercel project.

Required GitHub repository secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

The repo includes `vercel.json`, which copies `site/` into the Vercel output
directory so the site is served from the domain root.

Custom domain setup:

- Add `aigent-office.com` to the Vercel project domains.
- Add `www.aigent-office.com` too, then configure the preferred redirect in
  Vercel.
- For the apex domain, configure the DNS record Vercel shows in the dashboard.
- For the `www` subdomain, configure the CNAME record Vercel shows in the
  dashboard.
