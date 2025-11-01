import argparse
import sys
from .detector import detect

def main():
    """Main function for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="A fast, lightweight language detector for code.",
        epilog="If no file is provided, it reads from stdin."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType('r', encoding='utf-8'),
        default=sys.stdin,
        help="Path to the code file to analyze."
    )
    args = parser.parse_args()

    try:
        content = args.file.read()
        language = detect(content)
        print(language)
    except Exception as e:
        print(f"Error: Could not process the input. {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Close the file if it's not stdin
        if args.file is not sys.stdin:
            args.file.close()

if __name__ == "__main__":
    main()