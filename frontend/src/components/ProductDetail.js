import { useEffect, useState } from "react";
import axios from "axios";
import { trackEvent } from "../tracking";

const API_URL = "http://localhost:5000";

export default function ProductDetail({ productId }) {
  const [product, setProduct] = useState(null);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setProduct(null);
    setAdded(false);
    axios
      .get(`${API_URL}/api/products/${productId}`)
      .then((res) => {
        if (!cancelled) setProduct(res.data);
      })
      .catch(() => {
        if (!cancelled) {
          setProduct({
            item_id: productId,
            display_name: `San pham #${productId}`,
            category_display_name: "Chua phan loai",
            image_url: "/placeholders/generic.svg",
            price_note: "Chua co gia xac thuc",
          });
        }
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

  const handleAddToCart = () => {
    trackEvent(productId, "addtocart");
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  };

  if (!product) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
        <div className="h-40 bg-gray-100 rounded-lg mb-4" />
        <div className="h-4 bg-gray-100 rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-100 rounded w-1/3" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 flex gap-4 flex-col">
      <div className="w-full h-40 bg-gray-50 rounded-lg flex items-center justify-center shrink-0">
        <img src={product.image_url} alt={product.display_name} className="max-h-full max-w-full object-contain" />
      </div>

      <div className="flex-1">
        <span className="inline-block text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full mb-2">
          {product.category_display_name}
        </span>
        <h2 className="text-xl font-semibold text-gray-900">{product.display_name}</h2>
        <p className="text-gray-500 mt-1">{product.price_note || "Chua co gia xac thuc"}</p>

        <button
          onClick={handleAddToCart}
          className={`mt-4 px-4 py-2 rounded-lg text-sm font-medium transition ${
            added ? "bg-green-600 text-white" : "bg-indigo-600 text-white hover:bg-indigo-700"
          }`}
        >
          {added ? "Da them vao gio ✓" : "Them vao gio"}
        </button>

        <p className="text-xs text-gray-400 mt-4">
          ID goc RetailRocket: {product.item_id} — ten/anh chi dung de minh hoa (SYNTHETIC)
        </p>
      </div>
    </div>
  );
}
