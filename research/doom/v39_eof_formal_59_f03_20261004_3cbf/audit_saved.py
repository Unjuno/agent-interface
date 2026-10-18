"""Separate saved-only semantic audit; never invoke a producer."""
import json
from pathlib import Path
import sys
from audit import check_directory


if __name__ == '__main__':
    verdict = check_directory(Path(sys.argv[1]))
    with Path(sys.argv[2]).open('x') as output:
        json.dump({'verdict': verdict, 'scope': 'saved-row-and-directory-semantics-only'}, output)
        output.write('\n')
