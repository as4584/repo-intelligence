from __future__ import annotations

from change_radar.git.history import _parse_git_log_name_only


def test_parse_git_log_name_only_counts_files_once_per_commit() -> None:
    log_text = """
__COMMIT__
src/a.ts
src/b.ts
src/a.ts
__COMMIT__
src/a.ts
__COMMIT__
src/b.ts
"""

    counts = _parse_git_log_name_only(log_text)

    assert counts == {
        "src/a.ts": 2,
        "src/b.ts": 2,
    }
