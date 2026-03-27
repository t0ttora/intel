"""Remote CLI main — entry point for remote-only mode."""
from __future__ import annotations

import os
import sys


def main() -> None:
    """Remote CLI entry point.

    Forces remote mode by setting NOBLE_INTEL_URL if not already set,
    then delegates to the main CLI.
    """
    if not os.environ.get("NOBLE_INTEL_URL"):
        print(
            "Error: NOBLE_INTEL_URL must be set for remote mode.\n"
            "Usage: NOBLE_INTEL_URL=https://your-server.com noblecli-remote <command>\n"
            "Or use 'noblecli' for local mode."
        )
        sys.exit(1)

    # Force remote mode
    os.environ["NOBLE_INTEL_REMOTE"] = "1"

    from cli.main import app
    app()


if __name__ == "__main__":
    main()
