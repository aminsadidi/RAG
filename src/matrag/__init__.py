"""RAG over scientific papers for material properties."""

import os

# Colab preinstalls JAX and TensorFlow. If a dependency imports them, JAX reserves
# 75 % of the GPU memory up front (TensorFlow grabs it all), leaving no room for the
# PyTorch embedding model or Ollama. Keep them off the GPU; set before any import.
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("TF_FORCE_GPU_ALLOW_GROWTH", "true")
os.environ.setdefault("USE_TF", "0")  # transformers: use PyTorch only
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
