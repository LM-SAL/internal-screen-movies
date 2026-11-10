"""Build a balanced, shuffled M3U movie playlist."""

from __future__ import annotations

import logging
import random
import threading
from pathlib import Path

from config import SOURCES

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
PLAYLIST = HERE / "playlist.m3u"
# A stale network mount blocks forever on stat, so the mount check gives up.
MOUNT_CHECK_TIMEOUT = 30.0


def mount_problem(directory: Path, timeout: float = MOUNT_CHECK_TIMEOUT) -> str | None:
    """Check a directory in a daemon thread so a stalled mount can time out."""
    failures: list[OSError] = []

    def probe() -> None:
        try:
            directory.expanduser().resolve(strict=True)
        except OSError as exc:
            failures.append(exc)

    thread = threading.Thread(target=probe, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return f"did not respond within {timeout:g} seconds (stale mount?)"
    if failures:
        return f"cannot be read: {failures[0].strerror or failures[0]}"
    return None


def check_directories_mounted() -> None:
    """Check that every configured source is accessible."""
    for directory, *_ in SOURCES:
        if directory is None:
            continue
        problem = mount_problem(directory)
        if problem is not None:
            msg = f"Error: Directory '{directory}' {problem}"
            raise OSError(msg)


def get_paths_for_movies(base_path: Path, filename: str, *, prefer_encoded: bool = False) -> list[str]:
    """Ignore ``orig`` directories and keep one copy of each movie."""
    # rglob also matches directories, so keep only regular files.
    paths = {
        path for path in base_path.rglob(filename) if path.is_file() and "orig" not in path.relative_to(base_path).parts
    }
    if prefer_encoded:
        names_by_parent: dict[Path, set[str]] = {}
        for path in paths:
            names_by_parent.setdefault(path.parent, set()).add(path.name)
        replaced_names = {
            path.name
            for path in paths
            if any(
                other.startswith(f"{path.stem}_") and Path(other).suffix == path.suffix
                for other in names_by_parent[path.parent]
            )
        }
        paths = {path for path in paths if path.name not in replaced_names}

    seen: dict[str, str] = {}
    for path in sorted(paths, key=lambda path: (len(path.parts), path)):
        seen.setdefault(path.name, str(path))
    return list(seen.values())


def shuffled_cycle(movies: list[str], count: int) -> list[str]:
    """Return ``count`` movies, reshuffled each pass so every movie plays once before any repeats."""
    playlist: list[str] = []
    while len(playlist) < count:
        batch = random.sample(movies, len(movies))
        # Redraw so a pass never starts with the movie the previous pass ended on.
        while len(movies) > 1 and playlist and batch[0] == playlist[-1]:
            batch = random.sample(movies, len(movies))
        playlist.extend(batch)
    return playlist[:count]


def spread(sources: list[list[str]]) -> list[str]:
    """Give each source one slot per round, in random order within the round."""
    if not sources or not all(sources):
        msg = "Every source needs at least one movie."
        raise ValueError(msg)
    rounds = max(len(source) for source in sources)
    playlist = []
    for round_movies in zip(*(shuffled_cycle(source, rounds) for source in sources)):
        playlist.extend(random.sample(round_movies, len(round_movies)))
    return playlist


def create_playlist(movies: list[str]) -> None:
    """Write the M3U playlist."""
    logger.info("Writing %s", PLAYLIST)
    PLAYLIST.write_text("#EXTM3U\n" + "".join(f"{path}\n" for path in movies), encoding="utf-8")


def build_playlist() -> None:
    """Find movies and write the playlist."""
    check_directories_mounted()
    sources = []
    for base_path, filename_pattern, prefer_encoded in SOURCES:
        if base_path is None:
            continue
        logger.info("Searching for movies in %s", base_path)
        found = get_paths_for_movies(base_path, filename_pattern, prefer_encoded=prefer_encoded)
        if not found:
            msg = f"No movies found in {base_path}"
            raise FileNotFoundError(msg)
        logger.info("Found %d movies in %s", len(found), base_path)
        sources.append(found)
    create_playlist(spread(sources))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_playlist()
