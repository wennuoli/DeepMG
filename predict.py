import argparse
import os
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.loader import DataLoader
from tqdm import tqdm

from models import DeepMG
from preprocess import seqs2graphs, smis2graphs


def build_predict_data(input_xlsx):
    """Build graph inputs and retain the matching Excel rows."""
    full_df = pd.read_excel(input_xlsx)
    required = {
        "Smiles", "Sequence", "Effector Sequence", "Sequence_ID",
        "Effector_Sequence_ID",
    }
    missing = required.difference(full_df.columns)
    if missing:
        raise ValueError(f"Input Excel is missing columns: {', '.join(sorted(missing))}")

    seq_dict = {}
    for _, row in full_df.iterrows():
        seq_dict[row["Effector_Sequence_ID"]] = row["Effector Sequence"]
        seq_dict[row["Sequence_ID"]] = row["Sequence"]

    prot_graphs = seqs2graphs(seq_dict)
    drug_graphs = smis2graphs(set(full_df["Smiles"].tolist()))
    data = []
    kept_rows = []
    for idx, row in tqdm(full_df.iterrows(), total=len(full_df), desc="Building prediction data"):
        e3_id = row["Effector_Sequence_ID"]
        poi_id = row["Sequence_ID"]
        smiles = row["Smiles"]
        drug = drug_graphs.get(smiles)
        effector = prot_graphs.get(e3_id)
        target = prot_graphs.get(poi_id)
        if drug is not None and effector is not None and target is not None:
            data.append([drug, effector, target])
            kept_rows.append(idx)
        else:
            print(f"[Warning] Skipping row {idx}: missing molecular or protein graph.")

    if not data:
        raise ValueError("No valid graph inputs were found. Check the released feature files.")
    return data, full_df.loc[kept_rows].reset_index(drop=True)


def predict_with_model(test_loader, model, device):
    model.eval()
    predictions = []
    with torch.no_grad():
        for data in test_loader:
            drug_graph = data[0].to(device)
            effector_graph = data[1].to(device)
            target_graph = data[2].to(device)
            output = model(drug_graph, effector_graph, target_graph).view(-1)
            predictions.extend(output.cpu().numpy().tolist())
    return predictions


def load_model(checkpoint_path, device):
    if not Path(checkpoint_path).is_file():
        raise FileNotFoundError(
            f"Model checkpoint not found: {checkpoint_path}\n"
            "Download the release linked in README.md and place deepmg.pt in pts/."
        )
    model = DeepMG()
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict, strict=True)
    return model.to(device).eval()


def parse_args():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Predict with the pretrained DeepMG model.")
    parser.add_argument("--input", type=Path, default=root / "dataset" / "Dataset.xlsx")
    parser.add_argument("--checkpoint", type=Path, default=root / "pts" / "deepmg.pt")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--output", type=Path, default=root / "predict" / "full_predictions.csv")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    args.input = args.input.expanduser().resolve()
    args.checkpoint = args.checkpoint.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    return args


def main():
    args = parse_args()
    # Existing graph builders resolve the released features from the repository root.
    os.chdir(Path(__file__).resolve().parent)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(args.checkpoint, device)
    test_data, full_df = build_predict_data(args.input)
    test_loader = DataLoader(test_data, batch_size=args.batch_size, num_workers=0)
    predictions = predict_with_model(test_loader, model, device)
    if len(predictions) != len(full_df):
        raise RuntimeError("Prediction count does not match the retained input rows.")
    full_df["Prediction"] = predictions
    full_df["Predicted_Label"] = [int(value > 0.5) for value in predictions]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_csv(args.output, index=False)
    print(f"[INFO] Saved {len(predictions)} predictions to {args.output}")


if __name__ == "__main__":
    main()
