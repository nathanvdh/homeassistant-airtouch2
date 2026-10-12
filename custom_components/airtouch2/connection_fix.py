"""Reliable reconnects for the airtouch2 library's network client.

The library (airtouch2 0.8.6 and 0.8.7) only notices a lost connection when the
socket reports an error. A connection that dies silently, for example after a
Wi-Fi hiccup, leaves the client waiting forever and Home Assistant stops
receiving updates while the integration still shows as loaded.

airtouch2 0.8.7 tries to fix this with TCP keepalive, but its helper checks for
the keepalive constants on the socket object instead of the socket module, so
SO_KEEPALIVE and TCP_KEEPIDLE are never set and keepalive stays off.

This module patches NetClient.connect so that, on every successful connection:
- keepalive is switched on properly, so a dead connection is detected within
  about 10 seconds, even when idle, and the library's own reconnect runs;
- the previous connection is closed first, so stale connections do not pile
  up on the AirTouch's Wi-Fi module.

It works with airtouch2 0.8.6 and 0.8.7. Once the library fixes this itself,
this module can be removed.
"""
from __future__ import annotations

import asyncio
import logging
import socket

from airtouch2.common.NetClient import NetClient

_LOGGER = logging.getLogger(__name__)

# Same values the library author chose in 0.8.7: probe after 5 seconds idle,
# then every second, give up after 5 missed probes (about 10 seconds in total).
KEEPALIVE_IDLE_SECONDS = 5
KEEPALIVE_INTERVAL_SECONDS = 1
KEEPALIVE_COUNT = 5

_PATCHED_FLAG = "_airtouch2_connection_fix_applied"


def set_keepalive(sock, idle: int, interval: int, count: int) -> None:
    """Switch on TCP keepalive, checking the socket module for each option."""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    if hasattr(socket, "TCP_KEEPIDLE"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle)
    if hasattr(socket, "TCP_KEEPINTVL"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval)
    if hasattr(socket, "TCP_KEEPCNT"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, count)
    if hasattr(socket, "TCP_USER_TIMEOUT"):
        sock.setsockopt(
            socket.IPPROTO_TCP,
            socket.TCP_USER_TIMEOUT,
            1000 * (idle + interval * count),
        )


async def close_writer(writer: asyncio.StreamWriter | None) -> None:
    """Close a stream writer, ignoring errors from an already dead connection."""
    if writer is None:
        return
    try:
        writer.close()
        await asyncio.wait_for(writer.wait_closed(), timeout=2)
    except Exception:  # noqa: BLE001 - the connection is being thrown away
        pass


def apply() -> None:
    """Patch NetClient.connect once per Home Assistant run."""
    if getattr(NetClient, _PATCHED_FLAG, False):
        return

    original_connect = NetClient.connect

    async def connect(self: NetClient) -> bool:
        old_writer = self._writer
        if old_writer is not None and not old_writer.is_closing():
            _LOGGER.debug("Closing previous connection to %s", self._host_ip)
            await close_writer(old_writer)

        connected = await original_connect(self)
        if connected and self._writer is not None:
            sock = self._writer.get_extra_info("socket")
            if sock is not None:
                try:
                    set_keepalive(
                        sock,
                        KEEPALIVE_IDLE_SECONDS,
                        KEEPALIVE_INTERVAL_SECONDS,
                        KEEPALIVE_COUNT,
                    )
                except OSError as err:
                    _LOGGER.warning("Could not enable TCP keepalive: %s", err)
        return connected

    NetClient.connect = connect
    setattr(NetClient, _PATCHED_FLAG, True)
    _LOGGER.debug("Applied airtouch2 connection fix")
