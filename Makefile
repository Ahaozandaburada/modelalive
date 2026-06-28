.PHONY: sync validate test check release lint

sync:
	python scripts/merge_seeds.py
	python scripts/sync_registry.py

validate: sync
	modelalive validate --strict

test: validate
	pytest -q

check: test
	python scripts/refresh_sources.py
	modelalive validate --strict

release: check
	python -m build

smoke:
	modelalive check claude-sonnet-4-20250514 || true
	modelalive ensure claude-sonnet-4-20250514
	modelalive info gemini-2.0-flash
