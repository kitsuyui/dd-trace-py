import asyncio
import sys

import httpx
import pytest
import ddtrace
from ddtrace.contrib.starlette import patch, unpatch
from ddtrace.propagation import http as http_propagation
from starlette.testclient import TestClient
from tests import override_http_config
from tests.tracer.test_tracer import get_dummy_tracer
from app import get_app


@pytest.fixture
def tracer():
    original_tracer = ddtrace.tracer
    tracer = get_dummy_tracer()
    if sys.version_info < (3, 7):
        # enable legacy asyncio support
        from ddtrace.contrib.asyncio.provider import AsyncioContextProvider

        tracer.configure(context_provider=AsyncioContextProvider())
    setattr(ddtrace, "tracer", tracer)
    patch()
    yield tracer
    setattr(ddtrace, "tracer", original_tracer)
    unpatch()


@pytest.fixture
def app(tracer):
    app = get_app()
    yield app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def test_200(client, tracer):
    r = client.get("/200")

    assert r.status_code == 200
    assert r.text == "Success"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/200"
    assert request_span.get_tag("http.status_code") == "200"
    assert request_span.get_tag("http.query.string") is None


def test_200_query_string(client, tracer):
    with override_http_config("starlette", dict(trace_query_string=True)):
        r = client.get("?foo=bar")

    assert r.status_code == 200
    assert r.text == "Success"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/"
    assert request_span.get_tag("http.status_code") == "200"
    assert request_span.get_tag("http.query.string") == "foo=bar"


def test_200_multi_query_string(client, tracer):
    with override_http_config("starlette", dict(trace_query_string=True)):
        r = client.get("?foo=bar&x=y")

    assert r.status_code == 200
    assert r.text == "Success"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/"
    assert request_span.get_tag("http.status_code") == "200"
    assert request_span.get_tag("http.query.string") == "foo=bar&x=y"


def test_201(client, tracer):
    r = client.post("/201")

    assert r.status_code == 201
    assert r.text == "Created"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "POST"
    assert request_span.get_tag("http.url") == "http://testserver/201"
    assert request_span.get_tag("http.status_code") == "201"
    assert request_span.get_tag("http.query.string") is None


def test_404(client, tracer):
    r = client.get("/404")

    assert r.status_code == 404
    assert r.text == "Not Found"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/404"
    assert request_span.get_tag("http.status_code") == "404"


def test_500error(client, tracer):
    with pytest.raises(RuntimeError):
        client.get("/500")

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 1
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/500"
    assert request_span.get_tag("http.status_code") == "500"
    assert request_span.get_tag("error.msg") == "Server error"
    assert request_span.get_tag("error.type") == "builtins.RuntimeError"
    assert 'raise RuntimeError("Server error")' in request_span.get_tag("error.stack")


def test_distributed_tracing(client, tracer):
    headers = [
        (http_propagation.HTTP_HEADER_PARENT_ID, "1234"),
        (http_propagation.HTTP_HEADER_TRACE_ID, "5678"),
    ]
    r = client.get("http://testserver/", headers=dict(headers))

    assert r.status_code == 200
    assert r.text == "Success"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/"
    assert request_span.get_tag("http.status_code") == "200"
    assert request_span.parent_id == 1234
    assert request_span.trace_id == 5678


@pytest.mark.asyncio
async def test_multiple_requests(app, tracer):
    with override_http_config("starlette", dict(trace_query_string=True)):
        async with httpx.AsyncClient(app=app) as client:
            responses = await asyncio.gather(
                client.get("http://testserver/", params={"sleep": True}),
                client.get("http://testserver/", params={"sleep": True}),
            )

    assert len(responses) == 2
    assert [r.status_code for r in responses] == [200] * 2
    assert [r.text for r in responses] == ["Success"] * 2

    spans = tracer.writer.pop_traces()
    assert len(spans) == 2
    assert len(spans[0]) == 1
    assert len(spans[1]) == 1

    r1_span = spans[0][0]
    assert r1_span.service == "starlette"
    assert r1_span.name == "starlette.request"
    assert r1_span.get_tag("http.method") == "GET"
    assert r1_span.get_tag("http.url") == "http://testserver/"
    assert r1_span.get_tag("http.query.string") == "sleep=true"

    r2_span = spans[0][0]
    assert r2_span.service == "starlette"
    assert r2_span.name == "starlette.request"
    assert r2_span.get_tag("http.method") == "GET"
    assert r2_span.get_tag("http.url") == "http://testserver/"
    assert r2_span.get_tag("http.query.string") == "sleep=true"


def test_streaming_response(client, tracer):
    r = client.get("/stream")

    assert r.status_code == 200

    assert r.text.endswith("streaming")

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/stream"
    assert request_span.get_tag("http.query.string") is None
    assert request_span.get_tag("http.status_code") == "200"


def test_file_response(client, tracer):
    r = client.get("/file")

    assert r.status_code == 200
    assert r.text == "Datadog says hello!"

    spans = tracer.writer.pop_traces()
    assert len(spans) == 1
    assert len(spans[0]) == 1
    request_span = spans[0][0]
    assert request_span.service == "starlette"
    assert request_span.name == "starlette.request"
    assert request_span.error == 0
    assert request_span.get_tag("http.method") == "GET"
    assert request_span.get_tag("http.url") == "http://testserver/file"
    assert request_span.get_tag("http.query.string") is None
    assert request_span.get_tag("http.status_code") == "200"
