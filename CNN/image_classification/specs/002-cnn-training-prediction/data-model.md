# Data Model: CNN Classifier

## Dataset set

- Root `/data`; splits `train` and `held-out`; class directories `circle`, `rectangle`, `triangle` in that order.
- Require exactly 10 readable PNG images per training class and 5 per held-out class; reject missing/extra images or unexpected class labels rather than silently dropping them. Ignore feature 001's root manifest, lock and unrelated non-image files.
- Training images are decoded to RGB, resized and cached once as `[3,144,256]` float32 tensors in `[0,1]`; held-out data is used only for final unaugmented evaluation.

## Training configuration

- Training seed: integer, default 42; optional per-set dataset seed provenance: integer or literal `unknown` independently.
- Epochs: positive integer, default 30; batch size: positive integer, default 8; Adam learning rate 0.001.
- Augmentation: rotation ±10°, horizontal and vertical flip probabilities 0.5, color brightness/contrast/saturation jitter 0.1; apply only to cached training samples.

## Checkpoint

- `/data/shapes.pth` by default; single dictionary with CPU `state_dict` and plain-data `metadata`.
- Metadata: `class_order` = `["circle", "rectangle", "triangle"]`; `input_size` = `[144,256]` (height, width); `pixel_scaling` = `"float32_0_1"`; `training_seed` integer; `dataset_train_seed` and `dataset_held_out_seed` integer or `"unknown"`; `pytorch_version` string; `environment` = `"docker"`; `device` = `"cpu"`.
- Save atomically after a successful final epoch; load with `weights_only=True`, validate metadata and strict weights against matching model architecture; errors must not produce success.

## Evaluation result

- For each split: correct integer, total integer, accuracy = correct/total, with 0 ≤ correct ≤ total. Report both splits in the same operation. Evaluate in inference mode without augmentation or weight updates.

## Prediction

- Input: one readable image; output: one class name selected using checkpoint class order. Convert to RGB and apply shared preprocessing before inference.
