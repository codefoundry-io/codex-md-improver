"""Validate and package the portable skill subtree without publishing it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


ALLOWLIST = sorted([
    "LICENSE", "SKILL.md", "agents/openai.yaml", "assets/criteria.json", "assets/defaults.json",
    "references/assessment-format.md", "references/recognition-probes.md", "references/review-rules.md",
    "scripts/discovery.py", "scripts/lint_candidates.py", "scripts/md_improver.py",
    "scripts/recognition.py", "scripts/references.py", "scripts/reporting.py",
])
ARCHIVE_ROOT = "codex-md-improver/"
VERSION_PATTERN = re.compile(r"v?\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", re.ASCII)
LOCAL_PATH_PATTERN = re.compile(r"/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\Users\\")


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def file_record(name, data):
    return {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def verify_package(archive_path: Path, manifest: dict) -> bool:
    """Verify exact selected members and byte hashes; no provenance attestation."""
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "version", "files"}:
        raise ValueError("Invalid manifest fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported manifest version")
    if not isinstance(manifest["version"], str) or not VERSION_PATTERN.fullmatch(manifest["version"]):
        raise ValueError("Invalid package version")
    rows = manifest["files"]
    if not isinstance(rows, list) or any(not isinstance(row, dict) or set(row) != {"path", "size", "sha256"} for row in rows):
        raise ValueError("Invalid file records")
    if [row["path"] for row in rows] != ALLOWLIST:
        raise ValueError("Manifest does not match selected file allowlist")
    expected = {ARCHIVE_ROOT + name for name in ALLOWLIST} | {ARCHIVE_ROOT + "MANIFEST.json"}
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("Unexpected, missing or duplicate archive members")
        if archive.read(ARCHIVE_ROOT + "MANIFEST.json") != json_bytes(manifest):
            raise ValueError("Embedded/external manifest mismatch")
        for row in rows:
            actual = file_record(row["path"], archive.read(ARCHIVE_ROOT + row["path"]))
            if actual != row or type(row["size"]) is not int:
                raise ValueError("File hash or size mismatch")
    return True


def build_package(skill_root: Path, out_dir: Path, version: str) -> dict:
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Invalid package version")
    source = Path(skill_root).resolve(strict=True)
    output = Path(out_dir)
    if not source.is_dir():
        raise ValueError("Skill source must be a directory")
    if (not output.is_absolute() or output.exists() or output.is_symlink()
            or output.resolve().is_relative_to(source) or source.is_relative_to(output.resolve())):
        raise ValueError("Output must be a new absolute directory outside the source")
    paths = list(source.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("Source symlinks are not package resources")
    files = sorted(path.relative_to(source).as_posix() for path in paths if path.is_file())
    if files != ALLOWLIST:
        raise ValueError("Missing or unexpected source files: " + repr(sorted(set(files) ^ set(ALLOWLIST))))
    contents = {name: (source / name).read_bytes() for name in ALLOWLIST}
    for name, data in contents.items():
        try:
            text = data.decode("utf-8")
        except UnicodeError as error:
            raise ValueError("Non-text package resource: " + name) from error
        if LOCAL_PATH_PATTERN.search(text):
            raise ValueError("Machine-specific path in package resource: " + name)
    manifest = {"schema_version": 1, "version": version,
                "files": [file_record(name, contents[name]) for name in ALLOWLIST]}
    members = {ARCHIVE_ROOT + name: contents[name] for name in ALLOWLIST}
    members[ARCHIVE_ROOT + "MANIFEST.json"] = json_bytes(manifest)
    output.mkdir(parents=True, exist_ok=False)
    archive_path = output / ("codex-md-improver-" + version + ".zip")
    with zipfile.ZipFile(archive_path, "x") as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    manifest_path = output / "manifest.json"
    manifest_path.write_bytes(json_bytes(manifest))
    verify_package(archive_path, manifest)
    return {"archive": str(archive_path), "manifest": str(manifest_path), "files": manifest["files"],
            "version": version, "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build_package(args.skill_root, args.out_dir, args.version), indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print("Package error: " + str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
