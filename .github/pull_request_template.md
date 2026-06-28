## Registry change

### Provider
<!-- anthropic | openai | google | qwen | together | ... -->

### Source URL
<!-- Official deprecation or model docs URL -->

### Models added/updated
<!-- List model IDs and status changes -->

### Checklist
- [ ] `modelalive validate --strict` passes
- [ ] `pytest -q` passes
- [ ] No self-referencing aliases
- [ ] Retired/deprecated models have `replacement` pointing to active model
- [ ] `migrate_url` links to official provider docs
