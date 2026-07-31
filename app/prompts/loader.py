from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


PROMPT_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def load_yaml_prompt(filename: str) -> dict[str, Any]:
    """
    prompts 디렉터리의 YAML 프롬프트 파일을 로드합니다.

    동일 파일은 메모리에 캐싱하여 반복적인 파일 읽기를 방지합니다.
    """
    prompt_path = PROMPT_DIR / filename

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"프롬프트 파일을 찾을 수 없습니다: {prompt_path}"
        )

    if not prompt_path.is_file():
        raise ValueError(
            f"지정된 경로가 파일이 아닙니다: {prompt_path}"
        )

    try:
        with prompt_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            prompt_data = yaml.safe_load(file)

    except yaml.YAMLError as exc:
        raise ValueError(
            f"YAML 파싱에 실패했습니다: {prompt_path}\n상세 오류: {exc}"
        ) from exc

    if not isinstance(prompt_data, dict):
        raise ValueError(
            f"YAML 최상위 구조는 객체여야 합니다: {prompt_path}"
        )

    required_fields = {
        "system_prompt",
        "human_prompt",
    }

    missing_fields = required_fields - prompt_data.keys()

    if missing_fields:
        raise ValueError(
            "필수 프롬프트 필드가 없습니다: "
            f"{', '.join(sorted(missing_fields))}"
        )

    for field_name in required_fields:
        field_value = prompt_data[field_name]

        if not isinstance(field_value, str):
            raise TypeError(
                f"{field_name} 값은 문자열이어야 합니다."
            )

        if not field_value.strip():
            raise ValueError(
                f"{field_name} 값이 비어 있습니다."
            )

    return prompt_data