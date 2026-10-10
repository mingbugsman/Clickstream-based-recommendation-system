import products from "../data/products";

export default function ProductList({ onSelect }) {
  return (
    <div className="product-list">
      <h2>San pham</h2>
      <ul>
        {products.map((p) => (
          <li key={p.id} onClick={() => onSelect(p.id)}>
            {p.name} - {p.price.toLocaleString()}d
          </li>
        ))}
      </ul>
    </div>
  );
}
