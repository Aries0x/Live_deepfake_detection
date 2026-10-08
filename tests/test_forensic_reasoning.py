import os
import pytest
from backend.app.config import settings

@pytest.mark.skipif(not os.getenv("HF_TOKEN") and not settings.HF_TOKEN, reason="HF_TOKEN not configured")
def test_forensic_reasoning_api():
    """Test remote Hugging Face reasoning model if token is available."""
    from forensic.explainable_ai import MultimodalForensicExplainer
    
    metrics = {
        "fusion_risk": 0.864,
        "classification": "LIKELY_MANIPULATED",
        "visual_score": 0.842,
        "audio_score": 0.891,
        "sync_latency_ms": 160,
    }
    stability = {
        "stability_score": 0.942,
        "verdict": "STABLE",
    }
    
    result = MultimodalForensicExplainer.generate_reasoning_synthesis(metrics, stability)
    assert result is not None
    assert "explanation" in result
