"""CLI interface for afrecord-win."""

import argparse
import os
import sys
from .afrecordmain import AudioRecorder


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="afrecord",
        description="Record sound from the command line on Windows.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        default="output.wav",
        help="Output WAV file path (default: output.wav)",
    )
    return parser


def cli() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    recorder = AudioRecorder()

    try:
        print(f"Starting recording to {args.output_file}")

        if not recorder.start_recording(args.output_file):
            print("Failed to start recording", file=sys.stderr)
            sys.exit(1)

        print("Recording... Press Enter to stop")

        input()

        recorder.stop_recording()

        if os.path.exists(args.output_file):
            size = os.path.getsize(args.output_file)
            print(f"Recording saved: {args.output_file} ({size} bytes)")
        else:
            print("Recording file was not created", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nStopping recording...")
        recorder.stop_recording()

        if os.path.exists(args.output_file):
            size = os.path.getsize(args.output_file)
            print(f"Recording saved: {args.output_file} ({size} bytes)")
        else:
            print("Recording file was not created", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    cli()
