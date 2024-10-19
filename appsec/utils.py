import os
import re

from typing import List, Tuple, Dict, Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)


HUNK_HEADER_PATTERN = r'^@@ -(\d+),\d+ \+(\d+),\d+ @@'
NO_NEW_LINE_META_PATTERN = 'no newline at end of file'

DEFAULT_ANTHROPIC_MODEL = 'claude-3-5-sonnet-20240620'
DEFAULT_OPENAI_MODEL = 'gpt-4o'


def has_set_llm_provider_api_key() -> bool:
    return os.getenv('ANTHROPIC_API_KEY', None) is not None or os.getenv('OPENAI_API_KEY', None) is not None


def get_anthropic_model():
    return os.getenv('ANTHROPIC_MODEL', DEFAULT_ANTHROPIC_MODEL)


def get_openai_model():
    return os.getenv('OPENAI_MODEL', DEFAULT_OPENAI_MODEL)


def get_llm_provider_config() -> List:
    if os.getenv('ANTHROPIC_API_KEY', None):
        return [
            {
                "model": get_anthropic_model(),
                "api_key": os.getenv('ANTHROPIC_API_KEY'),
                "api_type": "anthropic",
            }
        ]
    elif os.getenv('OPENAI_API_KEY', None):
        return [
            {
                "model": get_openai_model(),
                "api_key": os.getenv('OPENAI_API_KEY'),
                "api_type": "openai",
            }
        ]
    else:
        raise Exception('Model provider API key not specified or provider model is currently unsupported')


def get_llm_settings_config(cache_seed: Optional[str] = None) -> Dict[str, Any]:
    return {"config_list": get_llm_provider_config(), "cache_seed": cache_seed,}


def get_llm() -> BaseChatModel:
    if os.getenv('ANTHROPIC_API_KEY', None):
        return ChatAnthropic(
            model=get_anthropic_model(),
            temperature=0,
            max_tokens_to_sample=8192,
            default_request_timeout=30,
            max_retries=10,
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        )
    elif os.getenv('OPENAI_API_KEY', None):
        return ChatOpenAI(
            model=get_openai_model(),
            temperature=0,
            max_tokens=8192,
            timeout=30,
            max_retries=10,
            openai_api_key=os.getenv('OPENAI_API_KEY'),
        )
    else:
        raise Exception('Model provider API key not specified or provider model is currently unsupported')


def extract_hunks(diff) -> List[Tuple[str, str, str]]:
    """
    :param diff: pull request patch
    :return: extracted patch hunks, including hunk header, and old and new code
    """
    old_lines = []
    new_lines = []

    current_old_line_num = None
    current_new_line_num = None

    hunks = []
    hunk_header = None
    for line in diff.splitlines():
        if NO_NEW_LINE_META_PATTERN in line.lower():
            continue

        header_match = re.match(HUNK_HEADER_PATTERN, line)
        if header_match:
            if hunk_header:
                hunks.append((hunk_header, "\n".join(old_lines), "\n".join(new_lines)))

            hunk_header = line
            current_old_line_num = int(header_match.group(1)) - 1
            current_new_line_num = int(header_match.group(2)) - 1

        elif line.startswith('-'):
            current_old_line_num += 1
            # old lines do not have a line number prefix to prevent the LLM
            # from erroneously using returning them as line_number_start and
            # line_number_end values
            old_lines.append(f"{line}")
        elif line.startswith('+'):
            current_new_line_num += 1
            new_lines.append(f"{current_new_line_num} {line}")
        else:
            current_old_line_num += 1
            current_new_line_num += 1
            old_lines.append(f"{line}")
            new_lines.append(f"{current_new_line_num} {line}")

    hunks.append((hunk_header, "\n".join(old_lines), "\n".join(new_lines)))
    return hunks
