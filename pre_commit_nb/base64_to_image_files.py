import argparse
import re
import os
import base64
import uuid
from typing import List
from typing import Optional
from typing import Sequence
import subprocess


def base64_to_image_file(base64_string: str, image_path: str):
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as fh:
        fh.write(base64.decodebytes(base64_string.encode()))


def create_nb_cell_output(url: str) -> str:
    return """"text/html": [
            "<img src=\\"%s\\"/>"
        ]""" % url


def process_nb(
        filename: str,
        add_changes_to_staging: bool,
        auto_commit_changes: bool,
        **kwargs
        ) -> int:
    print("==================")
    print(add_changes_to_staging, auto_commit_changes)
    print("Processing %s" % filename)
    with open(filename, 'r') as file:
        data = " ".join(file.readlines())
        matches = re.findall(
            r"\"image/(?:gif|png|jpeg|bmp|webp)\": \".*[a-zA-Z0-9+/=]\"",
            data)

        new_files = ""

        for match in matches:
            ext = "." + re.findall(r"image/[a-zA-Z]*", match)[0].split('/')[1]
            image_path = "nb_images" + "/" + str(uuid.uuid4()) + ext

            full_path = "./" + os.path.dirname(filename) + "/" + image_path
            print("Base64 string found. Converting it to image file and saving as %s" % full_path)
            base64_string = match.split(':')[1].replace('"', '').replace(' ', '').replace('\\n', '')
            base64_to_image_file(base64_string, full_path)
            new_files += " " + full_path

            url_path = "./" + image_path
            data = data.replace(match, create_nb_cell_output(url_path))

    if len(new_files) > 0:
        with open(filename, 'w') as file:
            file.write(data)
            new_files += " " + filename

        if add_changes_to_staging:
            print("'--add_changes_to_staging' flag set to 'True' - added new and changed files to staging.")
            git_add(new_files)

        if auto_commit_changes:
            print("'--auto_commit_changes' flag set to 'True' - git hook set to return exit code 0.")
            return 0

        return 1
    else:
        print("Didn't find any base64 strings...")
        return 0


def git_add(filenames: str):
    process = subprocess.Popen(
            ['git', 'add', *filenames.split()],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    parser.add_argument(
        '--add_changes_to_staging',
        default=False, action='store_true',
        help='Automatically add new and changed files to staging')
    parser.add_argument(
        '--auto_commit_changes', default=False, action='store_true',
        help='Automatically commits added and changed files in staging')
    args = parser.parse_args(argv)

    retv = 0

    for filename in args.filenames:
        # print(f'Processing {filename}')
        return_value = process_nb(filename=filename, **vars(args))
        # if return_value != 0:
        #     print(f'Done converting base64 strings to files for {filename}')
        retv |= return_value

    return retv


if __name__ == '__main__':
    exit(main())
