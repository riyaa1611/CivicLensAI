# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ScaleDown** is a Python library for intelligent LLM context optimization. It reduces token usage via two mechanisms:
1. **Optimizers** — local processing that extracts relevant code/text chunks
2. **Compressors** — API-powered prompt compression via the hosted ScaleDown service

## Commands

```bash
# Install core
pip install -e .

# Install with optional dependencies
pip install -e ".[haste]"       # HASTE optimizer (requires HasteContext>=0.2.4)
pip install -e ".[semantic]"    # Semantic optimizer (sentence-transformers + faiss)
pip install -e ".[haste,semantic]"

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_pipeline.py -v
pytest tests/test_compressor.py -v
pytest tests/test_haste.py -v
pytest tests/test_semantic.py -v
```

## Architecture

### Data Flow
```
Input context → Optimizer(s) [optional] → Compressor(s) [optional] → PipelineResult
```

The `Pipeline` class enforces ordering: all optimizers must precede all compressors. Each stage produces metrics (token counts, compression ratio, latency).

### Key Modules

- **`scaledown/pipeline.py`** — Orchestrates multi-stage processing; validates step ordering; collects `StepMetadata` per stage.
- **`scaledown/optimizer/haste.py`** — `HasteOptimizer`: AST-guided code retrieval using Tree-sitter + BM25 + semantic search via the HASTE API.
- **`scaledown/optimizer/semantic_code.py`** — `SemanticOptimizer`: embedding-based search using sentence-transformers + FAISS locally.
- **`scaledown/compressor/scaledown_compressor.py`** — `ScaleDownCompressor`: batched HTTP calls to the hosted compression API; uses `ThreadPoolExecutor` for concurrency.
- **`scaledown/compressor/types/`** — Pydantic models: `OptimizedContext`, `CompressedPrompt`, `OptimizerMetrics`, `CompressorMetrics`, `PipelineResult`, `StepMetadata`.

### Lazy Loading

`scaledown/optimizer/__init__.py` uses `__getattr__` for lazy imports so that missing optional dependencies (`HasteContext`, `sentence-transformers`, `faiss`) only raise errors when the specific optimizer is instantiated, not on `import scaledown`.

### API Key

Set via environment variable `SCALEDOWN_API_KEY` or programmatically via `scaledown.set_api_key()`. Stored in module-level global state in `scaledown/compressor/config.py` and `scaledown/optimizer/config.py`.

### Known Structural Issue

The package references `scaledown.types` and `scaledown.config` as top-level modules (e.g., in `__init__.py` re-exports), but these files do not exist — the actual types live in `scaledown.compressor.types`. Any work touching imports should use `scaledown.compressor.types` as the canonical location or create the missing shim modules.
