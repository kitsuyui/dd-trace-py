import os

import pytest

from ddtrace.appsec._iast.constants import VULN_PATH_TRAVERSAL
from ddtrace.appsec._iast.reporter import Evidence
from ddtrace.appsec._iast.reporter import IastSpanReporter
from ddtrace.appsec._iast.reporter import Location
from ddtrace.appsec._iast.reporter import Source
from ddtrace.appsec._iast.reporter import Vulnerability
from ddtrace.appsec._iast.taint_sinks.path_traversal import PathTraversal


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    "file_path",
    [
        "1",
        "12",
        "123",
        "a",
        "ab",
        "AbC",
        "-",
        "txt",
        ".txt",
    ],
)
def test_path_traversal_redact_exclude(file_path):
    ev = Evidence(
        valueParts=[
            {"value": file_path, "source": 0},
        ]
    )
    loc = Location(path="foobar.py", line=35, spanId=123)
    v = Vulnerability(type=VULN_PATH_TRAVERSAL, evidence=ev, location=loc)
    s = Source(origin="SomeOrigin", name="SomeName", value="SomeValue")
    report = IastSpanReporter([s], {v})

    redacted_report = PathTraversal._redact_report(report)
    for v in redacted_report.vulnerabilities:
        assert v.evidence.valueParts == [{"source": 0, "value": file_path}]


@pytest.mark.parametrize(
    "file_path",
    [
        "/mytest/folder/",
        "mytest/folder/",
        "mytest/folder",
        "../mytest/folder/",
        "../mytest/folder/",
        "../mytest/folder",
        "/mytest/folder/",
        "/mytest/folder/",
        "/mytest/folder",
        "/mytest/../folder/",
        "mytest/../folder/",
        "mytest/../folder",
        "../mytest/../folder/",
        "../mytest/../folder/",
        "../mytest/../folder",
        "/mytest/../folder/",
        "/mytest/../folder/",
        "/mytest/../folder",
        "/mytest/folder/file.txt",
        "mytest/folder/file.txt",
        "../mytest/folder/file.txt",
        "/mytest/folder/file.txt",
        "mytest/../folder/file.txt",
        "../mytest/../folder/file.txt",
        "/mytest/../folder/file.txt",
    ],
)
def test_path_traversal_redact_rel_paths(file_path):
    ev = Evidence(
        valueParts=[
            {"value": file_path, "source": 0},
        ]
    )
    loc = Location(path="foobar.py", line=35, spanId=123)
    v = Vulnerability(type=VULN_PATH_TRAVERSAL, evidence=ev, location=loc)
    s = Source(origin="SomeOrigin", name="SomeName", value="SomeValue")
    report = IastSpanReporter([s], {v})

    redacted_report = PathTraversal._redact_report(report)
    for v in redacted_report.vulnerabilities:
        assert v.evidence.valueParts == [{"source": 0, "value": file_path}]


def test_path_traversal_redact_abs_paths():
    file_path = os.path.join(ROOT_DIR, "../fixtures", "taint_sinks", "path_traversal_test_file.txt")
    ev = Evidence(
        valueParts=[
            {"value": file_path, "source": 0},
        ]
    )
    loc = Location(path="foobar.py", line=35, spanId=123)
    v = Vulnerability(type=VULN_PATH_TRAVERSAL, evidence=ev, location=loc)
    s = Source(origin="SomeOrigin", name="SomeName", value="SomeValue")
    report = IastSpanReporter([s], {v})

    redacted_report = PathTraversal._redact_report(report)
    for v in redacted_report.vulnerabilities:
        assert v.evidence.valueParts == [{"source": 0, "value": file_path}]
