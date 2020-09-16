import filecmp
import os
import tempfile
import sys
import shutil

import pytest

sys.path.append("../pre_commit_nb")
from pre_commit_nb.base64_to_image_files import (
    base64_to_local_file, main
)


TEST1_FILE = "./tests/data/test1.png"
TEST1_B64 = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACMSURBVDhPpc1RCsMgFETR7n/TFuIhJOqbKj0/gb479nNr//HKzc/n7AeOJyyXJHtsMm0ksoh6WXmdLSLpZHGwiKQP9T9skF7KhzqLSNk/mUWm3WBQUZ2wHDjusVmS/KIOhAVRpOyfmSqSXhYPqSLpw/vVDdKJgyrqZUWUaSNpRbXBYOB4wvLm51OtfQGRVu87E3xWdwAAAABJRU5ErkJggg=="  # NOQA 501

TEST_NB_FILE = "./tests/data/example_nb.txt"
TEST_NB_OUT_FILE = "./tests/data/example_nb_out.txt"

TEST_MAIN_DATA = [
    # ("test_file, test_retv")
    (TEST_NB_FILE, 1),
    (TEST_NB_OUT_FILE, 0),
]


def test_base64_to_local_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_out_path = os.path.join(
            temp_dir, "test1_out.png")
        base64_to_local_file(TEST1_B64, test_out_path)
        assert os.path.exists(test_out_path)
        assert filecmp.cmp(TEST1_FILE, test_out_path, shallow=False)


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
