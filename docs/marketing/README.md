# Marketing / launch copy

Copy-paste posts for distribution. Update version pins when releasing.

| File | Channel |
|------|---------|
| [show-hn.md](show-hn.md) | Hacker News Show HN |
| [reddit-local-llama.md](reddit-local-llama.md) | r/LocalLLaMA |
| [reddit-ml-stable.md](reddit-ml-stable.md) | r/MachineLearning |
| [twitter-thread.md](twitter-thread.md) | X / LinkedIn |

## Terminal recording

```bash
./scripts/record_demo.sh          # run demo in terminal
./scripts/record_demo.sh --cast   # record with asciinema (install: brew install asciinema)
```

Upload `.cast` to https://asciinema.org and embed in README.

## Weekly metrics checklist

- [ ] PyPI downloads: https://pypistats.org/packages/modelalive
- [ ] npm downloads: https://www.npmjs.com/package/modelalive
- [ ] GitHub stars / forks
- [ ] `gh search code "import modelalive"` (exclude this repo)
- [ ] Fly logs: `/v1/alive?model=` from non-health IPs

## Design partners

First 3 integrations get priority registry updates. Template: [design-partner.md](design-partner.md)
