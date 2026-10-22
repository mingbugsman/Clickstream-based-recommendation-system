import torch
import torch.nn as nn

PAD_IDX = 0
UNK_IDX = 1


class GRU4Rec(nn.Module):
    """Kien truc dung trong models/train_on_kaggle.ipynb: 1 tang GRU mot chieu,
    hidden_size=100, train theo session-parallel mini-batch + loss TOP1.
    Khac voi ban GRU4Rec cu (dung nn.GRU tren ca chuoi), model nay chay tung
    buoc mot qua forward_step() de phuc vu ca training (session-parallel) lan
    inference tang dan (moi lan co item moi thi chi can 1 buoc GRUCell)."""

    def __init__(self, vocab_size, hidden_dim=100):
        super().__init__()
        self.item_emb = nn.Embedding(vocab_size, hidden_dim, padding_idx=PAD_IDX)
        self.cell = nn.GRUCell(hidden_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim, vocab_size)

    def forward_step(self, item_idx, hidden):
        x = self.item_emb(item_idx)
        h_new = self.cell(x, hidden)
        scores = self.output(h_new)
        return scores, h_new


class GRU4RecCat(nn.Module):
    """Phien ban mo rong co them category - dung cho gru4rec_ext_category.pt,
    hien chua duoc goi trong streaming/inference.py (chi tich hop GRU4Rec CORE)."""

    def __init__(self, vocab_size, cat_vocab_size, item_dim=84, cat_dim=16, hidden_dim=100):
        super().__init__()
        self.item_emb = nn.Embedding(vocab_size, item_dim, padding_idx=PAD_IDX)
        self.cat_emb = nn.Embedding(cat_vocab_size, cat_dim, padding_idx=0)
        self.cell = nn.GRUCell(item_dim + cat_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim, vocab_size)

    def forward_step(self, item_idx, cat_idx, hidden):
        x = torch.cat([self.item_emb(item_idx), self.cat_emb(cat_idx)], dim=-1)
        h_new = self.cell(x, hidden)
        scores = self.output(h_new)
        return scores, h_new
