"""Shared CTC command-model definition (training + serving import this).

Backbone: torchaudio `WAV2VEC2_ASR_BASE_960H` — wav2vec2.0 transformer encoder
SSL-pretrained then fully CTC-supervised on 960 h LibriSpeech. For a small
command corpus this converges far better than cold-start training. We replace
its 29-class ASR head (`model.aux`) with our 30-symbol char vocab and fine-tune;
the backbone freezes for the first 5% of steps (anti-forgetting), then opens up.
"""
from __future__ import annotations

from .char_vocab import V  # single source of truth for vocab size


def build_finetune_model(num_tokens: int = V):
    import torch
    import torchaudio

    model = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H.get_model()
    model.aux = torch.nn.LazyLinear(num_tokens)      # fresh CTC head (d_enc=768)
    return model


def load_checkpoint(path: str, map_location: str = "cpu"):
    import torch
    model = build_finetune_model()
    sd = torch.load(path, map_location=map_location, weights_only=True)
    model.load_state_dict(sd)
    model.eval()
    return model


def decode_logits(model, audio_np):
    """-> (greedy ids list over time, raw logits[T, V])"""
    import numpy as np
    import torch
    wave = torch.from_numpy(np.asarray(audio_np, dtype=np.float32))[None]
    with torch.no_grad():
        logits, _ = model(wave)
    return logits[0].argmax(-1).tolist(), logits[0]
