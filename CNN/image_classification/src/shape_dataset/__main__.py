import argparse
import sys
from .config import DEFAULT_HELD_OUT_SEED, DEFAULT_TRAIN_SEED
from .generate import generate
from .output import publish


def main():
    parser = argparse.ArgumentParser(description='Generate a synthetic shape dataset')
    parser.add_argument('--output-dir', default='/data')
    parser.add_argument('--train-seed', type=int, default=DEFAULT_TRAIN_SEED)
    parser.add_argument('--held-out-seed', type=int, default=DEFAULT_HELD_OUT_SEED)
    args = parser.parse_args()
    if args.train_seed == args.held_out_seed: parser.error('training and held-out seeds must differ')
    try:
        publish(args.output_dir, generate(args.train_seed, args.held_out_seed))
    except (OSError, ValueError) as exc:
        print(f'Generation failed: {exc}', file=sys.stderr)
        return 1
    print(f'Generated 30 training and 15 held-out images in {args.output_dir}')
    return 0


if __name__ == '__main__': sys.exit(main())
