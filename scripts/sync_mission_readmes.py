"""Keep per-mission README file lists current without rewriting hand-written text.

Run from anywhere with: python3 scripts/sync_mission_readmes.py
Only the region between AUTO-FILE-LIST markers is generated.
"""

from pathlib import Path
import re
from urllib.parse import quote


REPO = Path(__file__).resolve().parents[1]
MISSION_NAME = re.compile(r"^미션 (\d+)-(\d+)$")
START = "<!-- AUTO-FILE-LIST:START -->"
END = "<!-- AUTO-FILE-LIST:END -->"


def mission_directories():
    folders = []
    for entry in REPO.iterdir():
        match = MISSION_NAME.fullmatch(entry.name)
        if entry.is_dir() and match:
            folders.append((int(match.group(1)), int(match.group(2)), entry))
    return [entry for _, _, entry in sorted(folders)]


def markdown_link(file_path: Path, mission_folder: Path) -> str:
    relative = file_path.relative_to(mission_folder)
    target = "./" + "/".join(quote(piece, safe="-_.~") for piece in relative.parts)
    label = relative.as_posix().replace("\\", "\\\\").replace("|", "\\|")
    label = label.replace("[", "\\[").replace("]", "\\]")
    return f"[{label}]({target})"


def generated_block(mission_folder: Path) -> str:
    files = sorted(
        (p for p in mission_folder.rglob("*") if p.is_file() and p.relative_to(mission_folder).as_posix() != "README.md"),
        key=lambda p: p.relative_to(mission_folder).as_posix().casefold(),
    )
    rows = [
        START,
        "## 현재 파일 목록 (자동 갱신)",
        "",
        "이 표는 파일이 추가·삭제·이름 변경될 때 자동으로 갱신됩니다. 위의 설명은 그대로 보존합니다.",
        "",
        "| 파일 경로 | 형식 |",
        "| --- | --- |",
    ]
    for item in files:
        suffix = item.suffix.lower().lstrip(".")
        kind = suffix.upper() if suffix else "파일"
        rows.append(f"| {markdown_link(item, mission_folder)} | {kind} |")
    if not files:
        rows.append("| 등록된 파일 없음 | — |")
    rows.append(END)
    return "\n".join(rows)


def update_readme(mission_folder: Path) -> bool:
    readme = mission_folder / "README.md"
    original = readme.read_text(encoding="utf-8") if readme.exists() else f"# {mission_folder.name} — 파일 안내\n"
    have_start, have_end = START in original, END in original
    if have_start != have_end or original.count(START) > 1 or original.count(END) > 1:
        raise ValueError(f"자동 갱신 구역의 시작·종료 표시를 확인해 주세요: {readme}")

    block = generated_block(mission_folder)
    if have_start:
        left = original[: original.index(START)]
        right = original[original.index(END) + len(END) :]
        updated = left + block + right
    else:
        updated = original.rstrip("\n") + "\n\n" + block + "\n"

    if updated == original:
        return False
    readme.write_text(updated, encoding="utf-8")
    return True


def main():
    for mission in mission_directories():
        if update_readme(mission):
            print(f"Updated: {mission.relative_to(REPO) / 'README.md'}")
        else:
            print(f"Unchanged: {mission.relative_to(REPO) / 'README.md'}")


if __name__ == "__main__":
    main()
