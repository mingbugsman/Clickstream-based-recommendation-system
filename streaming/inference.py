import pickle
import sys
import os

import torch

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "models"))
from gru4rec import GRU4Rec, PAD_IDX, UNK_IDX

_markov_matrix = None
_gru_model = None
_item2idx = None
_idx2item = None


def load_models():
    global _markov_matrix, _gru_model, _item2idx, _idx2item

    with open("models/markov.pkl", "rb") as f:
        _markov_matrix = pickle.load(f)

    with open("models/item2idx.pkl", "rb") as f:
        _item2idx = pickle.load(f)
    # "<pad>"/"<unk>" khong phai san pham that, bo qua khi anh xa nguoc
    _idx2item = {idx: item for item, idx in _item2idx.items() if item not in ("<pad>", "<unk>")}

    _gru_model = GRU4Rec(vocab_size=len(_item2idx))
    _gru_model.load_state_dict(torch.load("models/gru4rec_core.pt", map_location="cpu"))
    _gru_model.eval()


def get_topk_markov(last_item_id, k=5):
    if _markov_matrix is None or last_item_id not in _markov_matrix:
        return []
    next_items = _markov_matrix[last_item_id]
    ranked = sorted(next_items.items(), key=lambda kv: kv[1], reverse=True)
    return [item for item, _ in ranked[:k]]


def get_topk_gru(session_items, k=5):
    if _gru_model is None or not session_items:
        return []

    with torch.no_grad():
        hidden = torch.zeros(1, _gru_model.cell.hidden_size)
        scores = None
        for item_id in session_items:
            idx = _item2idx.get(item_id, UNK_IDX)
            idx_t = torch.tensor([idx], dtype=torch.long)
            scores, hidden = _gru_model.forward_step(idx_t, hidden)

        scores = scores.clone()
        scores[0, PAD_IDX] = float("-inf")
        scores[0, UNK_IDX] = float("-inf")
        topk = torch.topk(scores, k=min(k, scores.shape[-1] - 1), dim=-1).indices[0].tolist()

    return [_idx2item[i] for i in topk if i in _idx2item]
