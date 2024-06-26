from ddtrace.appsec._iast.constants import HEADER_NAME_VALUE_SEPARATOR
from ddtrace.internal.logger import get_logger


log = get_logger(__name__)


def header_injection_sensitive_analyzer(evidence, name_pattern, value_pattern):
    evidence_value = evidence.value
    sections = evidence_value.split(HEADER_NAME_VALUE_SEPARATOR)
    header_name = sections[0]
    header_value = HEADER_NAME_VALUE_SEPARATOR.join(sections[1:])

    if name_pattern.search(header_name) or value_pattern.search(header_value):
        return [{"start": len(header_name) + len(HEADER_NAME_VALUE_SEPARATOR), "end": len(evidence_value)}]

    return []
