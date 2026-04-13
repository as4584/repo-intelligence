from __future__ import annotations

from change_radar.git.diff import _parse_diff_output


def test_parse_diff_output_extracts_new_line_numbers() -> None:
    diff_text = """
diff --git a/src/services/payment_service.ts b/src/services/payment_service.ts
index 123..456 100644
--- a/src/services/payment_service.ts
+++ b/src/services/payment_service.ts
@@ -3,0 +4,2 @@
+const updated = true;
+return updated;
"""

    changes = _parse_diff_output(diff_text)

    assert len(changes) == 1
    assert changes[0].relative_path == "src/services/payment_service.ts"
    assert changes[0].changed_lines == (4, 5)
