# AI력 Bundle v0.1 Standard

Each bundle is a downloadable package that includes a mini SaaS and the AI
worker setup used to build or operate it.

## Required Structure

```txt
bundle-name/
  README.md
  bundle.json
  .env.example
  LICENSE

  app/
    Mini SaaS source code

  worker/
    agent.json
    agent.md
    skills/
    harness/
    mcp/

  examples/
    input/
    output/

  docs/
    build-log.md
    cost-guide.md
    security-notes.md
    limitations.md
```

## Required Metadata

`bundle.json` must include:

- slug
- title
- worker name
- category
- difficulty
- runtime mode
- required API keys
- estimated cost
- included assets
- download URL
- disclaimer

## Difficulty Levels

- Beginner: API key and one command are enough.
- Intermediate: package install, local runtime, and basic config are required.
- Advanced: MCP, database, deployment, or cloud setup is required.

## Publishing Checklist

- README exists.
- `.env.example` exists.
- No real API keys or secrets are committed.
- Sample input and output exist.
- Cost guide exists.
- Security notes exist.
- Limitations are documented.
- Original SaaS brand, UI, and copy are not cloned.
- Local execution path is clear.

