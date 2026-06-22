import argparse
import os
import pickle

import pandas as pd
import torch
from torch_geometric.loader import DataLoader
from tqdm import tqdm

from models import DeepMG
from preprocess import seqs2graphs, smis2graphs


def build_predict_data(input_xlsx, processed_path=None):
    """Build graph inputs for prediction from a DeepMG-format Excel file."""
    full_df = pd.read_excel(input_xlsx)

    if processed_path and os.path.exists(processed_path):
        print(f"[INFO] Loading cached prediction data: {processed_path}")
        with open(processed_path, "rb") as f:
            data = pickle.load(f)
        return data, full_df

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

        if drug_graphs.get(smiles) and prot_graphs.get(e3_id) and prot_graphs.get(poi_id):
            data.append([drug_graphs[smiles], prot_graphs[e3_id], prot_graphs[poi_id]])
            kept_rows.append(idx)
        else:
            print(
                "[Warning] Skipping sample due to missing graph input: "
                f"row={idx}, e3={e3_id}, poi={poi_id}, smiles={smiles}"
            )

    full_df = full_df.loc[kept_rows].reset_index(drop=True)

    if processed_path:
        os.makedirs(os.path.dirname(processed_path) or ".", exist_ok=True)
        with open(processed_path, "wb") as f:
            pickle.dump(data, f)
        print(f"[INFO] Saved cached prediction data: {processed_path}")

    return data, full_df


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
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(
            f"Model checkpoint not found: {checkpoint_path}\n"
            "Please make sure the pts folder exists and contains trained .pt files."
        )

    model = DeepMG().to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def parse_args():
    parser = argparse.ArgumentParser(description="Run DeepMG prediction with trained checkpoints.")
    parser.add_argument("--input", default=os.path.join("dataset", "Dataset.xlsx"), help="Input Excel file.")
    parser.add_argument(
        "--processed",
        default=os.path.join("dataset", "predict_processed.pkl"),
        help="Optional cache for prediction graph data.",
    )
    parser.add_argument("--checkpoint-dir", default="pts", help="Directory containing trained .pt checkpoints.")
    parser.add_argument("--seeds", nargs="+", type=int, default=[40, 41, 42], help="Random seeds to ensemble.")
    parser.add_argument("--folds", nargs="+", type=int, default=[0, 1, 2, 3, 4], help="Fold checkpoints to ensemble.")
    parser.add_argument(
        "--checkpoint-pattern",
        default="MG_Nodes_seed_{seed}_fold_{fold}.pt",
        help="Checkpoint filename pattern. Available fields: {seed}, {fold}.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", default=os.path.join("predict", "full_predictions.csv"))
    return parser.parse_args()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.isdir(args.checkpoint_dir):
        raise FileNotFoundError(
            f"Checkpoint directory not found: {args.checkpoint_dir}\n"
            "Create a pts folder and place trained model checkpoints there before prediction."
        )

    test_data, full_df = build_predict_data(args.input, args.processed)
    test_loader = DataLoader(test_data, batch_size=args.batch_size, num_workers=1)

    all_predictions = []
    for seed in args.seeds:
        for fold in args.folds:
            checkpoint_name = args.checkpoint_pattern.format(seed=seed, fold=fold)
            checkpoint = os.path.join(args.checkpoint_dir, checkpoint_name)
            model = load_model(checkpoint, device)
            preds = predict_with_model(test_loader, model, device)
            all_predictions.append(preds)
            full_df[f"Seed_{seed}_Fold_{fold}_Prediction"] = preds

    mean_predictions = torch.tensor(all_predictions, dtype=torch.float32).mean(dim=0).numpy()
    full_df = full_df.iloc[: len(mean_predictions)].copy()
    full_df["Mean_Prediction"] = mean_predictions
    full_df["Mean_Label"] = (torch.tensor(mean_predictions) > 0.5).int().numpy()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    full_df.to_csv(args.output, index=False)
    print(f"[INFO] Saved predictions to {args.output}")


if __name__ == "__main__":
    main()
