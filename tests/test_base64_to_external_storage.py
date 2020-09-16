import filecmp
import os
import shutil
import sys
import tempfile
import urllib

import pytest
from dotenv import load_dotenv

sys.path.append("../pre_commit_nb")
from pre_commit_nb.base64_to_external_storage import (
    base64_to_blob_storage, main,
    check_sas_token_for_correct_permissions, validate_env_vars)

load_dotenv()  # tests doesnt work locally without this line

TEST1_FILE = "./tests/data/test1.png"
TEST1_B64 = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACMSURBVDhPpc1RCsMgFETR7n/TFuIhJOqbKj0/gb479nNr//HKzc/n7AeOJyyXJHtsMm0ksoh6WXmdLSLpZHGwiKQP9T9skF7KhzqLSNk/mUWm3WBQUZ2wHDjusVmS/KIOhAVRpOyfmSqSXhYPqSLpw/vVDdKJgyrqZUWUaSNpRbXBYOB4wvLm51OtfQGRVu87E3xWdwAAAABJRU5ErkJggg=="  # NOQA 501

TEST_NB_FILE = "./tests/data/example_nb.txt"
TEST_NB_OUT_FILE = "./tests/data/example_nb_out.txt"

TEST_AZ_BLOB_CONTAINER_URL = os.environ.get("AZ_BLOB_CONTAINER_URL")  # NOQA E501
TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD = os.environ.get("AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD")  # NOQA E501
TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_DOWNLOAD = os.environ.get("AZ_BLOB_CONTAINER_SAS_TOKEN_DOWNLOAD")  # NOQA E501

TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR = "?st=2020-09-15T13%3A37%3A04Z&se=2022-09-16T13%3A37%3A00Z&sp=cwr&sv=2018-03-28&sr=c&sig=hQslYqRHlphcygR1VbcaB9dOIRq42abqYlZQoAoz2ks%3D"  # NOQA E501
TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR = "?st=2020-09-15T13%3A37%3A04Z&se=2022-09-16T13%3A37%3A00Z&sp=cr&sv=2018-03-28&sr=c&sig=hQslYqRHlphcygR1VbcaB9dOIRq42abqYlZQoAoz2ks%3D"  # NOQA E501
TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CW = "?st=2020-09-15T13%3A37%3A04Z&se=2022-09-16T13%3A37%3A00Z&sp=cw&sv=2018-03-28&sr=c&sig=hQslYqRHlphcygR1VbcaB9dOIRq42abqYlZQoAoz2ks%3D"  # NOQA E501
TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_NONE = "?st=2020-09-15T13%3A37%3A04Z&se=2022-09-16T13%3A37%3A00Z&sv=2018-03-28&sr=c&sig=hQslYqRHlphcygR1VbcaB9dOIRq42abqYlZQoAoz2ks%3D"  # NOQA E501


TEST_MAIN_DATA = [
    # (test_file, test_retv)
    (TEST_NB_FILE, 1),
    (TEST_NB_OUT_FILE, 0),
]

TEST_PERMISSIONS = [
    # (sas_token, permissions_list, expected)
    (TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ['c', 'w', 'r'], True),
    (TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ['c'], True),
    (TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ['c', 'w', 'a'], False),
    (TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ['a'], False),
    (TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_NONE, ['c'], False),
]

TEST_VAL_ENV_VARS_EXCEPTIONS = [
    # (az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download, expected)  # NOQA E501
    (None, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ValueError),  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, None, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, ValueError),  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR, Exception),  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR, None, Exception),  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CW, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CW, Exception),  # NOQA E501
]

TEST_VAL_ENV_VARS_OK = [
    # (az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download, expected)  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CW, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR,  # NOQA E501
        (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CW, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CR)),  # NOQA E501
    (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, None,  # NOQA E501
        (TEST_AZ_BLOB_CONTAINER_URL, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR, TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_CWR)),  # NOQA E501
]


@pytest.mark.parametrize(
    "az_blob_container_url, permissions_list, expected",
    TEST_PERMISSIONS)
def test_check_sas_token_for_correct_permissions(
        az_blob_container_url, permissions_list, expected):
    result = check_sas_token_for_correct_permissions(
        az_blob_container_url, permissions_list)
    assert result == expected


@pytest.mark.parametrize(
    "az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download, expected",  # NOQA E501
    TEST_VAL_ENV_VARS_EXCEPTIONS)
def test_validate_env_vars_exceptions(
        az_blob_container_url, az_blob_container_sas_token_upload,
        az_blob_container_sas_token_download, expected):
    with pytest.raises(expected):
        validate_env_vars(
            az_blob_container_url, az_blob_container_sas_token_upload,
            az_blob_container_sas_token_download)


@pytest.mark.parametrize(
    "az_blob_container_url, az_blob_container_sas_token_upload, az_blob_container_sas_token_download, expected",  # NOQA E501
    TEST_VAL_ENV_VARS_OK)
def test_validate_env_vars_ok(
        az_blob_container_url,
        az_blob_container_sas_token_upload,
        az_blob_container_sas_token_download, expected):
    results = validate_env_vars(
            az_blob_container_url, az_blob_container_sas_token_upload,
            az_blob_container_sas_token_download)
    assert results == expected


def test_base64_to_external_storage():
    with tempfile.TemporaryDirectory() as temp_dir:
        response_code, url = base64_to_blob_storage(
            TEST1_B64,
            TEST_AZ_BLOB_CONTAINER_URL + TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_UPLOAD,  # NOQA E501
            TEST1_FILE)
        r = urllib.request.Request(
            url.split('?')[0] + TEST_AZ_BLOB_CONTAINER_SAS_TOKEN_DOWNLOAD,
            method="GET")

        out_path = os.path.join(temp_dir, 'test1_out.png')
        with urllib.request.urlopen(r) as response:
            open(out_path, 'wb').write(response.read())

        assert os.path.exists(out_path)
        assert filecmp.cmp(TEST1_FILE, out_path, shallow=False)


@pytest.mark.parametrize(
    "test_file, test_retv",
    TEST_MAIN_DATA)
def test_main(test_file, test_retv):
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_copy = os.path.join(temp_dir, os.path.basename(test_file))
        shutil.copyfile(test_file, test_file_copy)
        retv = main([
            test_file_copy
        ])
        assert retv == test_retv
        assert os.path.getsize(test_file_copy) < 10000
