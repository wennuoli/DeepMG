# Pretrained DeepMG Model Weights

Pretrained DeepMG model weights are not included in this GitHub repository because of their large file size.

The pretrained model checkpoints are available from Zenodo:

https://doi.org/10.5281/zenodo.21881285

After downloading the released checkpoint files, place all `.pt` files directly in this `pts/` folder. Do not create any additional subfolders.

The expected directory structure is:

```text
pts/
|-- MG_Nodes_seed_40_fold_*.pt
|-- MG_Nodes_seed_41_fold_*.pt
-- MG_Nodes_seed_42_fold_*.pt
```

A total of 15 pretrained checkpoints should be available:

- seeds 40, 41, and 42
- folds 0-4 for each seed

The checkpoint naming convention is:

```text
MG_Nodes_seed_{seed}_fold_{fold}.pt
```

For example:

```text
pts/MG_Nodes_seed_40_fold_0.pt
```

No modification of the source code is required.

Notes:

- Do not modify the checkpoint filenames.
- Do not rename the `pts` folder.
- Do not create additional directories such as `pts/models/` or `pts/pretrained/`.
- Keeping the files directly under `pts/` allows the existing prediction and evaluation scripts to find the checkpoints using their predefined paths.
