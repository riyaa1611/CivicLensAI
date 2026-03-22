"""
ScaleDown optimization pipeline for CivicLens.

Uses ScaleDown library (from the parent directory) for intelligent LLM context
compression and optimization:

  - ScaleDownCompressor: API-powered prompt compression (requires SCALEDOWN_API_KEY)
  - SemanticOptimizer:   Local embedding-based code chunk selection (for code docs)

The RAG pipeline calls compress_context() to reduce token usage before LLM calls.
Gracefully falls back to raw context when ScaleDown API key is not configured.
"""
import os
import sys
import logging
import tempfile
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Ensure ScaleDown root is on the path (set by settings.py, but be defensive)
_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class ContextOptimizer:
    """
    Wraps ScaleDown components for CivicLens context optimization.

    Usage:
        optimizer = ContextOptimizer()
        compressed_ctx, metrics = optimizer.compress_context(context, query)
    """

    def __init__(self):
        self._compressor = None
        self._semantic_optimizer = None
        self._pipeline = None
        self._init_components()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_components(self) -> None:
        """Attempt to initialize all ScaleDown components."""
        self._init_compressor()
        self._init_semantic_optimizer()

    def _init_compressor(self) -> None:
        """Initialize ScaleDownCompressor if SCALEDOWN_API_KEY is set."""
        try:
            import scaledown as sd
            from scaledown.compressor import ScaleDownCompressor

            api_key = os.environ.get("SCALEDOWN_API_KEY") or _get_settings_key()
            if api_key:
                sd.set_api_key(api_key)
                self._compressor = ScaleDownCompressor(
                    target_model="gpt-4o",
                    rate="auto",
                )
                logger.info("ScaleDownCompressor initialized ✓")
            else:
                logger.info(
                    "SCALEDOWN_API_KEY not set — ScaleDownCompressor disabled "
                    "(context will be passed raw to LLM)"
                )
        except ImportError as e:
            logger.warning(f"ScaleDown import error: {e}")
        except Exception as e:
            logger.warning(f"ScaleDownCompressor init failed: {e}")

    def _init_semantic_optimizer(self) -> None:
        """
        Initialize SemanticOptimizer for code-document optimization.
        This works locally without an API key (uses sentence-transformers + FAISS).
        """
        try:
            from scaledown.optimizer import SemanticOptimizer

            self._semantic_optimizer = SemanticOptimizer(
                model_name="BAAI/bge-large-en-v1.5",
                top_k=3,
            )
            logger.info("SemanticOptimizer initialized ✓")
        except ImportError as e:
            logger.info(f"SemanticOptimizer unavailable (optional): {e}")
        except Exception as e:
            logger.info(f"SemanticOptimizer init skipped: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress_context(
        self, context: str, query: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Compress retrieved policy context using ScaleDownCompressor.

        Args:
            context: Concatenated policy chunks from vector retrieval
            query:   User's question (guides compression toward relevance)

        Returns:
            (compressed_context, metrics_dict)
            If compressor is unavailable, returns (original_context, fallback_metrics)
        """
        if not context or not context.strip():
            return context, _empty_metrics()

        if self._compressor is None:
            return context, {
                "status": "no_compressor",
                "fallback": True,
                "original_tokens": _estimate_tokens(context),
                "compressed_tokens": _estimate_tokens(context),
                "compression_ratio": 1.0,
                "savings_percent": 0.0,
            }

        try:
            result = self._compressor.compress(context=context, prompt=query)
            return result.content, {
                "status": "compressed",
                "fallback": False,
                "original_tokens": result.tokens[0],
                "compressed_tokens": result.tokens[1],
                "compression_ratio": result.compression_ratio,
                "savings_percent": result.savings_percent,
                "latency_ms": result.latency,
            }
        except Exception as e:
            logger.warning(f"ScaleDown compression failed, using raw context: {e}")
            return context, {
                "status": "error",
                "fallback": True,
                "error": str(e),
                "original_tokens": _estimate_tokens(context),
                "compressed_tokens": _estimate_tokens(context),
                "compression_ratio": 1.0,
                "savings_percent": 0.0,
            }

    def optimize_code_document(
        self, text: str, query: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Optimize a text document using SemanticOptimizer.
        Writes text to a temporary Python file and runs semantic extraction.

        Useful for uploaded policy documents or code files.

        Returns:
            (optimized_content, metrics_dict)
            Returns (None, metrics) if optimizer is unavailable or fails.
        """
        if self._semantic_optimizer is None:
            return None, {"status": "no_optimizer"}

        # SemanticOptimizer requires a file path to a Python file.
        # Write the content to a temp file for processing.
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp:
                # Wrap text as Python docstring so AST parser can handle it
                tmp.write(f'"""\n{text}\n"""\n')
                tmp_path = tmp.name

            result = self._semantic_optimizer.optimize(
                context="",
                query=query,
                file_path=tmp_path,
            )

            os.unlink(tmp_path)

            return result.content, {
                "status": "optimized",
                "original_tokens": result.metrics.original_tokens,
                "optimized_tokens": result.metrics.optimized_tokens,
                "compression_ratio": result.metrics.compression_ratio,
                "chunks_retrieved": result.metrics.chunks_retrieved,
                "latency_ms": result.metrics.latency_ms,
                "retrieval_mode": result.metrics.retrieval_mode,
            }

        except Exception as e:
            logger.warning(f"SemanticOptimizer failed: {e}")
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            return None, {"status": "error", "error": str(e)}

    def run_full_pipeline(
        self, context: str, query: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Run the full ScaleDown pipeline using Pipeline class when possible.
        Falls back to compress_context if pipeline setup fails.
        """
        if self._compressor is None:
            return context, _empty_metrics()

        try:
            import scaledown as sd

            pipeline = sd.Pipeline([
                ("compressor", self._compressor),
            ])
            result = pipeline.run(context=context, prompt=query)

            total_metrics = {
                "status": "pipeline_run",
                "fallback": False,
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.final_tokens,
                "compression_ratio": result.total_compression_ratio,
                "savings_percent": result.savings_percent,
                "history": [
                    {
                        "step": step.step_name,
                        "input_tokens": step.input_tokens,
                        "output_tokens": step.output_tokens,
                        "latency_ms": step.latency_ms,
                    }
                    for step in result.history
                ],
            }
            return result.final_content, total_metrics

        except Exception as e:
            logger.warning(f"Pipeline run failed, falling back to direct compress: {e}")
            return self.compress_context(context, query)

    @property
    def compressor_available(self) -> bool:
        return self._compressor is not None

    @property
    def semantic_optimizer_available(self) -> bool:
        return self._semantic_optimizer is not None


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_optimizer: Optional[ContextOptimizer] = None


def get_optimizer() -> ContextOptimizer:
    """Return the singleton ContextOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = ContextOptimizer()
    return _optimizer


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_settings_key() -> Optional[str]:
    """Try to read SCALEDOWN_API_KEY from CivicLens settings."""
    try:
        from ..config.settings import settings
        return settings.scaledown_api_key
    except Exception:
        return None


def _estimate_tokens(text: str) -> int:
    """Quick token count estimate (≈ 4 chars per token)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


def _empty_metrics() -> Dict[str, Any]:
    return {
        "status": "empty_context",
        "fallback": True,
        "original_tokens": 0,
        "compressed_tokens": 0,
        "compression_ratio": 1.0,
        "savings_percent": 0.0,
    }
