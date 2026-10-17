#!/usr/bin/env python3
"""Generate a structured, clean GitHub release summary based on git logs and update draft release."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile


def run_cmd(cmd: str) -> str:
    """Run shell command and return decoded output."""
    return subprocess.check_output(cmd, shell=True).decode("utf-8").strip()


def main() -> None:
    if len(sys.argv) > 1:
        git_range = sys.argv[1]
        tags = git_range.split("..")
        if len(tags) == 2:
            latest = tags[1]
        else:
            latest = run_cmd("git tag --sort=-v:refname | head -n 1")
    else:
        tag_output = run_cmd("git tag --sort=-v:refname | head -n 2")
        tags = tag_output.splitlines() if tag_output else []
        if len(tags) < 2:
            latest = tags[0] if tags else "HEAD"
            git_range = tags[0] if tags else "HEAD"
        else:
            latest = tags[0]
            git_range = f"{tags[1]}..{tags[0]}"

    print(f"Using range: {git_range} (target release: {latest})")

    try:
        log_output = run_cmd(f'git log --pretty=format:"- %s" {git_range}')
    except Exception as e:
        print(f"Error fetching git log: {e}")
        return

    sections: dict[str, list[str]] = {
        "feat": [],
        "data": [],
        "fix": [],
        "improve": [],
        "maintenance": [],
        "docs": [],
    }

    for line in log_output.splitlines():
        if "conductor" in line.lower() or "checkpoint" in line.lower():
            continue

        match = re.match(r"-\s*(\w+)(\([^)]+\))?:\s*(.*)", line)
        if not match:
            continue

        type_str, scope, msg = match.groups()
        msg = msg.strip()
        msg = msg[0].upper() + msg[1:] if msg else msg

        if scope:
            scope_clean = scope[1:-1]
            entry = f"- `{scope_clean}`: {msg}"
        else:
            entry = f"- {msg}"

        if type_str == "feat":
            if any(
                k in entry.lower() for k in ["dataset", "scrape", "series", "season"]
            ):
                sections["data"].append(entry)
            else:
                sections["feat"].append(entry)
        elif type_str in ["data", "scrape"]:
            sections["data"].append(entry)
        elif type_str == "fix":
            sections["fix"].append(entry)
        elif type_str in ["refactor", "perf", "style"]:
            sections["improve"].append(entry)
        elif type_str in ["chore", "ci", "build"]:
            sections["maintenance"].append(entry)
        elif type_str == "docs":
            sections["docs"].append(entry)

    summary: list[str] = []
    if sections["feat"]:
        summary.append(
            "### 🚀 **New Features**\n\n" + "\n".join(sections["feat"]) + "\n"
        )
    if sections["data"]:
        summary.append(
            "### 📊 **Dataset & Pipeline Updates**\n\n"
            + "\n".join(sections["data"])
            + "\n"
        )
    if sections["fix"]:
        summary.append("### 🐛 **Bug Fixes**\n\n" + "\n".join(sections["fix"]) + "\n")
    if sections["improve"]:
        summary.append(
            "### ✨ **Improvements**\n\n" + "\n".join(sections["improve"]) + "\n"
        )
    if sections["maintenance"]:
        summary.append(
            "### 🔧 **Maintenance & Automation**\n\n"
            + "\n".join(sections["maintenance"])
            + "\n"
        )
    if sections["docs"]:
        summary.append(
            "### 📝 **Documentation**\n\n" + "\n".join(sections["docs"]) + "\n"
        )

    if ".." in git_range:
        url_range = git_range.replace("..", "...")
        summary.append(
            f"**Full Changelog**: https://github.com/nicholaswilde/the-great-british-bake-off/compare/{url_range}\n"
        )
    else:
        summary.append(
            "**Commit History**: https://github.com/nicholaswilde/the-great-british-bake-off/commits/main\n"
        )

    notes = "\n".join(summary)
    print("\n--- Generated Release Notes ---")
    print(notes)
    print("--------------------------------\n")

    if latest == "HEAD":
        print("Latest is HEAD; skipping gh release edit.")
        return

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(notes)
        tmp_name = f.name

    print(f"Updating release notes for {latest}...")
    try:
        rel_info = run_cmd(f"gh release view {latest} --json isDraft")
        is_draft = '"isDraft":true' in rel_info.replace(" ", "")
        draft_flag = "--draft" if is_draft else ""
        url = run_cmd(f"gh release edit {latest} {draft_flag} -F {tmp_name}".strip())
        print(f"Release updated successfully: {url}")
    except Exception as e:
        print(f"Failed to update release with gh: {e}")
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


if __name__ == "__main__":
    main()
