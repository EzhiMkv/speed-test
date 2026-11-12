#!/usr/bin/env python3
"""Замер скорости скачивания: N последовательных GET-запросов к одному URL."""

import argparse
import http.client
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_COUNT = 10
DEFAULT_TIMEOUT = 30
USER_AGENT = "speed-test/1.0"


def download_once(url: str, timeout: float) -> tuple[int, float]:
    """Один GET-запрос; ждём полный ответ. Возвращает (байт, секунд)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    return len(body), time.perf_counter() - started


def format_bytes(value: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if value < 1000 or unit == "ГБ":
            return f"{value:.0f} {unit}" if unit == "Б" else f"{value:.2f} {unit}"
        value /= 1000


def format_seconds(seconds: float) -> str:
    return f"{seconds * 1000:.0f} мс" if seconds < 1 else f"{seconds:.2f} с"


def percentile(values: list[float], pct: float) -> float:
    """Линейная интерполяция по рангу, как в numpy.percentile."""
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)


def error_reason(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    reason = getattr(exc, "reason", None)
    return str(reason) if reason is not None else str(exc)


def request_row(label: str, elapsed: float, size: int) -> str:
    speed = size * 8 / elapsed / 1_000_000
    return f"  {label:<13} {format_seconds(elapsed):>9}  {format_bytes(size):>11}  {speed:>10.2f} Мбит/с"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="speed_test",
        description="Замер скорости скачивания: N последовательных запросов к одному URL.",
    )
    parser.add_argument("url", help="URL для скачивания (например, тяжёлая картинка)")
    parser.add_argument(
        "-n", "--count", type=int, default=DEFAULT_COUNT,
        help=f"количество запросов (по умолчанию {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help=f"тайм-аут одного запроса, секунд (по умолчанию {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--no-warmup", action="store_true",
        help="не делать прогревочный запрос перед замерами",
    )
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count должен быть >= 1")
    if args.timeout <= 0:
        parser.error("--timeout должен быть > 0")
    if urllib.parse.urlparse(args.url).scheme.lower() not in ("http", "https"):
        parser.error("URL должен начинаться с http:// или https://")
    return args


def main() -> int:
    args = parse_args()
    sizes: list[int] = []
    durations: list[float] = []

    print(f"URL: {args.url}")
    if args.no_warmup:
        print(f"Запросов: {args.count}\n")
    else:
        print(f"Запросов: {args.count} + прогрев\n")
        try:
            warm_size, warm_elapsed = download_once(args.url, args.timeout)
        except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
            print(f"  прогрев не удался ({error_reason(exc)}), замеры идут дальше", file=sys.stderr)
        else:
            print(request_row("прогрев:", warm_elapsed, warm_size))

    for i in range(1, args.count + 1):
        try:
            size, elapsed = download_once(args.url, args.timeout)
        except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
            print(f"  запрос {i:>2}/{args.count}: ошибка — {error_reason(exc)}", file=sys.stderr)
            continue
        sizes.append(size)
        durations.append(elapsed)
        print(request_row(f"запрос {i:>2}/{args.count}:", elapsed, size))

    if not durations:
        print("\nНи один запрос не завершился успешно.", file=sys.stderr)
        return 1

    total_bytes = sum(sizes)
    total_time = sum(durations)
    # Скорость = объём / сумма длительностей самих запросов, без пауз между ними.
    speed_mbit = total_bytes * 8 / total_time / 1_000_000
    speed_mbyte = speed_mbit / 8

    failed = args.count - len(durations)
    print("\n" + "─" * 46)
    print(f"Успешных запросов:     {len(durations)} из {args.count}")
    if failed:
        print(f"Неудачных запросов:    {failed}")
    print(f"Среднее время запроса: {format_seconds(total_time / len(durations))}")
    print(f"Мин/макс время:        {format_seconds(min(durations))} / {format_seconds(max(durations))}")
    print(f"Медиана (p50):         {format_seconds(percentile(durations, 50))}")
    print(f"p95:                   {format_seconds(percentile(durations, 95))}")
    print(f"Общий объём данных:    {format_bytes(total_bytes)}")
    print(f"Суммарное время:       {format_seconds(total_time)}")
    print(f"Скорость скачивания:   {speed_mbit:.2f} Мбит/с ({speed_mbyte:.2f} МБ/с)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.", file=sys.stderr)
        sys.exit(130)
