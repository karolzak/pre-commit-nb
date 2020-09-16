import argparse
import mimetypes
import os
import re
import urllib.request
from typing import Optional, Sequence
from urllib.parse import urlparse

from dotenv import load_dotenv

from pre_commit_nb.common import base64_string_to_bytes, process_nb


def base64_to_blob_storage(
        base64_string: str,
        az_blob_container_sas_url: str,
        image_path: str) -> (int, str):
    image_bytes = base64_string_to_bytes(base64_string)

    o = urlparse(az_blob_container_sas_url)
    # Remove first / from path
    if o.path[0] == '/':
        blob_storage_path = o.path[1:]
    else:  # pragma: no cover
        blob_storage_path = o.path

    storage_account = o.scheme + "://" + o.netloc + "/"
    file_name_only = os.path.basename(image_path)

    response_status, url_path = http_put_az_blob(
        storage_account, blob_storage_path,
        file_name_only, o.query, image_path, image_bytes
    )

    return response_status, url_path


def http_put_az_blob(
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
    with urllib.request.urlopen(req) as response:
        response_code = response.code

    return response_code, url


def check_sas_token_for_correct_permissions(
        sas_token: str, permissions_list: Sequence[str]) -> bool:
    search_results = re.search(
        r"&sp=[crawl]{1,5}&",
        sas_token)

    if not search_results:
        return False

    if not all(char in search_results[0] for char in permissions_list):
        return False

    return True


def validate_env_vars(
        az_blob_container_url: str,
        az_blob_container_sas_token_upload: str,
        az_blob_container_sas_token_download: str) -> (str, str, str):

    if az_blob_container_url is None:
        raise ValueError("Couldn't find `AZ_BLOB_CONTAINER_URL` in environment variables.")  # NOQA E501

    if az_blob_container_sas_token_upload is None:
        raise ValueError("Couldn't find `AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD` in environment variables.")  # NOQA E501

    if not check_sas_token_for_correct_permissions(
            az_blob_container_sas_token_upload, permissions_list=['w']):
        raise Exception("Provided SAS token doesn't have required permissions to write files. Required permission name: `write`")  # NOQA E501

    if az_blob_container_sas_token_download is None:
        print("WARNING: `AZ_BLOB_CONTAINER_SAS_TOKEN_DOWNLOAD` not found - trying to reuse `AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD` to read files from external storage")  # NOQA E501
        az_blob_container_sas_token_download = az_blob_container_sas_token_upload  # NOQA E501

    if not check_sas_token_for_correct_permissions(
            az_blob_container_sas_token_download, permissions_list=['r']):
        raise Exception("Provided SAS token doesn't have required permissions to read files. Required permission name: `read`")  # NOQA E501

    return az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download  # NOQA E501


def main(argv: Optional[Sequence[str]] = None) -> int:
    load_dotenv()

    az_blob_container_url = os.environ.get("AZ_BLOB_CONTAINER_URL")
    az_blob_container_sas_token_upload = os.environ.get("AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD")  # NOQA E501
    az_blob_container_sas_token_download = os.environ.get("AZ_BLOB_CONTAINER_SAS_TOKEN_DOWNLOAD")  # NOQA E501
    az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download = validate_env_vars(  # NOQA E501
        az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download)  # NOQA E501

    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    # parser.add_argument(
    #     '--az-blob-container-sas-url', required=True,
    #     help='If provided it will upload images to external Azure Blob Storage container rather than local files')  # NOQA E501
    parser.add_argument(
        '--add-changes-to-staging',
        default=False, action='store_true',
        help='Automatically add new and changed files to staging')
    parser.add_argument(
        '--force-commit', default=False, action='store_true',
        help='Forces `git commit` to go through even when there were some files modified with this git hook. Default behavior for `pre-commit` manager is to abort commit if git hook made any changes to staged files')  # NOQA E501
    args = parser.parse_args(argv)

    retv = 0

    for filename in args.filenames:
        return_value = process_nb(
            filename=filename,
            az_blob_container_url=az_blob_container_url,
            az_blob_container_sas_token_upload=az_blob_container_sas_token_upload,  # NOQA E501
            az_blob_container_sas_token_download=az_blob_container_sas_token_download,  # NOQA E501
            **vars(args))
        retv |= return_value

    return retv


if __name__ == '__main__':  # pragma: no cover
    exit(main())
