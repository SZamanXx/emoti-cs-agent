"""pytest configuration: common fixtures + path setup so `import app...` works from tests/."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `app` importable regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Ensure tests run with deterministic env defaults, not whatever the dev shell has.
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("WEBHOOK_HMAC_SECRET", "test-hmac-secret-32-bytes-min!!")
os.environ.setdefault("EMBEDDING_BACKEND", "local")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPERATOR_USERNAME", "test-operator")
os.environ.setdefault("OPERATOR_PASSWORD", "test-pwd")
