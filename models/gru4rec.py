import torch
import torch.nn as nn


class GRU4Rec(nn.Module):
    def __init__(self, n_items, embed_dim=64, hidden_dim=100):
        super().__init__()
        self.embedding = nn.Embedding(n_items, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, n_items)

    def forward(self, item_seq):
        x = self.embedding(item_seq)
        _, h = self.gru(x)
        return self.output(h.squeeze(0))
