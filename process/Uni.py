import pickle
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm
from unimol_tools import UniMolRepr


def parse_args():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate Uni-Mol molecular representations for DeepMG.")
    parser.add_argument("--input", default=str(repo_root / "dataset" / "Dataset.xlsx"))
    parser.add_argument("--output", default=str(repo_root / "dataset" / "smiles2rep.pkl"))
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clf = UniMolRepr(data_type="molecule", remove_hs=False)
    df = pd.read_excel(args.input)
    smiles_list = df.loc[:, "Smiles"].tolist()

    smiles2rep = {}
    for smiles in tqdm(smiles_list, desc="Processing SMILES"):
        if smiles in smiles2rep:
            continue

        unimol_repr = clf.get_repr([smiles], return_atomic_reprs=True)
        smiles2rep[smiles] = {
            "cls_repr": np.array(unimol_repr["cls_repr"]),
            "atomic_reprs": np.array(unimol_repr["atomic_reprs"]),
        }

    with open(output_path, "wb") as f:
        pickle.dump(smiles2rep, f)

    print(f"Saved molecular representations for {len(smiles2rep)} unique SMILES to: {output_path}")


if __name__ == "__main__":
    main()
