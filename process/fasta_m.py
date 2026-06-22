import argparse
from pathlib import Path

import pandas as pd


def parse_args():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate a FASTA file from DeepMG protein sequences.")
    parser.add_argument("--input", default=str(repo_root / "dataset" / "Dataset.xlsx"))
    parser.add_argument("--output", default=str(repo_root / "dataset" / "sequences.fasta"))
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(args.input)
    written_ids = set()

    with open(output_path, "w") as f:
        for _, row in df.iterrows():
            seq_id = row["Sequence_ID"]
            seq = row["Sequence"]
            if seq_id not in written_ids:
                f.write(f">{seq_id}\n{seq}\n")
                written_ids.add(seq_id)

            effector_id = row["Effector_Sequence_ID"]
            effector_seq = row["Effector Sequence"]
            if effector_id not in written_ids:
                f.write(f">{effector_id}\n{effector_seq}\n")
                written_ids.add(effector_id)

    print(f"FASTA file saved to: {output_path}; duplicate IDs were removed.")


if __name__ == "__main__":
    main()
