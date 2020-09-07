import argparse
import os
from typing import Optional, Sequence

from .common import base64_string_to_bytes, process_nb


def base64_to_local_file(base64_string: str, image_path: str):
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as fh:
        fh.write(base64_string_to_bytes(base64_string))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    parser.add_argument(
        '--add-changes-to-staging',
        default=False, action='store_true',
        help='Automatically add new and changed files to staging')
    parser.add_argument(
        '--auto-commit-changes', default=False, action='store_true',
        help='Automatically commits added and changed files in staging')
    args = parser.parse_args(argv)

    retv = 0

    for filename in args.filenames:
        return_value = process_nb(filename=filename, **vars(args))
        retv |= return_value

    return retv


if __name__ == '__main__':
    exit(main())
