import argparse
import mimetypes
import os
import urllib.request
from typing import Optional, Sequence
from urllib.parse import urlparse

from .common import process_nb, base64_string_to_bytes


def base64_to_blob_storage(
        base64_string: str,
        az_blob_container_sas_url: str,
        image_path: str) -> (int, str):
    print("Uploading image to blob storage...")
    image_bytes = base64_string_to_bytes(base64_string)

    o = urlparse(az_blob_container_sas_url)
    # Remove first / from path
    if o.path[0] == '/':
        blob_storage_path = o.path[1:]
    else:
        blob_storage_path = o.path

    storage_account = o.scheme + "://" + o.netloc + "/"
    file_name_only = os.path.basename(image_path)

    response_status, url_path = http_put(
        storage_account, blob_storage_path,
        file_name_only, o.query, image_path, image_bytes
    )

    return response_status, url_path


def http_put(
        storage_url: str, container_name: str, blob_name: str,
        qry_string: str, image_name: str, image_bytes) -> (int, str):

    file_name_only = os.path.basename(image_name)

    file_ext = os.path.splitext(file_name_only)[1]

    url = storage_url + container_name + '/' + blob_name + '?' + qry_string

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
        return_value = process_nb(filename=filename, **vars(args))
        retv |= return_value

    return retv


if __name__ == '__main__':
    exit(main())
