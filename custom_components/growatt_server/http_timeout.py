"""Default socket-level timeout for growattServer's HTTP session.

growattServer's requests.Session calls (both the Classic and the Open API V1
client) never pass timeout=. When a connection gets silently dropped instead
of reset (no RST/FIN - the Growatt cloud does this occasionally, see
coordinator.py's MAX_TRANSIENT_FAILURES comment for the "cleanly reset"
case), the blocking call inside _sync_update_data hangs forever on the
executor thread. Because _async_update_data never returns, the coordinator
never logs anything further and never reschedules its next poll - the
integration goes silent and every one of its entities freezes at whatever
value they last held, with no error anywhere to point at.

Mounting an adapter that fills in a default timeout turns that hang into a
requests.exceptions.Timeout (a RequestException subclass), which
coordinator.py's existing transient-error handling already retries and
caches correctly - no other change needed.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter

# (connect, read) seconds. A real call normally completes in ~2-3s; this
# stays generous relative to that while still resolving well inside
# coordinator.py's 5-minute SCAN_INTERVAL, even for the "min" device type's
# three sequential calls per poll.
DEFAULT_API_TIMEOUT = (10, 30)


class _DefaultTimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that fills in a default timeout when the caller omits one."""

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = DEFAULT_API_TIMEOUT
        return super().send(request, **kwargs)


def apply_default_timeout(api: object) -> None:
    """Mount the default-timeout adapter on a growattServer API client's session.

    Takes the api object rather than api.session directly because the test
    suite's autospec'd API doubles don't carry `session` - it's a runtime
    instance attribute `GrowattApi.__init__` sets, invisible to autospec's
    class introspection - so accessing it on those mocks would raise
    AttributeError. Looking it up defensively lets this no-op against a test
    double while still applying to every real api instance.
    """
    session = getattr(api, "session", None)
    if not isinstance(session, requests.Session):
        return
    adapter = _DefaultTimeoutHTTPAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
