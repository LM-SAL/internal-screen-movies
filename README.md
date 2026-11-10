# internal_screen_movies

Build a shuffled playlist of IRIS and SDO/AIA movies from mounted network shares.
Configure directories and filename patterns in `config.py` (`SOURCES`); set a directory
to `None` to disable it. Requires Python 3.9+. No extra Python packages are needed.

    python display_movies.py

Ignores movies in `orig/`, prefers suffixed encoded IRIS movies over an unsuffixed
movie beside them, and keeps one copy per remaining filename. Every source gets the
same number of slots: each round of the playlist holds one movie from each source in
random order, and within a source every movie plays once before any repeats, so the
same movie never plays twice in a row.

The result is `playlist.m3u` (absolute paths), which any M3U-capable player can open.
Set fullscreen, looping and playback speed (previously half speed) in the player.
