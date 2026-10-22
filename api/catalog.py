import os

import pandas as pd

CATALOG_PATH = os.environ.get(
    "CATALOG_PATH", "data/RetailRocket_Catalog_Enrichment_Output/product_catalog.csv"
)
CATEGORY_MAPPING_PATH = os.environ.get(
    "CATEGORY_MAPPING_PATH", "data/RetailRocket_Catalog_Enrichment_Output/category_mapping.csv"
)

_catalog_by_id = None
_catalog_sorted_ids = None  # item_id sap theo event_count giam dan, dung cho phan trang
_category_rows = None

DISPLAY_FIELDS = [
    "item_id",
    "original_category_id",
    "display_name",
    "name_source",
    "category_display_name",
    "category_name_source",
    "department_name",
    "image_url",
    "image_source",
    "availability_status",
    "event_count",
]


def load_catalog():
    """Nap catalog gia lap 1 lan khi khoi dong API. item_id la ID that cua
    RetailRocket, khop truc tiep voi item2idx.pkl ma model dang dung - KHONG
    duoc dung bat ky truong SYNTHETIC nao (display_name, category_display_name...)
    de anh huong toi logic goi y, chi phuc vu hien thi."""
    global _catalog_by_id, _catalog_sorted_ids, _category_rows

    df = pd.read_csv(CATALOG_PATH, dtype={"item_id": str, "original_category_id": str})
    df = df[DISPLAY_FIELDS].fillna("")
    df = df.sort_values("event_count", ascending=False)  # san pham co lich su len truoc, de demo "song dong" hon

    _catalog_sorted_ids = df["item_id"].tolist()
    _catalog_by_id = df.set_index("item_id", drop=False).to_dict(orient="index")

    cat_df = pd.read_csv(
        CATEGORY_MAPPING_PATH,
        dtype={"category_id": str, "parent_category_id": str, "root_category_id": str},
    ).fillna("")
    _category_rows = cat_df[
        ["category_id", "parent_category_id", "department_name", "category_display_name"]
    ].to_dict(orient="records")

    print(f"[catalog] da nap {len(_catalog_by_id)} san pham, {len(_category_rows)} category")


def _to_product_dto(row):
    return {
        "item_id": row["item_id"],
        "display_name": row["display_name"] or f"San pham #{row['item_id']}",
        "name_source": row["name_source"] or "UNKNOWN",
        "category_display_name": row["category_display_name"] or "Chua phan loai",
        "category_id": row["original_category_id"] or None,
        "department_name": row["department_name"] or None,
        "image_url": row["image_url"] or "/placeholders/generic.svg",
        "image_source": row["image_source"] or "PLACEHOLDER",
        "availability_status": row["availability_status"] or "UNKNOWN",
        "price": None,
        "price_note": "Chua co gia xac thuc",
    }


def get_product(item_id):
    if _catalog_by_id is None:
        load_catalog()
    row = _catalog_by_id.get(str(item_id))
    return _to_product_dto(row) if row else None


def get_products_batch(item_ids):
    if _catalog_by_id is None:
        load_catalog()
    result = {}
    for item_id in item_ids:
        row = _catalog_by_id.get(str(item_id))
        result[str(item_id)] = _to_product_dto(row) if row else None
    return result


def list_products(cursor=0, limit=24, category_id=None):
    if _catalog_by_id is None:
        load_catalog()

    ids = _catalog_sorted_ids
    if category_id:
        ids = [i for i in ids if _catalog_by_id[i]["original_category_id"] == str(category_id)]

    page_ids = ids[cursor:cursor + limit]
    items = [_to_product_dto(_catalog_by_id[i]) for i in page_ids]
    next_cursor = cursor + limit if cursor + limit < len(ids) else None

    return {"items": items, "next_cursor": next_cursor, "total": len(ids)}


def list_categories():
    if _category_rows is None:
        load_catalog()
    return _category_rows
