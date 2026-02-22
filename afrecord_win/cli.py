import argparse

def create_parser():
    parser = argparse.ArgumentParser(description="Record sound in cli in windows")
    parser.add_argument("name", type=str, help="Dummy argument")
    return parser


def cli():
    "Record sound in cli in windows"
    parser = create_parser()
    args = parser.parse_args()
    mycommand(args)


def mycommand(args):
    print(args)