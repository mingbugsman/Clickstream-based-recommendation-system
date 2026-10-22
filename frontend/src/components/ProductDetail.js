import { useEffect, useState } from "react";
import axios from "axios";
import { trackEvent } from "../tracking";

const API_URL = "http://localhost:5000";

export default function ProductDetail({ productId }) {
  const [product, setProduct] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setProduct(null);
    axios
      .get(`${API_URL}/api/products/${productId}`)
      .then((res) => {
        if (!cancelled) setProduct(res.data);
      })
      .catch(() => {
        if (!cancelled) setProduct({ item_id: productId, display_name: `San pham #${productId}`, category_display_name: "Chua phan loai" });
      });
    return () => {
      cancelled = true;
    };
  }, [productId]);

  // event "view" gui ngay khi mo trang chi tiet, dung item_id GOC - khong phu thuoc
  // vao catalog gia lap da load xong hay chua, de khong lam tre du lieu tracking
  useEffect(() => {
    trackEvent(productId, "view");
  }, [productId]);

  if (!product) return <div className="product-detail">Dang tai san pham...</div>;

  return (
    <div className="product-detail">
      <h2>{product.display_name}</h2>
      <p>Danh muc: {product.category_display_name}</p>
      <p>Gia: {product.price_note || "Chua co gia xac thuc"}</p>
      <p style={{ fontSize: 12, color: "#888" }}>
        ID goc RetailRocket: {product.item_id} — ten/anh chi dung de minh hoa (SYNTHETIC)
      </p>
      <button onClick={() => trackEvent(productId, "addtocart")}>
        Them vao gio
      </button>
    </div>
  );
}
