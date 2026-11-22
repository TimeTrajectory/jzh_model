"""Runtime TSG/TEM loader patch for Ultralytics without duplicate image datasets."""
from pathlib import Path
import re
import cv2


def install(encoding: str):
    if encoding == "rgb":
        return
    if encoding not in {"tsg", "tem"}:
        raise ValueError(encoding)
    import ultralytics.data.base as base
    original = base.imread
    pattern = re.compile(r"^(.*_)(\d+)$")

    def neighbor(path: Path, delta: int):
        match = pattern.match(path.stem)
        if not match:
            return path
        number = int(match.group(2)) + delta
        candidate = path.with_name(f"{match.group(1)}{number:0{len(match.group(2))}d}{path.suffix}")
        return candidate if candidate.exists() else path

    def temporal_imread(filename, flags=cv2.IMREAD_COLOR):
        path = Path(filename)
        current_bgr = original(str(path), flags=cv2.IMREAD_COLOR)
        if current_bgr is None:
            return None
        previous_bgr = original(str(neighbor(path, -1)), flags=cv2.IMREAD_COLOR)
        following_bgr = original(str(neighbor(path, 1)), flags=cv2.IMREAD_COLOR)
        current = cv2.cvtColor(current_bgr, cv2.COLOR_BGR2GRAY)
        previous = cv2.cvtColor(previous_bgr, cv2.COLOR_BGR2GRAY)
        following = cv2.cvtColor(following_bgr, cv2.COLOR_BGR2GRAY)
        if encoding == "tsg":
            return cv2.merge((previous, current, following))
        return cv2.merge((cv2.absdiff(current, previous), current, cv2.absdiff(current, following)))

    base.imread = temporal_imread
