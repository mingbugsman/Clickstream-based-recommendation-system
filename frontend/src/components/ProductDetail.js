import { useEffect } from "react";
import products from "../data/products";
import { trackEvent } from "../tracking";

export default function ProductDetail({ productId }) {
  const product = products.find((p) => p.id === productId);

  useEffect(() => {
    if (product) {
      trackEvent(product.id, "view");
    }
  }, [product]);

  if (!product) return null;

  return (
    <div className="product-detail">
      <h2>{product.name}</h2>
      <p>Gia: {product.price.toLocaleString()}d</p>
      <button onClick={() => trackEvent(product.id, "addtocart")}>
        Them vao gio
      </button>
    </div>
  );
}
