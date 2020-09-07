import argparse
import base64
import mimetypes
import os
import re
import subprocess
import urllib.request
import uuid
from typing import Optional, Sequence
from urllib.parse import urlparse


def base64_to_blob_storage(
        base64_string: str,
        sas_url: str,
        image_path: str):
    print("Uploading image to blob storage...")
    image_bytes = base64.decodebytes(base64_string.encode())

    o = urlparse(sas_url)
    # Remove first / from path
    if o.path[0] == '/':
        blob_storage_path = o.path[1:]
    else:
        blob_storage_path = o.path

    storage_account = o.scheme + "://" + o.netloc + "/"
    file_name_only = os.path.basename(image_path)

    response_status, url_path = put_blob(
        storage_account, blob_storage_path,
        file_name_only, o.query, image_path, image_bytes
    )

    if response_status >= 200 and response_status < 300:
        print(f"Successfully uploaded image to blob storage: {url_path}")
    else:
        print(f"Uploading process failed with response code: {response_status}")  # NOQA E501

    return url_path


def put_blob(
        storage_url: str, container_name: str, blob_name: str,
        qry_string: str, image_name: str, image_bytes):

    file_name_only = os.path.basename(image_name)

    file_ext = os.path.splitext(file_name_only)[1]

    url = storage_url + container_name + '/' + blob_name + '?' + qry_string

    # with open(file_name_full_path, 'rb') as fh:
    req = urllib.request.Request(
        url, data=image_bytes, method='PUT',
        headers={
                    'content-type': mimetypes.types_map[file_ext],
                    'x-ms-blob-type': 'BlockBlob'
                })
    response_code = urllib.request.urlopen(req).code
    # response_code = requests.put(
    #     url,
    #     data=image_bytes,
    #     headers={
    #                 'content-type': mimetypes.types_map[file_ext],
    #                 'x-ms-blob-type': 'BlockBlob'
    #             },
    #     params={'file': file_name_only}
    # ).status_code
    return response_code, url


def base64_to_local_file(base64_string: str, image_path: str):
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
        az_blob_container_url: str,
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

            base64_string = (
                match.split(':')[1]
                .replace('"', '')
                .replace(' ', '')
                .replace('\\n', '')
            )

            if az_blob_container_url:
                response_code, url_path = base64_to_blob_storage(
                    base64_string, az_blob_container_url, full_path
                )
            else:
                print("Converting base64 to image file and saving as %s" % full_path)  # NOQA E501
                base64_to_local_file(
                    base64_string, full_path
                )
                url_path = "./" + image_path

            new_files += " " + full_path

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
        '--az-blob-container-url',
        default=None,
        help='If provided it will upload images to external Azure Blob Storage container rather than local files')  # NOQA E501
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
        # print(f'Processing {filename}')
        return_value = process_nb(filename=filename, **vars(args))
        # if return_value != 0:
        #     print(f'Done converting base64 strings to files for {filename}')
        retv |= return_value

    return retv


if __name__ == '__main__':
    exit(main())
