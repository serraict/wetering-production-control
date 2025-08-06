# UV Migration Notes

## Project: Switch to uv package manager

**Date Started:** 6 August 2025

## Objective

Migrate from pip to uv for dependency management to improve installation speed and reproducibility.

## Current Environment

- Python: 3.12.2 (via pyenv)
- uv version: 0.5.12
- Virtual environment: `/Users/marijn/dev/serraict/customers/wetering/production_control/venv`
- uv.lock exists: ✅ (2373 lines)

## Baseline Measurements

### Current Setup Analysis

- Makefile `update` target uses: `pip install --upgrade pip build` + `pip install -r requirements-dev.txt` + `pip install -e .`
- CI workflow uses: `make update`
- Dependencies split between:
  - `pyproject.toml` (runtime deps)
  - `requirements-dev.txt` (dev deps)
  - `uv.lock` (lockfile, up-to-date)

### Performance Baseline

**Environment:**

- Clean virtual environment in `/tmp/test_venv_pip`
- Network: Good connection
- Test date: 6 August 2025

**Pip Installation Metrics (BASELINE):**
**Pip Installation Metrics (BASELINE):**

- [x] Pip clean install time: **30.249 seconds** ✅
- [x] Pip cached install time: **22.273 seconds** ✅ (26% faster with cache)
- [x] Current dependency count: ~52 packages installed (dev deps) + ~64 packages total (including runtime)
- [x] Current wheel cache behavior: Most packages cached from previous installs, significant speed improvement

**uv Installation Metrics:**

- [x] uv clean install time (cache cleared): **3.96 seconds** ✅
- [x] Performance improvement: **7.6x faster** than pip (30.2s → 3.96s) 🚀
- [x] All 82 packages installed successfully
- [x] uv creates virtual environment at `.venv` automatically
- [x] Command used: `uv sync --frozen` (respects lockfile, no modifications)

## Implementation Notes

### Observations

- Tests currently pass: 154 passed, 1 skipped (83% coverage)
- CI is passing (not failing as originally thought in backlog)
- Virtual environment is properly set up and being used
- **uv provides massive speed improvement even with cold cache**
- uv.lock file is comprehensive (2373 lines) and well-maintained

### Next Steps

1. ✅ Verified uv sync performance vs pip baseline
1. ✅ Test that applications still work with uv-installed dependencies
1. ✅ Update makefile targets to use uv sync instead of pip install
1. ✅ Update CI workflow to use uv
1. Test CI workflow passes
1. Update documentation to reflect new dependency management approach

### Implementation Details

**Makefile Changes:**

- `bootstrap`: Changed from `python -m venv venv` to `uv venv` (creates `.venv` directory)
- `update`: Changed from pip-based installation to `uv sync --frozen && uv pip install -r requirements-dev.txt`
- Used `--frozen` flag to ensure reproducible builds (same behavior in dev and CI)
- Removed redundant `update-frozen` target for consistency

**CI Workflow Changes:**

- Added `astral-sh/setup-uv@v4` action with caching enabled
- Kept existing `make update` call (now uses uv internally)
- No other workflow files needed changes

**Key Decisions:**

- Use `--frozen` everywhere for consistency and safety
- Dependency updates require explicit `make lock` first
- Maintain dev dependencies in requirements-dev.txt for now

## Issues & Decisions

### Questions to Resolve

- Should we keep `requirements-dev.txt` or migrate fully to pyproject.toml?
- How to handle backwards compatibility during transition?
- CI runner compatibility with uv installation?

## Results

*(To be filled as we progress)*
