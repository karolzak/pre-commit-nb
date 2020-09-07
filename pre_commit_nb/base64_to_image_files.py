import argparse
import io
import re
import tokenize
from typing import List
from typing import Optional
from typing import Sequence


def process_nb(filename: str) -> int:
    # with open(filename, encoding='UTF-8', newline='') as f:
    #     contents = f.read()
    # line_offsets = get_line_offsets_by_line_no(contents)

    # # Basically a mutable string
    # splitcontents = list(contents)

    # # Iterate in reverse so the offsets are always correct
    # tokens_l = list(tokenize.generate_tokens(io.StringIO(contents).readline))
    # tokens = reversed(tokens_l)
    # for token_type, token_text, (srow, scol), (erow, ecol), _ in tokens:
    #     if token_type == tokenize.STRING:
    #         new_text = handle_match(token_text)
    #         splitcontents[
    #             line_offsets[srow] + scol:
    #             line_offsets[erow] + ecol
    #         ] = new_text

    # new_contents = ''.join(splitcontents)
    # if contents != new_contents:
    #     with open(filename, 'w', encoding='UTF-8', newline='') as f:
    #         f.write(new_contents)
    #     return 1
    # else:
    #     return 0
    return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    args = parser.parse_args(argv)

    retv = 0

    for filename in args.filenames:
        print(f'Processing {filename}')
        return_value = process_nb(filename)
        if return_value != 0:
            print(f'Done converting base64 strings to files for {filename}')
        retv |= return_value

    return retv


if __name__ == '__main__':
    exit(main())
