import argparse
import pickle
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm


def parse_args():
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Generate ESM protein embeddings for DeepMG.")
    parser.add_argument("--input", default=str(repo_root / "dataset" / "Dataset.xlsx"))
    parser.add_argument("--output", default=str(repo_root / "dataset" / "embeddings.pkl"))
    parser.add_argument("--cuda", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model, alphabet = torch.hub.load("facebookresearch/esm:main", "esm2_t36_3B_UR50D")
    if args.cuda:
        model = model.cuda()
    batch_converter = alphabet.get_batch_converter()
    model.eval()

    df = pd.read_excel(args.input)
    id_to_sequence = {}
    for _, row in df.iterrows():
        id_to_sequence[str(row["Sequence_ID"])] = row["Sequence"]
        id_to_sequence[str(row["Effector_Sequence_ID"])] = row["Effector Sequence"]

    embeddings = {}
    for seq_id, sequence in tqdm(id_to_sequence.items(), desc="Generating ESM embeddings"):
        batch_labels, batch_strs, batch_tokens = batch_converter([(seq_id, sequence)])
        if args.cuda:
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

    with open(output_path, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"ESM embeddings saved to: {output_path}")


if __name__ == "__main__":
    main()
