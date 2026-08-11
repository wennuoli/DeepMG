# Dataset Artifacts

This directory contains the released DeepMG dataset file when available in the GitHub repository.

Large dataset-related artifacts are not included in this repository because of their file size. They are available from Zenodo:

https://doi.org/10.5281/zenodo.21881285

After downloading the released artifacts, place the following files and directory directly in this `dataset/` folder:

```text
dataset/
|-- embeddings.pkl
|-- smiles2rep.pkl
|-- processed.pkl
-- PDBs/
```

The artifacts are used as follows:

- `embeddings.pkl`: ESM-based protein representations.
- `smiles2rep.pkl`: Uni-Mol molecular representations.
- `processed.pkl`: cached graph dataset used by DeepMG.
- `PDBs/`: protein structure files used for graph construction.

Do not rename these files or directories. The existing DeepMG preprocessing, training, and prediction scripts use fixed paths to locate them.

`Dataset.xlsx` is included in this repository when present and does not need to be downloaded from Zenodo unless a separate release note states otherwise.
