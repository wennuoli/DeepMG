import argparse
from pathlib import Path

import pandas as pd
from rdkit import Chem


VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def is_valid_smiles(smiles: str) -> tuple:
    """Check whether a SMILES string can be parsed by RDKit."""
    if pd.isna(smiles) or not isinstance(smiles, str) or smiles.strip() == "":
        return False, "empty or non-string value"

    invalid_values = {"Unknown", "unknown", "UNKNOWN", "N/A", "n/a", "NA", "na", "None", "none", "NULL", "null"}
    if smiles in invalid_values:
        return False, f"invalid value: {smiles}"

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, "SMILES syntax error"
        return True, "valid"
    except Exception as exc:
        return False, f"RDKit error: {str(exc)[:50]}"


def is_valid_protein(seq: str) -> tuple:
    """Check whether a protein sequence contains only standard amino acids."""
    if pd.isna(seq) or not isinstance(seq, str) or seq.strip() == "":
        return False, "empty or non-string value"

    invalid_chars = set(seq) - VALID_AA
    if invalid_chars:
        return False, f"non-standard amino acids: {', '.join(sorted(invalid_chars))}"

    if len(seq) >= 3000:
        return False, f"sequence too long: {len(seq)} >= 3000"

    return True, "valid"


def filter_invalid(input_file: str, output_file: str):
    """Filter invalid rows and write a cleaning report."""
    print("Starting data cleaning...")

    df = pd.read_excel(input_file)
    print(f"Input rows: {len(df)}")

    required_columns = ["Smiles", "Sequence", "Effector Sequence"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    print("Validating SMILES...")
    smiles_results = df["Smiles"].apply(is_valid_smiles)
    df["smiles_valid"] = [result[0] for result in smiles_results]
    df["smiles_error"] = [result[1] for result in smiles_results]

    print("Validating target protein sequences...")
    protein_results = df["Sequence"].apply(is_valid_protein)
    df["protein_valid"] = [result[0] for result in protein_results]
    df["protein_error"] = [result[1] for result in protein_results]

    print("Validating effector protein sequences...")
    effector_results = df["Effector Sequence"].apply(is_valid_protein)
    df["effector_valid"] = [result[0] for result in effector_results]
    df["effector_error"] = [result[1] for result in effector_results]

    total_rows = len(df)
    valid_smiles = int(df["smiles_valid"].sum())
    valid_proteins = int(df["protein_valid"].sum())
    valid_effectors = int(df["effector_valid"].sum())

    print("\nValidation summary:")
    print(f"  Valid SMILES: {valid_smiles}/{total_rows} ({valid_smiles / total_rows * 100:.2f}%)")
    print(f"  Valid target sequences: {valid_proteins}/{total_rows} ({valid_proteins / total_rows * 100:.2f}%)")
    print(f"  Valid effector sequences: {valid_effectors}/{total_rows} ({valid_effectors / total_rows * 100:.2f}%)")

    invalid_smiles = df[~df["smiles_valid"]]
    if len(invalid_smiles) > 0:
        print(f"\nInvalid SMILES details ({len(invalid_smiles)} rows):")
        for error_type, count in invalid_smiles["smiles_error"].value_counts().items():
            print(f"  {error_type}: {count}")

        print("\nInvalid SMILES examples:")
        for i, (idx, row) in enumerate(invalid_smiles.head(10).iterrows()):
            smiles_preview = str(row["Smiles"])[:50] + "..." if len(str(row["Smiles"])) > 50 else str(row["Smiles"])
            print(f"  {i + 1}. row {idx}: {smiles_preview} -> {row['smiles_error']}")

    invalid_proteins = df[~df["protein_valid"]]
    if len(invalid_proteins) > 0:
        print(f"\nInvalid target sequence details ({len(invalid_proteins)} rows):")
        for error_type, count in invalid_proteins["protein_error"].value_counts().items():
            print(f"  {error_type}: {count}")

        print("\nInvalid target sequence examples:")
        for i, (idx, row) in enumerate(invalid_proteins.head(10).iterrows()):
            seq_preview = str(row["Sequence"])[:30] + "..." if len(str(row["Sequence"])) > 30 else str(row["Sequence"])
            print(f"  {i + 1}. row {idx}: {seq_preview} -> {row['protein_error']}")

    invalid_effectors = df[~df["effector_valid"]]
    if len(invalid_effectors) > 0:
        print(f"\nInvalid effector sequence details ({len(invalid_effectors)} rows):")
        for error_type, count in invalid_effectors["effector_error"].value_counts().items():
            print(f"  {error_type}: {count}")

        print("\nInvalid effector sequence examples:")
        for i, (idx, row) in enumerate(invalid_effectors.head(10).iterrows()):
            seq_preview = (
                str(row["Effector Sequence"])[:30] + "..."
                if len(str(row["Effector Sequence"])) > 30
                else str(row["Effector Sequence"])
            )
            print(f"  {i + 1}. row {idx}: {seq_preview} -> {row['effector_error']}")

    df_clean = df[df["smiles_valid"] & df["protein_valid"] & df["effector_valid"]].copy()
    df_clean = df_clean.drop(
        columns=[
            "smiles_valid",
            "smiles_error",
            "protein_valid",
            "protein_error",
            "effector_valid",
            "effector_error",
        ]
    )

    print("\nCleaning complete.")
    print(f"  Input rows: {total_rows}")
    print(f"  Clean rows: {len(df_clean)}")
    print(f"  Retention rate: {len(df_clean) / total_rows * 100:.2f}%")
    print(f"  Removed rows: {total_rows - len(df_clean)}")

    df_clean.to_excel(output_file, index=False)
    print(f"Cleaned data saved to: {output_file}")

    report_file = output_file.replace(".xlsx", "_cleaning_report.xlsx")
    with pd.ExcelWriter(report_file, engine="openpyxl") as writer:
        df_clean.to_excel(writer, sheet_name="Cleaned_Data", index=False)

        invalid_data = df[~(df["smiles_valid"] & df["protein_valid"] & df["effector_valid"])]
        if len(invalid_data) > 0:
            invalid_data.to_excel(writer, sheet_name="Invalid_Data", index=False)

        summary_df = pd.DataFrame(
            {
                "Metric": ["Input rows", "Valid rows", "Invalid rows", "Retention rate"],
                "Value": [
                    total_rows,
                    len(df_clean),
                    total_rows - len(df_clean),
                    f"{len(df_clean) / total_rows * 100:.2f}%",
                ],
            }
        )
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    print(f"Cleaning report saved to: {report_file}")
    return df_clean


def add_sequence_ids(df):
    """Add SMILES and protein sequence identifiers."""
    unique_smiles = df["Smiles"].dropna().unique()
    smiles_to_id = {smiles: i + 1 for i, smiles in enumerate(unique_smiles)}
    df["Smiles_ID"] = df["Smiles"].map(smiles_to_id)

    all_sequences = []
    all_sequences.extend(df["Sequence"].dropna().unique())
    all_sequences.extend(df["Effector Sequence"].dropna().unique())

    unique_sequences = list(dict.fromkeys(all_sequences))
    sequence_to_id = {seq: i + 1 for i, seq in enumerate(unique_sequences)}

    df["Sequence_ID"] = df["Sequence"].map(sequence_to_id)
    df["Effector_Sequence_ID"] = df["Effector Sequence"].map(sequence_to_id)

    print(
        "Identifier assignment complete: "
        f"SMILES={len(unique_smiles)}, "
        f"Sequence_ID={df['Sequence_ID'].nunique()}, "
        f"Effector_Sequence_ID={df['Effector_Sequence_ID'].nunique()}"
    )
    return df


def generate_fasta(df, output_file="sequences.fasta"):
    """Generate a FASTA file from target and effector protein sequences."""
    sequences_data = []

    for _, row in df.dropna(subset=["Sequence", "Sequence_ID"]).iterrows():
        sequences_data.append({"id": f"{row['Sequence_ID']}", "sequence": row["Sequence"]})

    for _, row in df.dropna(subset=["Effector Sequence", "Effector_Sequence_ID"]).iterrows():
        sequences_data.append({"id": f"{row['Effector_Sequence_ID']}", "sequence": row["Effector Sequence"]})

    unique_sequences = {}
    for item in sequences_data:
        if item["sequence"] not in unique_sequences:
            unique_sequences[item["sequence"]] = item["id"]

    for sequence, seq_id in unique_sequences.items():
        print(f"{seq_id}:({len(sequence)})")

    with open(output_file, "w") as f:
        for sequence, seq_id in unique_sequences.items():
            f.write(f">{seq_id}\n")
            f.write(f"{sequence}\n")

    print(f"FASTA file saved to: {output_file}")
    print(f"Unique sequences: {len(unique_sequences)}")
    return unique_sequences


def parse_args():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Clean a DeepMG-format dataset and assign representation IDs.")
    parser.add_argument("--input", default=str(repo_root / "dataset" / "Dataset.xlsx"))
    parser.add_argument("--output", default=str(repo_root / "dataset" / "Dataset_clean.xlsx"))
    parser.add_argument("--with-ids-output", default=str(repo_root / "dataset" / "Dataset_clean_with_ids.xlsx"))
    parser.add_argument("--fasta", default=str(repo_root / "dataset" / "sequences.fasta"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    filter_invalid(args.input, args.output)

    df = pd.read_excel(args.output)
    df_with_ids = add_sequence_ids(df)
    df_with_ids.to_excel(args.with_ids_output, index=False)

    generate_fasta(df_with_ids, args.fasta)
    print("Processing complete.")
