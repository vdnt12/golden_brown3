"""PDF parsing and page rendering in a resource-limited child process (Guide 6.2).

Why a child process: PDFium is C++ and can be made to loop, allocate or crash on
malicious input. Running it out-of-process means a hang or a crash costs one
subprocess, not the API server.

Limits applied in the child (POSIX):
  * RLIMIT_CPU      -- CPU seconds
  * RLIMIT_AS       -- address space (skipped on macOS, where it is unreliable)
  * wall-clock      -- enforced by the parent with terminate()
  * output cap      -- total extracted characters
  * page cap        -- configured maximum

On Windows `resource` is unavailable; the parent wall-clock timeout, output cap
and page cap still apply. `limits_report()` states this honestly at startup.
"""
from __future__ import annotations

import contextlib
import multiprocessing as mp
import struct
import sys
import zlib
from dataclasses import dataclass, field
from typing import Any

from app.ingest.errors import (
    ParserLimitError,
    ParserTimeoutError,
    ParserUnavailable,
    PdfEncryptedError,
    PdfMalformedError,
)

MAX_CHILD_ADDRESS_SPACE = 1_500 * 1024 * 1024  # 1.5 GiB
MAX_CHILD_CPU_SECONDS = 60


class WorkerFailure(RuntimeError):
    """Raised in the child; transported to the parent as (code, message)."""

    code = "WORKER_FAILURE"


@dataclass
class WorkerPage:
    page_no: int
    text: str


@dataclass
class WorkerResult:
    pages: list[WorkerPage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# capability reporting
# ---------------------------------------------------------------------------


def limits_report() -> dict[str, Any]:
    posix = sys.platform != "win32"
    return {
        "platform": sys.platform,
        "child_process": True,
        "cpu_limit": posix,
        "address_space_limit": posix and sys.platform != "darwin",
        "wall_clock_timeout": True,
        "output_cap": True,
        "page_cap": True,
        "startup_notice": (
            ""
            if posix and sys.platform != "darwin"
            else "Reduced parser isolation on this platform: "
            + ("macOS address-space limits are unreliable; " if sys.platform == "darwin" else "Windows has no rlimits; ")
            + "wall-clock timeout, output cap and page cap still apply."
        ),
    }


def _apply_limits() -> None:
    if sys.platform == "win32":
        return
    try:
        import resource
    except ImportError:  # pragma: no cover
        return
    with contextlib.suppress(ValueError, OSError):
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_CHILD_CPU_SECONDS, MAX_CHILD_CPU_SECONDS + 5))
    if sys.platform != "darwin":
        with contextlib.suppress(ValueError, OSError):
            resource.setrlimit(
                resource.RLIMIT_AS, (MAX_CHILD_ADDRESS_SPACE, MAX_CHILD_ADDRESS_SPACE)
            )


# ---------------------------------------------------------------------------
# child entry points
# ---------------------------------------------------------------------------


def _extract_child(data: bytes, max_pages: int, output_cap: int, conn: Any) -> None:
    _apply_limits()
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - dependency present in CI
        conn.send(("UNAVAILABLE", str(exc)))
        return

    try:
        document = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        message = str(exc).lower()
        if "password" in message or "security" in message:
            conn.send(("ENCRYPTED", str(exc)))
        else:
            conn.send(("MALFORMED", str(exc)))
        return
    except Exception as exc:  # noqa: BLE001 - PDFium raises its own exception types
        conn.send(("MALFORMED", str(exc)))
        return

    try:
        page_count = len(document)
        if page_count > max_pages:
            conn.send(("LIMIT", f"document has {page_count} pages; cap is {max_pages}"))
            return
        pages: list[tuple[int, str]] = []
        warnings: list[str] = []
        total = 0
        for index in range(page_count):
            try:
                textpage = document[index].get_textpage()
                text = textpage.get_text_bounded()
            except Exception as exc:  # noqa: BLE001 - one bad page must not kill the run
                warnings.append(f"page {index + 1} could not be extracted: {type(exc).__name__}")
                text = ""
            total += len(text)
            if total > output_cap:
                conn.send(("LIMIT", f"extracted text exceeds {output_cap} characters"))
                return
            pages.append((index + 1, text))
        conn.send(("OK", {"pages": pages, "warnings": warnings}))
    finally:
        with contextlib.suppress(Exception):
            document.close()


def _render_child(data: bytes, page_no: int, scale: float, conn: Any) -> None:
    _apply_limits()
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover
        conn.send(("UNAVAILABLE", str(exc)))
        return
    try:
        document = pdfium.PdfDocument(data)
    except Exception as exc:  # noqa: BLE001
        conn.send(("MALFORMED", str(exc)))
        return
    try:
        if not 1 <= page_no <= len(document):
            conn.send(("LIMIT", "page outside document"))
            return
        bitmap = document[page_no - 1].render(scale=scale)
        buffer = bytes(bitmap.buffer)
        conn.send(
            (
                "OK",
                {"png": _png_from_bitmap(buffer, bitmap.width, bitmap.height, bitmap.stride)},
            )
        )
    except Exception as exc:  # noqa: BLE001
        conn.send(("RENDER", str(exc)))
    finally:
        with contextlib.suppress(Exception):
            document.close()


def _png_from_bitmap(buffer: bytes, width: int, height: int, stride: int) -> bytes:
    """Minimal PNG encoder (BGR or BGRA -> RGB). Avoids a Pillow dependency."""
    channels = max(3, stride // max(width, 1))
    if channels not in (3, 4):
        raise ValueError(f"unsupported bitmap stride ({stride} for width {width})")
    rows = bytearray()
    for y in range(height):
        start = y * stride
        row = buffer[start : start + width * channels]
        rgb = bytearray(width * 3)
        if channels == 4:
            rgb[0::3] = row[2::4]
            rgb[1::3] = row[1::4]
            rgb[2::3] = row[0::4]
        else:
            rgb[0::3] = row[2::3]
            rgb[1::3] = row[1::3]
            rgb[2::3] = row[0::3]
        rows.append(0)  # filter type: none
        rows.extend(rgb)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(rows), 6))
        + chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------------------
# parent side
# ---------------------------------------------------------------------------


def _child_context() -> Any:
    """Use spawn on macOS and Windows; fork on other POSIX systems.

    macOS: fork() is unsafe in multithreaded processes (Python 3.14+ deprecates
    it, and pypdfium2 initialises CoreGraphics in the child which segfaults after
    a fork from a threaded parent). spawn() creates a clean child.
    Other POSIX (Linux): fork() is fine and cheaper (no module re-import).
    """
    if sys.platform == "darwin" or sys.platform == "win32":
        return mp.get_context("spawn")
    methods = mp.get_all_start_methods()
    return mp.get_context("fork" if "fork" in methods else "spawn")


def _run_child(target: Any, args: tuple[Any, ...], timeout_s: float) -> Any:
    context = _child_context()
    parent_conn, child_conn = context.Pipe(duplex=False)
    process = context.Process(target=target, args=(*args, child_conn), daemon=True)
    process.start()
    child_conn.close()
    try:
        if not parent_conn.poll(timeout_s):
            process.terminate()
            process.join(timeout=5)
            raise ParserTimeoutError(f"parser exceeded {timeout_s:.0f}s wall clock")
        code, payload = parent_conn.recv()
    except EOFError as exc:
        raise PdfMalformedError("parser child exited without a result") from exc
    finally:
        parent_conn.close()
        if process.is_alive():
            process.terminate()
        process.join(timeout=5)

    if code == "OK":
        return payload
    if code == "UNAVAILABLE":
        raise ParserUnavailable("pypdfium2 is not installed")
    if code == "ENCRYPTED":
        raise PdfEncryptedError("PDF is password-protected")
    if code == "LIMIT":
        raise ParserLimitError(str(payload))
    if code == "RENDER":
        raise PdfMalformedError(f"page render failed: {payload}")
    raise PdfMalformedError(f"PDF could not be parsed: {payload}")


def extract_pdf(
    data: bytes,
    *,
    max_pages: int = 300,
    timeout_s: float = 30.0,
    output_cap: int = 20 * 1024 * 1024,
) -> WorkerResult:
    payload = _run_child(_extract_child, (data, max_pages, output_cap), timeout_s)
    return WorkerResult(
        pages=[WorkerPage(page_no=no, text=text) for no, text in payload["pages"]],
        warnings=list(payload["warnings"]),
    )


def render_pdf_page(
    data: bytes, page_no: int, *, scale: float = 1.5, timeout_s: float = 30.0
) -> bytes:
    payload = _run_child(_render_child, (data, page_no, scale), timeout_s)
    return payload["png"]
