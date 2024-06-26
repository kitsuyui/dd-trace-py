import re

from ddtrace.internal.logger import get_logger


log = get_logger(__name__)

_INSIDE_QUOTES_REGEXP = re.compile(r"^(?:\s*(?:sudo|doas)\s+)?\b\S+\b\s*(.*)")
COMMAND_PATTERN = r"^(?:\s*(?:sudo|doas)\s+)?\b\S+\b\s(.*)"
pattern = re.compile(COMMAND_PATTERN, re.IGNORECASE | re.MULTILINE)


def command_injection_sensitive_analyzer(evidence, name_pattern=None, value_pattern=None):
    regex_result = pattern.search(evidence.value)
    if regex_result and len(regex_result.groups()) > 0:
        start = regex_result.start(1)
        end = regex_result.end(1)
        return [{"start": start, "end": end}]
    return []
