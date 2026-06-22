# DeepMG

DeepMG is a deep learning framework for molecular glue activity prediction. The model integrates molecular glue, target protein, and effector protein representations for binary classification.

## Project Structure

```text
DeepMG/
|-- main.py                    # Model training with independent test split and 5-fold validation
|-- models.py                  # DeepMG model architecture
|-- preprocess.py              # Graph construction and dataset loading
|-- predict.py                 # Prediction with trained checkpoints
|-- mg_env.yaml                # Environment for data cleaning, molecule preprocessing, training, and prediction
|-- esm_env.yaml               # Environment for protein preprocessing
|-- history.json               # Training records
|-- dataset/
|   |-- Dataset.xlsx           # Main DeepMG dataset
|   |-- collate_smi.py         # SMILES representation checking utility
|   |-- collate_seq.py         # Protein sequence/PDB/embedding checking utility
|   |-- embeddings.pkl         # ESM protein embeddings
|   |-- smiles2rep.pkl         # Uni-Mol molecular representations
|   |-- processed.pkl          # Cached graph dataset
|   -- PDBs/                   # Protein structure files
|-- process/
|   |-- clean.py               # Data cleaning and ID assignment
|   |-- fasta_m.py             # Standalone FASTA generation utility
|   |-- esm.py                 # Standalone ESM embedding utility
|   |-- protein_preprocess.py  # Combined protein FASTA/ESM/ESMFold workflow
|   -- Uni.py                  # Uni-Mol molecular representation generation
-- pts/                        # Trained model checkpoints
```

## Environment Setup

DeepMG uses two Conda environments because protein preprocessing and model training require different dependency stacks.

Create the molecular glue/model environment:

```bash
conda env create -f mg_env.yaml
conda activate mg
```

Create the protein preprocessing environment:

```bash
conda env create -f esm_env.yaml
conda activate esm
```

Key dependencies:

```text
mg environment
- Python 3.10.18
- PyTorch 2.7.1
- PyTorch Geometric 2.5.2
- RDKit 2025.3.6
- Uni-Mol tools 0.1.5
- pandas 2.3.2
- scikit-learn 1.7.2

esm environment
- Python 3.7
- PyTorch 1.12.1
- fair-esm 2.0.1
- openfold 1.0.0
- deepspeed 0.5.9
- pandas 1.3.5
- openpyxl 3.1.5
- biopython 1.81
```

## Reproduce DeepMG with the Released Dataset

### 1. Activate the model environment

```bash
conda activate mg
```

### 2. Prepare data and checkpoints

Place the released large files in the following locations:

```text
dataset/Dataset.xlsx
dataset/embeddings.pkl
dataset/smiles2rep.pkl
dataset/processed.pkl
dataset/PDBs/
pts/MG_Nodes_seed_{40,41,42}_fold_{0,1,2,3,4}.pt
```

The `dataset/*.pkl`, `dataset/PDBs/`, and `pts/*.pt` files are large artifacts and may be distributed separately from the GitHub repository.

### 3. Train / reproduce the model

```bash
python main.py
```

By default, `main.py` loads `dataset/processed.pkl` if it exists. If the cache is absent, `preprocess.py` builds graph data from `dataset/Dataset.xlsx`, `dataset/embeddings.pkl`, `dataset/smiles2rep.pkl`, and `dataset/PDBs/`.

### 4. Predict with released checkpoints

Before prediction, make sure the `pts/` folder exists and contains the 15 trained DeepMG checkpoints from seeds 40, 41, and 42 with folds 0-4.

```bash
python predict.py
```

The output includes each model prediction, the mean prediction across all 15 checkpoints, and a binary label generated with a 0.5 threshold.

## Use a Custom Dataset for Preprocessing, Prediction, and Model Training

### 1. Prepare the input table

Prepare an Excel file named `dataset/Dataset.xlsx` with the same column schema as the released dataset:

```text
ID
Name
label
Smiles
Target name
Sequence
Effector name
Effector Sequence
Smiles_ID
Sequence_ID
Effector_Sequence_ID
```

For prediction-only use, the `label` column is not required. For model training, `label` must be provided.

### 2. Clean the dataset

Environment: `mg`

```bash
conda activate mg
python process/clean.py
```

`clean.py` validates SMILES strings and protein sequences, removes invalid entries, assigns `Smiles_ID`, `Sequence_ID`, and `Effector_Sequence_ID`, and writes cleaned intermediate files. Review the cleaned output before replacing `dataset/Dataset.xlsx` for downstream preprocessing.

### 3. Run protein preprocessing

Environment: `esm`

```bash
conda activate esm
python process/protein_preprocess.py --run-esmfold
```

This command generates:

```text
dataset/sequences.fasta
dataset/embeddings.pkl
dataset/PDBs/
```

The script uses the default paths `dataset/Dataset.xlsx`, `dataset/sequences.fasta`, `dataset/embeddings.pkl`, and `dataset/PDBs/`. Use command-line options only when custom paths are needed.

The older `process/fasta_m.py` and `process/esm.py` scripts are kept as standalone utilities, but `process/protein_preprocess.py` is the recommended entry point.

### 4. Run molecular glue preprocessing

Environment: `mg`

```bash
conda activate mg
python process/Uni.py
```

`Uni.py` generates Uni-Mol molecular representations from the `Smiles` column. The required final file is:

```text
dataset/smiles2rep.pkl
```

### 5. Predict with released models

After preprocessing, make sure these files are available:

```text
dataset/Dataset.xlsx
dataset/embeddings.pkl
dataset/smiles2rep.pkl
dataset/PDBs/
pts/MG_Nodes_seed_{40,41,42}_fold_{0,1,2,3,4}.pt
```

Run:

```bash
conda activate mg
python predict.py
```

The output is saved to `predict/full_predictions.csv` and includes the 15 individual model predictions, `Mean_Prediction`, and `Mean_Label`.

### 6. Train a custom model

Training requires a labeled dataset. Complete the preprocessing steps above, remove any stale cache generated from another dataset, and run:

```bash
conda activate mg
rm dataset/processed.pkl
python main.py
```

Save trained checkpoints in `pts/`. Prediction requires this folder and the trained `.pt` checkpoint files.
