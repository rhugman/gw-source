"""Experimental methods (Phase 5 research). Not part of the stable API; may change or go away.

- face_routing: face-to-face routing of water within rectilinear DIS cells (Chowdhury 2016)
  instead of full mixing.
"""

from . import face_routing

__all__ = ["face_routing"]
