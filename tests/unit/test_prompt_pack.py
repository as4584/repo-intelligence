from __future__ import annotations

from change_radar.reports.markdown import format_prompt_pack
from change_radar.types import RankedFile


def test_format_prompt_pack_includes_task_files_and_instructions() -> None:
    prompt = format_prompt_pack(
        "add retry logic to payment flow",
        [
            RankedFile(
                relative_path="src/services/payment_service.ts",
                score=5.0,
                reasons=("symbol contains 'payment'", "imports matched file"),
            ),
            RankedFile(
                relative_path="src/routes/checkout.ts",
                score=2.0,
                reasons=("imported by matched file",),
            ),
        ],
    )

    assert "Task: add retry logic to payment flow" in prompt
    assert "#src/services/payment_service.ts" in prompt
    assert "#src/routes/checkout.ts" in prompt
    assert "Make the smallest safe change" in prompt
