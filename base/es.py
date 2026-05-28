from __future__ import annotations

from elasticsearch import Elasticsearch

from settings import ES_API_KEY, ES_HOSTS, ES_PASSWORD, ES_REQUEST_TIMEOUT, ES_USERNAME

_client: Elasticsearch | None = None


def _parse_hosts(hosts: str) -> list[str]:
    return [host.strip() for host in hosts.split(",") if host.strip()]


def get_es_client() -> Elasticsearch:
    global _client

    if _client is not None:
        return _client

    hosts = _parse_hosts(ES_HOSTS)
    if not hosts:
        msg = "ES_HOSTS is required to create an Elasticsearch client"
        raise RuntimeError(msg)

    kwargs: dict[str, object] = {
        "hosts": hosts,
        "request_timeout": ES_REQUEST_TIMEOUT,
    }

    if ES_API_KEY:
        kwargs["api_key"] = ES_API_KEY
    elif ES_USERNAME and ES_PASSWORD:
        kwargs["basic_auth"] = (ES_USERNAME, ES_PASSWORD)
    elif ES_USERNAME or ES_PASSWORD:
        msg = "ES_USERNAME and ES_PASSWORD must be configured together"
        raise RuntimeError(msg)

    _client = Elasticsearch(**kwargs)
    return _client


def close_es_client() -> None:
    global _client

    if _client is not None:
        try:
            _client.close()
        finally:
            _client = None
