#!/bin/sh
# Keep Python's shared-library search separate from the n8n Node.js runtime.
PYTHONHOME=/opt/python LD_LIBRARY_PATH=/opt/python/lib exec /opt/python/bin/python3 "$@"
