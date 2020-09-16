import base64
import os
import re
import subprocess
import uuid


def create_nb_cell_output(url: str) -> str:
    return """"text/html": [
            "<img src=\\"%s\\"/>"
        ]""" % url


def git_add(filenames: str):  # pragma: no cover
    process = subprocess.Popen(
            ['git', 'add', *filenames.split()],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()


def base64_string_to_bytes(base64_string: str) -> bytes:
    return base64.decodebytes(base64_string.encode())


def process_nb(
        filename: str,
        add_changes_to_staging: bool,
        force_commit: bool,
        az_blob_container_url: str = None,
        az_blob_container_sas_token_upload: str = None,
        az_blob_container_sas_token_download: str = None,
        **kwargs
        ) -> int:
    print("==================")
    print("Processing %s" % filename)
    with open(filename, 'r') as file:
        org_data = " ".join(file.readlines())
    data = org_data
    matches = re.findall(
        r"\"image/(?:gif|png|jpeg|bmp|webp)\": \".*[a-zA-Z0-9+/=]\"",
        data)

    new_files = ""

    for match in matches:
        ext = "." + re.findall(r"image/[a-zA-Z]*", match)[0].split('/')[1]
        image_path = "nb_images" + "/" + str(uuid.uuid4()) + ext

        full_path = ""
        full_path += "" if os.path.isabs(os.path.dirname(filename)) else "./"
        full_path += os.path.dirname(filename) + "/" + image_path

        base64_string = (
            match.split(':')[1]
            .replace('"', '')
            .replace(' ', '')
            .replace('\\n', '')
        )

        if az_blob_container_url:
            from pre_commit_nb.base64_to_external_storage import (
                base64_to_blob_storage)

            print("Converting base64 to image file and uploading it to blob storage...")  # NOQA E501
            response_status, url_path = base64_to_blob_storage(
                base64_string,
                az_blob_container_url + az_blob_container_sas_token_upload,
                full_path
            )

            if az_blob_container_sas_token_download:
                url_path = url_path.split('?')[0] + az_blob_container_sas_token_download  # NOQA E501

            if response_status >= 200 and response_status < 300:
                print("Successfully uploaded image to blob storage: " + url_path)  # NOQA E501
            else:  # pragma: no cover
                print("Uploading process failed with response code: " + response_status)  # NOQA E501
        else:
            from pre_commit_nb.base64_to_image_files import (
                base64_to_local_file)

            print("Converting base64 to image file and saving as " + full_path)
            base64_to_local_file(
                base64_string, full_path
            )
            url_path = "./" + image_path
            new_files += " " + full_path

        data = data.replace(match, create_nb_cell_output(url_path))

    if org_data != data:
        with open(filename, 'w') as file:
            file.write(data)
            new_files += " " + filename
            new_files = new_files.strip()

        if add_changes_to_staging:  # pragma: no cover
            print("'--add-changes-to-staging' flag set to 'True' - adding new and changed files to staging...")  # NOQA E501
            print(new_files)
            git_add(new_files)

        if force_commit:  # pragma: no cover
            print("'--auto-commit-changes' flag set to 'True' - git hook set to return exit code 0.")  # NOQA E501
            return 0

        return 1
    else:
        print("Didn't find any base64 strings...")
        return 0
