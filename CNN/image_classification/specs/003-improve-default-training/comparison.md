# Epoch Comparison

## Predeclared protocol

Compare 30, 60 and 120 epochs sequentially on the same generated training images with training seed 42, batch size 8, Adam learning rate 0.001, cross-entropy loss, existing model and augmentation, one CPU thread and deterministic algorithms. Time only the epoch loop with a monotonic clock.

Choose the shortest longer candidate with at least three more correct training predictions than the 30-epoch baseline and loop time no more than four times baseline. Otherwise choose 30. Keep candidate counts and weights private until the choice is frozen; no held-out dataset is mounted during selection. After freezing, report each candidate's paired training and held-out results. Failures block selection.

## Dataset identity

Generator seeds: training 42; held-out 43. SHA-256 digests of training images:

- `circle/01.png`: `d6345db71ffdea93d9b198fb9a2e326ecc55c7d2eea3a2006974c9e577b95097`
- `circle/02.png`: `ee7bf615ad0bf32cbd81a2654ae535d5e35c32dab67e203ae148d4e8614e6f06`
- `circle/03.png`: `f4dbd956218f4d7f8f4782580f8f69a2d57bff6f38624565e55aa6c894860c3e`
- `circle/04.png`: `9d5d34796f1c219f473ea7a0d86c0c22361ee5b4f57e1e39839c13e6c5e32d14`
- `circle/05.png`: `53f87adf5df45d81ccdb979edfba071d7ff33e3e90884f1ebff3b5263d6f1d9c`
- `circle/06.png`: `0c324141b075bd3af0b17aad7cd640dd2342cf9fa3127c98698a5b7b261936cd`
- `circle/07.png`: `8fdee677f3ebe3876dcf50a64c4b77a5d293d75139cec474b40006b58fcce8a3`
- `circle/08.png`: `04bfc0eb5701421cd20ac06ab63e80cb12ca6b80e0ea2909200cf6083a3e75cf`
- `circle/09.png`: `d3fba944e7530b6b81ba89a8ef7a046ff2ae220878a13831dddd1dea425b0b93`
- `circle/10.png`: `7fbffd4a32c43020d8b4e01f999bd93a1a728ddfe66113c551b0ef7541a53ba9`
- `rectangle/01.png`: `83fa137c24a5ce167d3623a694a72b464e0af63043b6a16f9355bd76d83a3772`
- `rectangle/02.png`: `8c33b7249c7749121d149f24faad1e519b59f47da01ebf57d9b1e1098cfadfdb`
- `rectangle/03.png`: `573d148180dde8610e574e678526d4f32db0f83ae18db085141115e1a265f4b8`
- `rectangle/04.png`: `05157b7e9a658397522aa608975aae4d8278678aaad89feda3bff7d94c52ab0d`
- `rectangle/05.png`: `19a7bee9096bb044146a74e46c9615da69c10947caa34589630cbf36a3681ad8`
- `rectangle/06.png`: `3073dcedf8b79278cf5d931e5642392aec69635af7621225660e497cdb6620e8`
- `rectangle/07.png`: `88094b3bff882895ccd9524ccda826800b9799ce1e8b1399cd28b7e2fdab8c0b`
- `rectangle/08.png`: `873f303ef4e6594ce1e0c0f40a7516ccf328aae50d06cccf5eaded7d07dd23f9`
- `rectangle/09.png`: `bd4035fb81f6c29cbfa4c871f3edbb1416061c34acccaff71336e200a6ae18e1`
- `rectangle/10.png`: `47450bcf046893fcd86e7dad5dbbdd042772f39fe96f796d6ecab7d0da742299`
- `triangle/01.png`: `b1bfa183ce476fdd43ea2831e53e5be535fffd0a7f16943832aa1df2fc8d7a61`
- `triangle/02.png`: `7b139adf35f2bb894f90f0fd69d766769680cdc8512b12865aade5b619df5b6b`
- `triangle/03.png`: `e6ed07cb5748935da41a70d1283bd5e555bb02b0f99b6a91395d911798908ac4`
- `triangle/04.png`: `01977c1b4ee7efcf225f3251621766d27ff305c8a1d1f0a20669424f0c71eb79`
- `triangle/05.png`: `f7f754caea5541bc71e10e3fb1c6a7317fe321f3a5fbff83216646fcb43532d1`
- `triangle/06.png`: `f20470419d25068be39a7cf5debe8198f828c2a1403b6317f858af42bfc495a4`
- `triangle/07.png`: `4f508aa7644ab15e43b8ea46a4a669b6f941d88de80942512dfda1a607de9a70`
- `triangle/08.png`: `a609d79fbd297c22e845bbf03547b0e25011223bf17000c1c6a777f3114d5749`
- `triangle/09.png`: `105ea098a1dde41902ab1d7ca662918b2f6ce797d23e9890623204efe56b7d9c`
- `triangle/10.png`: `7c7426d027842e139b866d8088843f783a086f1dd16053983b94ea00a29237c0`

## Environment

Linux arm64 Docker CPU image `sha256:be37e69aed2d18b0df9dca5da5a7efed3d11f95f3a5f38a8cb9d0d33db5c3bdd`; Python 3.14.10; PyTorch 2.15.0+cpu; one CPU thread; deterministic algorithms enabled. Each candidate starts from the same seed and initialization. Times measure the training epoch loop only, sequentially on the same image.

## Frozen decision

Selected default: **60 epochs**. Frozen at 2026-11-06T19:45:18.937733+00:00 before held-out evaluation. The selection applied the predeclared rule using only training data and elapsed time. The earlier feature 002 held-out observation was already known and was excluded from selection.

## Paired candidate results

| Epochs | Training correct/total | Training accuracy | Held-out correct/total | Held-out accuracy | Epoch-loop seconds |
|---:|---:|---:|---:|---:|---:|
| 30 | 16/30 | 0.5333 | 7/15 | 0.4667 | 21.63 |
| 60 | 19/30 | 0.6333 | 6/15 | 0.4000 | 45.71 |
| 120 | 24/30 | 0.8000 | 5/15 | 0.3333 | 87.48 |

The 60-epoch run was the shortest longer candidate satisfying the predeclared training-count gain and time limit. All candidate training counts matched the private pre-freeze measurements. Held-out results did not influence selection. This small synthetic dataset does not establish real-world generalization, and the held-out set was previously observed.

## Default repeat validation

Two independent default 60-epoch runs on the same data and image each reported training 19/30 (0.6333) and held-out 6/15 (0.4000). Both wrote separate checkpoints; the correct counts were identical across runs.
