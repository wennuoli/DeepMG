# Pretrained DeepMG Model Weights

The pretrained model weights of DeepMG are not included in this GitHub repository because of their large file size.

The pretrained weights can be downloaded from Zenodo:

https://doi.org/10.5281/zenodo.21881285


## Installation

1. Download the pretrained model archive from Zenodo.

2. Extract all `.pt` model files from the downloaded archive.

3. Place the extracted model files directly into this `pts/` folder.

After installation, the directory structure should be:

```text
pts/
│
├── MG_Nodes_seed_40_fold_0.pt
├── MG_Nodes_seed_40_fold_1.pt
├── MG_Nodes_seed_40_fold_2.pt
├── MG_Nodes_seed_40_fold_3.pt
├── MG_Nodes_seed_40_fold_4.pt
├── MG_Nodes_seed_41_fold_0.pt
├── ...
└── MG_Nodes_seed_42_fold_4.pt
```

## Usage

No modification of the source code is required.

The provided scripts automatically load pretrained models from the `pts/` directory according to the predefined naming convention:

MG_Nodes_seed_{seed}fold{fold}.pt

For example:

pts/MG_Nodes_seed_40_fold_0.pt

will be automatically recognized when running the corresponding evaluation or prediction scripts.


## Notes

- Keep the original model filenames unchanged.
- Keep the folder name as `pts`.
- Do not rename or reorganize the `.pt` files, otherwise the provided scripts may not locate the pretrained models correctly.
- The released weights correspond to the DeepMG model architecture and training configurations describe
