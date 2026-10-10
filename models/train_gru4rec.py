import os
import pickle
import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset, DataLoader
from cassandra.cluster import Cluster

from gru4rec import GRU4Rec

# gioi han so luong CPU thread de tranh tinh trang qua tai luong (oversubscription)
# lam cham training thay vi tang toc tren may nhieu core
torch.set_num_threads(4)

MAX_SEQ_LEN = 20
BATCH_SIZE = 512
EPOCHS = 3
LR = 1e-3

CASSANDRA_HOST = os.environ.get("CASSANDRA_HOST", "127.0.0.1")


def load_sessions():
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect("recsys")
    rows = session.execute("SELECT session_id, item_id, event_time FROM events")
    df = pd.DataFrame(list(rows))
    df = df.sort_values(["session_id", "event_time"])

    sequences = []
    for _, group in df.groupby("session_id"):
        items = group["item_id"].tolist()
        if len(items) >= 2:
            sequences.append(items)
    return sequences


def build_vocab(sequences):
    item2idx = {"<pad>": 0}
    for seq in sequences:
        for item in seq:
            if item not in item2idx:
                item2idx[item] = len(item2idx)
    return item2idx


class SessionDataset(Dataset):
    def __init__(self, sequences, item2idx):
        self.samples = []
        for seq in sequences:
            idx_seq = [item2idx[i] for i in seq][-MAX_SEQ_LEN - 1:]
            for t in range(1, len(idx_seq)):
                history = idx_seq[:t]
                target = idx_seq[t]
                self.samples.append((history, target))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        history, target = self.samples[idx]
        return torch.tensor(history, dtype=torch.long), target


def collate(batch):
    histories, targets = zip(*batch)
    padded = pad_sequence(histories, batch_first=True, padding_value=0)
    return padded, torch.tensor(targets, dtype=torch.long)


def main():
    print("loading sessions tu cassandra...", flush=True)
    sequences = load_sessions()
    print(f"loaded {len(sequences)} sessions", flush=True)

    item2idx = build_vocab(sequences)
    print(f"vocab size: {len(item2idx)}", flush=True)

    dataset = SessionDataset(sequences, item2idx)
    print(f"built {len(dataset)} training samples", flush=True)

    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate)
    print(f"batches per epoch: {len(loader)}", flush=True)

    model = GRU4Rec(n_items=len(item2idx))
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(EPOCHS):
        total_loss = 0.0
        for batch_idx, (history, target) in enumerate(loader):
            optimizer.zero_grad()
            logits = model(history)
            loss = criterion(logits, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            if batch_idx % 50 == 0:
                print(f"  epoch {epoch + 1} batch {batch_idx}/{len(loader)}", flush=True)
        print(f"epoch {epoch + 1}/{EPOCHS} - loss {total_loss / len(loader):.4f}", flush=True)

    torch.save(model.state_dict(), "models/gru4rec.pt")
    with open("models/item2idx.pkl", "wb") as f:
        pickle.dump(item2idx, f)

    print("Done training GRU4Rec,", len(item2idx), "items")


if __name__ == "__main__":
    main()
