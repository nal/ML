"""Command line interface for training, evaluation and prediction."""
import argparse
import platform
import sys
import torch
from .device import resolve_device, available_cpus
from .benchmark import read_results, format_summary
from .publication import locked, _result_lock, recover_results
from pathlib import Path
from .predict import predict
from .train import evaluate, train


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description='Classify synthetic shapes on CPU')
    sub = parser.add_subparsers(dest='command', required=True)
    training = sub.add_parser('train')
    evaluation = sub.add_parser('evaluate')
    prediction = sub.add_parser('predict')
    summary = sub.add_parser('summary')
    summary.add_argument('--data-dir', default='/data')
    for command in (training, evaluation):
        command.add_argument('--data-dir', default='/data')
    for command in (training, evaluation, prediction):
        command.add_argument('--checkpoint', default='/data/shapes.pth')
        command.add_argument('--device', choices=('auto', 'cpu', 'mps'), default='auto')
    training.add_argument('--seed', type=int, default=42)
    training.add_argument('--epochs', type=positive_int, default=60)
    training.add_argument('--batch-size', type=positive_int, default=8)
    training.add_argument('--dataset-train-seed', type=int)
    training.add_argument('--dataset-held-out-seed', type=int)
    prediction.add_argument('image')
    args = parser.parse_args(argv)
    try:
        if args.command == 'summary':
            root = Path(args.data_dir)
            if not root.exists():
                print('No results yet.')
                return 0
            while True:
                recover_results(root)
                with locked(_result_lock(root)):
                    if (root / '.benchmark-transaction.json').exists():
                        continue
                    print(format_summary(read_results(root / 'benchmark-results.json')))
                    break
            return 0
        environment, device = resolve_device(args.device)
        print(f'Environment: {environment}; device: {device}; Python: {platform.python_version()}; PyTorch: {torch.__version__}', file=sys.stderr)
        if args.command == 'train':
            print(f'CPU threads: {available_cpus()}', file=sys.stderr)
        if args.command == 'predict':
            print(predict(args.image, args.checkpoint, device))
        else:
            if args.command == 'train':
                results = train(args.data_dir, args.checkpoint, args.seed, args.epochs, args.batch_size,
                                args.dataset_train_seed, args.dataset_held_out_seed, device, environment)
            else:
                results = evaluate(args.data_dir, args.checkpoint, device)
            for name, (correct, total) in zip(('Training', 'Held-out'), results):
                print(f'{name}: {correct}/{total} accuracy={correct / total:.4f}')
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
