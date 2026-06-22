import argparse
import os
import pickle
import subprocess
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm


def resolve_path(path):
    return Path(path).expanduser().resolve()


def load_unique_sequences(dataset_path):
    df = pd.read_excel(dataset_path)
    id_to_sequence = {}

    for _, row in df.iterrows():
        id_to_sequence[str(row["Sequence_ID"])] = row["Sequence"]
        id_to_sequence[str(row["Effector_Sequence_ID"])] = row["Effector Sequence"]

    return id_to_sequence


def write_fasta(id_to_sequence, fasta_path):
    fasta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fasta_path, "w") as f:
        for seq_id, sequence in id_to_sequence.items():
            f.write(f">{seq_id}\n{sequence}\n")

    print(f"FASTA file saved to: {fasta_path}")
    print(f"Unique protein sequences: {len(id_to_sequence)}")


def generate_esm_embeddings(id_to_sequence, output_path, use_cuda=False):
    model, alphabet = torch.hub.load("facebookresearch/esm:main", "esm2_t36_3B_UR50D")
    if use_cuda:
        model = model.cuda()

    batch_converter = alphabet.get_batch_converter()
    model.eval()

    embeddings = {}
    for seq_id, sequence in tqdm(id_to_sequence.items(), desc="Generating ESM embeddings"):
        batch_labels, batch_strs, batch_tokens = batch_converter([(seq_id, sequence)])
        if use_cuda:
            batch_tokens = batch_tokens.cuda()

        batch_lens = (batch_tokens != alphabet.padding_idx).sum(1)
        assert len(batch_lens) == 1

        with torch.no_grad():
            results = model(batch_tokens, repr_layers=[36])

        token_representations = results["representations"][36][0][1 : batch_lens[0] - 1].cpu()
        embeddings[seq_id] = {
            "token_representations": token_representations,
            "sequence_representation": token_representations.mean(0),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"ESM embeddings saved to: {output_path}")


def run_esmfold(fasta_path, pdb_dir, max_tokens_per_batch, chunk_size):
    pdb_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "esm-fold",
        "-i",
        str(fasta_path),
        "-o",
        str(pdb_dir),
        "--max-tokens-per-batch",
        str(max_tokens_per_batch),
        "--chunk-size",
        str(chunk_size),
    ]
    print("Running ESMFold:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_args():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate protein FASTA, ESM embeddings, and optional ESMFold PDBs.")
    parser.add_argument("--input", default=str(repo_root / "dataset" / "Dataset.xlsx"), help="Input DeepMG dataset.")
    parser.add_argument("--fasta", default=str(repo_root / "dataset" / "sequences.fasta"), help="Output FASTA file.")
    parser.add_argument("--embeddings", default=str(repo_root / "dataset" / "embeddings.pkl"), help="Output ESM embeddings.")
    parser.add_argument("--pdb-dir", default=str(repo_root / "dataset" / "PDBs"), help="Output PDB directory.")
    parser.add_argument("--cuda", action="store_true", help="Use CUDA for ESM embedding generation.")
    parser.add_argument("--run-esmfold", action="store_true", help="Run esm-fold after FASTA generation.")
    parser.add_argument("--skip-embeddings", action="store_true", help="Only generate FASTA and optionally PDBs.")
    parser.add_argument("--max-tokens-per-batch", type=int, default=1)
    parser.add_argument("--chunk-size", type=int, default=128)
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_path = resolve_path(args.input)
    fasta_path = resolve_path(args.fasta)
    embeddings_path = resolve_path(args.embeddings)
    pdb_dir = resolve_path(args.pdb_dir)

    id_to_sequence = load_unique_sequences(dataset_path)
    write_fasta(id_to_sequence, fasta_path)

    if not args.skip_embeddings:
        generate_esm_embeddings(id_to_sequence, embeddings_path, use_cuda=args.cuda)

    if args.run_esmfold:
        run_esmfold(fasta_path, pdb_dir, args.max_tokens_per_batch, args.chunk_size)


if __name__ == "__main__":
    main()
