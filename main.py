from automove import AutoMove
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("--sftp", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", action="store_true", default=False)

    return vars(parser.parse_args())


if __name__ == "__main__":
    args = parse_args()
    mover = AutoMove(args)
    mover.run()
