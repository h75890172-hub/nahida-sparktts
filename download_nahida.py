import hashlib
import math
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests


ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com").rstrip("/")
BASE_REPO = "wesjos/spark-tts-genshin-charactors"
CHARACTER_REPO = "wesjos/spark-tts-genshin-charactors-new"
BASE_REPO_REVISION = "f22c47a417ca8379c70e1388331e25bd0407a61f"
CHARACTER_REPO_REVISION = "15d4ca3dc31389edd906e6f52bc2c56b2563c57b"
CHARACTER_FOLDER = "纳西妲"
OUTPUT_ROOT = Path(__file__).resolve().parent / "genshin"
CHUNK_SIZE = 8 * 1024 * 1024
MAX_RETRIES = 8
PARALLEL_THRESHOLD = 64 * 1024 * 1024
SEGMENT_SIZE = 96 * 1024 * 1024
MAX_WORKERS = 8


def get_remote_files(repo_id: str, revision: str, prefix: str) -> list[dict]:
    response = requests.get(
        f"{ENDPOINT}/api/models/{repo_id}",
        params={"blobs": "true", "revision": revision},
        timeout=60,
    )
    response.raise_for_status()
    files = []
    for item in response.json()["siblings"]:
        filename = item["rfilename"]
        if filename.startswith(prefix) and filename != f"{prefix}.gitattributes":
            files.append(item)
    return files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def file_matches(path: Path, expected_size: int, expected_sha256: str | None) -> bool:
    if not path.is_file() or path.stat().st_size != expected_size:
        return False
    if expected_sha256 and sha256_file(path) != expected_sha256:
        return False
    return True


def find_aria2c() -> str | None:
    configured = os.getenv("ARIA2C")
    if configured and Path(configured).is_file():
        return configured
    discovered = shutil.which("aria2c")
    if discovered:
        return discovered
    return None


def aria2_download(url: str, destination: Path) -> Path:
    aria2c = find_aria2c()
    if not aria2c:
        raise RuntimeError("aria2c executable was not found")

    partial = destination.with_suffix(destination.suffix + ".aria2part")
    command = [
        aria2c,
        "--continue=true",
        "--max-connection-per-server=8",
        "--split=8",
        "--min-split-size=1M",
        "--file-allocation=none",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--max-tries=8",
        "--retry-wait=3",
        "--connect-timeout=30",
        "--timeout=300",
        "--dir",
        str(destination.parent),
        "--out",
        partial.name,
        url,
    ]
    subprocess.run(command, check=True)
    return partial


def cleanup_stale_partials(destination: Path) -> None:
    for path in destination.parent.glob(destination.name + ".part*"):
        if path.is_file():
            path.unlink()


def download_once(url: str, destination: Path, expected_size: int) -> None:
    if expected_size >= PARALLEL_THRESHOLD:
        if find_aria2c():
            partial = aria2_download(url, destination)
        else:
            parallel_download(url, destination, expected_size)
            return
        actual_size = partial.stat().st_size
        if actual_size != expected_size:
            raise RuntimeError(
                f"size mismatch for {destination.name}: "
                f"expected {expected_size}, got {actual_size}"
            )
        os.replace(partial, destination)
        return

    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists() and partial.stat().st_size > expected_size:
        partial.unlink()

    command = [
        "curl.exe",
        "--location",
        "--fail",
        "--retry",
        str(MAX_RETRIES),
        "--retry-all-errors",
        "--retry-delay",
        "3",
        "--connect-timeout",
        "30",
        "--continue-at",
        "-",
        "--output",
        str(partial),
        url,
    ]
    subprocess.run(command, check=True)
    actual_size = partial.stat().st_size
    if actual_size != expected_size:
        raise RuntimeError(
            f"size mismatch for {destination.name}: "
            f"expected {expected_size}, got {actual_size}"
        )
    os.replace(partial, destination)


def download_segment(
    url: str,
    segment_path: Path,
    start: int,
    end: int,
) -> None:
    expected_size = end - start + 1

    for attempt in range(1, MAX_RETRIES + 1):
        existing_size = segment_path.stat().st_size if segment_path.exists() else 0
        if existing_size == expected_size:
            return
        if existing_size:
            segment_path.unlink()

        command = [
            "curl.exe",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            str(MAX_RETRIES),
            "--retry-all-errors",
            "--retry-delay",
            "3",
            "--connect-timeout",
            "30",
            "--http1.1",
            "--range",
            f"{start}-{end}",
            "--output",
            str(segment_path),
            url,
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as error:
            if attempt == MAX_RETRIES:
                raise
            print(f"  segment retry {attempt}/{MAX_RETRIES}: {error}")
            time.sleep(min(attempt * 3, 15))

        actual_size = segment_path.stat().st_size if segment_path.exists() else 0
        if actual_size == expected_size:
            return
        if attempt == MAX_RETRIES:
            raise RuntimeError(
                f"segment size mismatch: expected {expected_size}, got {actual_size}"
            )


def parallel_download(url: str, destination: Path, expected_size: int) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    segment_count = max(2, math.ceil(expected_size / SEGMENT_SIZE))
    segment_count = min(segment_count, MAX_WORKERS)
    segment_size = math.ceil(expected_size / segment_count)
    ranges = []
    for index in range(segment_count):
        start = index * segment_size
        end = min(start + segment_size - 1, expected_size - 1)
        ranges.append((index, start, end))

    print(f"  parallel segments: {segment_count}")
    with ThreadPoolExecutor(max_workers=segment_count) as executor:
        futures = {
            executor.submit(
                download_segment,
                url,
                destination.with_suffix(destination.suffix + f".part.{index}"),
                start,
                end,
            ): index
            for index, start, end in ranges
        }
        for future in as_completed(futures):
            future.result()

    with partial.open("wb") as output:
        for index, _, _ in ranges:
            segment_path = destination.with_suffix(
                destination.suffix + f".part.{index}"
            )
            with segment_path.open("rb") as segment:
                while chunk := segment.read(CHUNK_SIZE):
                    output.write(chunk)
            segment_path.unlink()

    actual_size = partial.stat().st_size
    if actual_size != expected_size:
        raise RuntimeError(
            f"size mismatch for {destination.name}: "
            f"expected {expected_size}, got {actual_size}"
        )
    os.replace(partial, destination)


def download_file(
    repo_id: str,
    revision: str,
    item: dict,
    relative_path: Path,
) -> None:
    expected_size = int(item["size"])
    expected_sha256 = (item.get("lfs") or {}).get("sha256")
    destination = OUTPUT_ROOT / relative_path

    if file_matches(destination, expected_size, expected_sha256):
        print(f"[skip] {relative_path}")
        cleanup_stale_partials(destination)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded_path = quote(item["rfilename"], safe="/")
    url = f"{ENDPOINT}/{repo_id}/resolve/{revision}/{encoded_path}"

    print(
        f"[download] {relative_path} "
        f"({expected_size / 1024**3:.2f} GiB)"
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            download_once(url, destination, expected_size)
            break
        except (requests.RequestException, subprocess.CalledProcessError, RuntimeError) as error:
            if attempt == MAX_RETRIES:
                raise
            print(f"  retry {attempt}/{MAX_RETRIES}: {error}")
            time.sleep(min(attempt * 3, 15))

    if not file_matches(destination, expected_size, expected_sha256):
        raise RuntimeError(f"checksum failed for {destination}")
    cleanup_stale_partials(destination)


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    base_files = get_remote_files(
        BASE_REPO,
        BASE_REPO_REVISION,
        "Spark-TTS-0.5B/",
    )
    character_files = get_remote_files(
        CHARACTER_REPO,
        CHARACTER_REPO_REVISION,
        f"{CHARACTER_FOLDER}/",
    )
    if not character_files:
        raise RuntimeError(f"No remote files found for {CHARACTER_FOLDER}")

    for item in base_files:
        download_file(
            BASE_REPO,
            BASE_REPO_REVISION,
            item,
            Path(item["rfilename"]),
        )

    for item in character_files:
        relative_path = Path(item["rfilename"])
        download_file(
            CHARACTER_REPO,
            CHARACTER_REPO_REVISION,
            item,
            relative_path,
        )

    print(f"Models ready in {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
