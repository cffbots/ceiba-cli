"""Module to read user input and perform the requested input action."""
import argparse
import logging
from pathlib import Path

from .input_validation import validate_input
from .compute import compute_jobs

logger = logging.getLogger(__name__)


def exists(input_file: str) -> Path:
    """Check if the input file exists."""
    path = Path(input_file)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{input_file} doesn't exist!")

    return path


def main():
    """Parse the command line arguments to compute or query data from the database."""
    parser = argparse.ArgumentParser("moka")
    subparsers = parser.add_subparsers(help="compute or query some molecular properties", dest="command")

    # Request new jobs to run from the database
    parser_jobs = subparsers.add_parser("compute", help="compute available jobs")
    parser_jobs.add_argument("input", type=exists, help="Yaml input file")

    # Request data from the database
    parser_query = subparsers.add_parser("query", help="query some properties from the database")
    parser_query.add_argument("input", type=exists, help="Yaml input file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()

    opts = validate_input(args.input)
    # opts = validate_input()
    if args.command == "query":
        print("querying molecular properties!")
    elif args.command == "compute":
        print("computing properties")
        compute_jobs(opts)


if __name__ == "__main__":
    main()
