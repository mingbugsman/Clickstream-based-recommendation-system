// Ten hien thi trong catalog gia lap luon ket thuc bang " · RR-<item_id>" de dam bao
// duy nhat (xem data/RetailRocket_Catalog_Enrichment_Output/README_IMPORT.md).
// Cat bo hau to nay khi hien thi card cho gon, giu nguyen o trang chi tiet.
export function shortName(displayName) {
  if (!displayName) return "";
  return displayName.split(" · RR-")[0];
}
