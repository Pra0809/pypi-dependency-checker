"""
Usage:
    python check_requirements.py requirements.txt
"""

import json
import sys
import urllib.error
import urllib.request

PYPI = "https://pypi.org/pypi"


def fetch_json(url):
    """Return the parsed JSON response, or None if PyPI returns 404."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def read_requirements(path):
    """Return non-empty, non-comment lines from the requirements file."""
    with open(path, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def check(lines):
    """Check each 'name==version' line against PyPI and collect the results."""
    missing_packages = 0
    missing_versions = 0
    oldest = None  

    for line in lines:
        name, _, version = line.partition("==")
        name, version = name.strip(), version.strip()

        
        if fetch_json(f"{PYPI}/{name}/json") is None:
            missing_packages += 1
            continue

        if not version:
            continue  

       
        release = fetch_json(f"{PYPI}/{name}/{version}/json")
        if release is None:
            missing_versions += 1
            continue

        
        files = release.get("urls") or []
        if files:
            upload_time = files[0]["upload_time"]
            if oldest is None or upload_time < oldest[0]:
                oldest = (upload_time, name, version)

    return missing_packages, missing_versions, oldest


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    lines = read_requirements(path)
    missing_packages, missing_versions, oldest = check(lines)

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {missing_packages}")
    print(f"Versions not on PyPI: {missing_versions}")
    if oldest:
        upload_time, name, version = oldest
        print(f"Oldest pinned release: {name}=={version} ({upload_time[:4]})")
    else:
        print("Oldest pinned release: none")


if __name__ == "__main__":
    main()