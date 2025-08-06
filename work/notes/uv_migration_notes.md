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

## Implementation Notes

### Observations

- Tests currently pass: 154 passed, 1 skipped (83% coverage)
- CI is passing (not failing as originally thought in backlog)
- Virtual environment is properly set up and being used

### Next Steps

1. ✅ Benchmark current pip performance - **COMPLETED**
2. 🔄 **NEXT:** Plan makefile migration strategy  
3. Test uv equivalent commands
4. Update makefile targets
5. Update CI workflow

## Issues & Decisions

### Questions to Resolve

- Should we keep `requirements-dev.txt` or migrate fully to pyproject.toml?
- How to handle backwards compatibility during transition?
- CI runner compatibility with uv installation?

## Results

*(To be filled as we progress)*
