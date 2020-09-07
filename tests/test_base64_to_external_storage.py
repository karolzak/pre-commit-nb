import filecmp
import os
import tempfile
import sys
import shutil
import urllib
import pytest

sys.path.append("../pre_commit_nb")
from pre_commit_nb.base64_to_external_storage import (
    base64_to_blob_storage, main
)


TEST1_FILE = "./tests/data/test1.png"
TEST1_B64 = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACMSURBVDhPpc1RCsMgFETR7n/TFuIhJOqbKj0/gb479nNr//HKzc/n7AeOJyyXJHtsMm0ksoh6WXmdLSLpZHGwiKQP9T9skF7KhzqLSNk/mUWm3WBQUZ2wHDjusVmS/KIOhAVRpOyfmSqSXhYPqSLpw/vVDdKJgyrqZUWUaSNpRbXBYOB4wvLm51OtfQGRVu87E3xWdwAAAABJRU5ErkJggg=="  # NOQA 501

TEST_NB_FILE = "./tests/data/example_nb.txt"
TEST_NB_OUT_FILE = "./tests/data/example_nb_out.txt"

TEST_AZ_BLOB_CONTAINER_URL = "https://privdatastorage.blob.core.windows.net/teststorage?st=2020-09-07T11%3A59%3A21Z&se=2021-09-08T11%3A59%3A00Z&sp=rwl&sv=2018-03-28&sr=c&sig=3h9nxZrNUxRx6PeqvyiEbWYeNRJVrLA22HsjYNFl%2FDU%3D"  # NOQA E501

TEST_MAIN_DATA = [
    # ("test_file, test_retv")
    (TEST_NB_FILE, 1),
    (TEST_NB_OUT_FILE, 0),
]


def test_base64_to_external_storage():
    with tempfile.TemporaryDirectory() as temp_dir:
        response_code, url = base64_to_blob_storage(
            TEST1_B64, TEST_AZ_BLOB_CONTAINER_URL, TEST1_FILE)
        r = urllib.request.Request(url, method="GET")
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
            test_file_copy,
            "--az-blob-container-url=%s" % TEST_AZ_BLOB_CONTAINER_URL
        ])
        assert retv == test_retv
        assert os.path.getsize(test_file_copy) < 10000
