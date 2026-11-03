# DeepMG

DeepMG predicts molecular glue-mediated degradation activity from a molecular glue, a target protein, and an effector protein. The three components are encoded by graph neural networks and combined for binary classification.

## Installation

Run the model in the `mg` environment:

```bash
conda env create -f mg_env.yaml
conda activate mg
```

Protein preprocessing from new sequences uses the separate environment in `esm_env.yaml`. This step is not needed when using the released precomputed features.

## Dataset and pretrained model

The modeling dataset contains 2354 records, including 1597 positive and 757 negative labels, and 2338 unique molecular structures. The release includes a single-sheet `Dataset.xlsx`, precomputed molecular and protein features, sequence-predicted protein structures, and the pretrained checkpoint `deepmg.pt`.

**Download: the new Zenodo record will be linked here after it is uploaded.**

Download `DeepMG_release.zip` and extract it directly into this repository's root directory. The extracted layout is:

```text
DeepMG/
|-- main.py
|-- models.py
|-- preprocess.py
|-- predict.py
|-- dataset/
|   |-- Dataset.xlsx
|   |-- embeddings.pkl
|   |-- smiles2rep.pkl
|   `-- PDBs/
`-- pts/
    `-- deepmg.pt
```

Use the Excel, features, and model from the same release. The data and weights are distributed externally and are not included in the Git repository. If updating an existing installation, move old `processed.pkl` and `predict_processed.pkl` caches aside before rebuilding graph inputs for the new dataset.

`Dataset.xlsx` contains the `Model_Dataset` worksheet with these columns:

```text
ID, old ID, Name, label, Smiles, Target name, Sequence,
Effector name, Effector Sequence, Smiles_ID, Sequence_ID,
Effector_Sequence_ID
```

The `old ID` column is retained for provenance. Original activity labels use reported DC50 or IC50 below 1000 nM, or reported Dmax/another explicit protein degradation percentage above 60%.

## Prediction

After extracting the release, run:

```bash
python predict.py
```

The script loads `pts/deepmg.pt` once and writes `predict/full_predictions.csv`. The output retains the input columns and adds `Prediction` (predicted probability) and `Predicted_Label` (1 when the probability is greater than 0.5, otherwise 0).

Optional input and output paths can be supplied:

```bash
python predict.py --input dataset/Dataset.xlsx --checkpoint pts/deepmg.pt --output predict/full_predictions.csv
```

The default inference batch size is 1. This inference setting does not change the model's training batch size. The released checkpoint supports direct prediction; benchmark metrics in the paper are averaged across random seeds 40, 41, and 42 and five folds.

## Training

With the released dataset and features in place, run:

```bash
python main.py
```

The training script builds `dataset/processed.pkl` if needed. Its configured seed is trained with an independent test split and five-fold cross-validation. Set the training seed to 40, 41, or 42 for the corresponding run; a single default invocation is not a three-seed benchmark run.

## Preparing new inputs

New molecular glues or proteins require the same feature generation and graph construction used by the model. Prepare an Excel file with the same molecular, sequence, and identifier columns, generate its protein and molecular features with the scripts in `process/`, and use matching feature files. Labels are needed for training but not for prediction. Precomputed features supplied in the release cover the released dataset.

## Code structure

- `models.py`: DeepMG model architecture.
- `preprocess.py`: molecular/protein graph construction and dataset loading.
- `main.py`: model training and evaluation.
- `predict.py`: prediction with the released model.
- `process/`: molecular and protein preprocessing utilities.

The model implementation and training hyperparameters are unchanged by the dataset release update.
