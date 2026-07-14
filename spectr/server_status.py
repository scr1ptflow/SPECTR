# Live Elite Dangerous server status checker
# Uses QNetworkAccessManager for non-blocking async HEAD requests
# to Frontier's auth and game servers.

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

log = logging.getLogger(__name__)


class ServerStatusChecker(QObject):
    """Periodically probes Frontier's servers and emits status changes.

    Emits:
        status_changed(str) — "ONLINE", "OFFLINE", "MAINTENANCE", or "UNKNOWN"
    """

    status_changed = Signal(str)

    _AUTH_URL = QUrl("https://auth.frontierstore.net/")
    _GAME_URL = QUrl("https://elite.frontier.co.uk/")
    _TIMEOUT_MS = 10_000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last = "UNKNOWN"
        self._nam = QNetworkAccessManager(self)
        self._count = 0
        self._results: dict[str, bool] = {}

    def start(self, interval_ms: int = 120_000) -> None:
        """Start periodic checking. Fires immediately, then every *interval_ms*."""
        self.check()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.check)
        self._timer.start(interval_ms)

    def check(self) -> None:
        """Fire async HEAD requests to auth and game servers."""
        if self._count > 0:
            return
        self._count = 0
        self._results = {}
        for key, url in [("auth", self._AUTH_URL), ("game", self._GAME_URL)]:
            req = QNetworkRequest(url)
            req.setTransferTimeout(self._TIMEOUT_MS)
            reply = self._nam.head(req)
            reply.finished.connect(lambda k=key, r=reply: self._on_reply(k, r))
            self._count += 1

    def _on_reply(self, key: str, reply: QNetworkReply) -> None:
        err = reply.error()
        if err == QNetworkReply.NoError:
            self._results[key] = True
        elif err in (
            QNetworkReply.ConnectionRefusedError,
            QNetworkReply.OperationCanceledError,
            QNetworkReply.TimeoutError,
            QNetworkReply.HostNotFoundError,
        ):
            self._results[key] = False
        else:
            status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            self._results[key] = bool(status and status < 500)

        self._count -= 1
        if self._count <= 0:
            self._evaluate()
        reply.deleteLater()

    def _evaluate(self) -> None:
        auth = self._results.get("auth")
        game = self._results.get("game")
        if auth and game:
            s = "ONLINE"
        elif auth and not game:
            s = "MAINTENANCE"
        elif not auth and not game:
            s = "OFFLINE"
        else:
            s = "UNKNOWN"
        if s != self._last:
            self._last = s
            log.info("Server status changed: %s", s)
            self.status_changed.emit(s)
