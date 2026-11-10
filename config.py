"""Movie sources."""

from pathlib import Path

# Each source is (directory, filename pattern, prefer encoded replacements).
# Set a directory to None to disable it.
SOURCES = (
    (Path("/irisa/mod/podmovie/modvideos/"), "*.mp4", True),
    (Path("/viz2/media/SunInTime/"), "AIAtriratio*.mp4", False),
)
