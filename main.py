"""Entry program for news-image-20261119, round 3.

Why this file only copies: the competition sandbox runs the entry
with the Python 3.13 standard library alone and nothing installed,
so the Pillow renderer that drew this picture cannot run there.
The rules bless the simple shape used here instead: the repository
holds the finished image and the program copies it into place.

The picture itself is entry.png beside this file, drawn locally by
draw.py from the checked stories in stories.json. Running this
program puts a byte-identical copy at entry.png inside the folder
named by MAKEFUN_OUTPUT_DIR, falling back to /output, which is
where the grader looks for it. No network, no input, and the same
bytes every run.
"""

import os
import shutil
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    shutil.copyfile(source, target)
    print("wrote", target)


if __name__ == "__main__":
    main()
