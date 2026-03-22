"""Shim package: re-exports from scaledown.compressor.types for top-level access."""
from scaledown.compressor.types import (
    CompressedPrompt,
    OptimizedContext,
    PipelineResult,
    StepMetadata,
    OptimizerMetrics,
    CompressorMetrics,
)

__all__ = [
    "CompressedPrompt",
    "OptimizedContext",
    "PipelineResult",
    "StepMetadata",
    "OptimizerMetrics",
    "CompressorMetrics",
]
