"""
GitHub auto-update: update *detection* + optional download & install.

Design rules:
  - fully optional: silent when offline, never blocks scanning
  - two sources, tried in order:
      1. GitHub Releases  (latest release tag + installer asset)
      2. version.json on the main branch (works before any release exists)
  - only the update check touches the network - documents never do

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from .. import GITHUB_REPO, REPO_URL, __version__

USER_AGENT = f"Attribo/{__version__}"
API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RAW_VERSION = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
RELEASES_PAGE = REPO_URL + "/releases"


def is_newer(candidate: str, current: str) -> bool:
    """Semver-ish tuple compare; 'v' prefixes and trailing text tolerated."""

    def parts(value):
        out = []
        for chunk in str(value).strip().lstrip("v").split("."):
            digits = "".join(ch for ch in chunk if ch.isdigit())
            out.append(int(digits) if digits else 0)
        while len(out) < 3:
            out.append(0)
        return tuple(out[:3])

    return parts(candidate) > parts(current)


def _get_json(url: str, timeout: float):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def check_for_update(timeout: float = 8.0) -> dict:
    """Never raises. Returns update info; update_available=False when offline."""
    info = {
        "current": __version__,
        "latest": "",
        "update_available": False,
        "download_url": "",
        "html_url": RELEASES_PAGE,
        "notes": "",
        "source": "",
    }

    try:
        data = _get_json(API_LATEST, timeout)
        tag = str(data.get("tag_name") or "").lstrip("v")
        if tag:
            info["latest"] = tag
            info["html_url"] = str(data.get("html_url") or info["html_url"])
            info["notes"] = str(data.get("body") or "")[:1500]
            for asset in data.get("assets") or []:
                name = str(asset.get("name", "")).lower()
                if name.endswith(".exe") and ("setup" in name or "installer" in name):
                    info["download_url"] = str(asset.get("browser_download_url") or "")
                    break
            info["source"] = "github-release"
            info["update_available"] = is_newer(info["latest"], __version__)
            return info
    except Exception:  # noqa: BLE001 - offline / rate limit / no releases yet
        pass

    try:
        data = _get_json(RAW_VERSION, timeout)
        tag = str(data.get("version") or "").lstrip("v")
        if tag:
            info["latest"] = tag
            info["download_url"] = str(data.get("download_url") or "")
            info["notes"] = str(data.get("notes") or "")[:1500]
            info["source"] = "version-json"
            info["update_available"] = is_newer(tag, __version__)
    except Exception:  # noqa: BLE001
        pass
    return info


def download_installer(url: str, timeout: float = 90.0, progress=None) -> str:
    """Streams the installer into %TEMP% and returns the local path."""
    if not str(url).lower().startswith(("http://", "https://")):
        raise RuntimeError("No installer download URL published with this update.")
    name = str(url).rsplit("/", 1)[-1] or "Attribo_Setup.exe"
    if not name.lower().endswith(".exe"):
        name = "Attribo_Setup.exe"
    target = Path(tempfile.gettempdir()) / f"Attribo_update_{name}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response, open(target, "wb") as fh:
        total = int(response.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = response.read(262144)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
            if progress and total:
                progress(
                    min(1.0, got / total),
                    f"Downloading update {got // 1048576}/{max(1, total // 1048576)} MB",
                )
    if target.stat().st_size < 1_000_000:
        raise RuntimeError("Downloaded installer is unexpectedly small - aborted.")
    return str(target)


def launch_installer(path: str) -> None:
    """Start the Inno Setup installer in silent update mode."""
    subprocess.Popen(
        [str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"], close_fds=True
    )
