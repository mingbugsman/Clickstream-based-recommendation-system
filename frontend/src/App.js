import { useState } from "react";
import ProductList from "./components/ProductList";
import ProductDetail from "./components/ProductDetail";
import RecommendationPanel from "./components/RecommendationPanel";
import { getSessionId } from "./tracking";

export default function App() {
  const [selectedProductId, setSelectedProductId] = useState(null);
  const sessionId = getSessionId();

  return (
    <div className="App">
      <h1>Recsys Demo</h1>
      <ProductList onSelect={setSelectedProductId} />
      {selectedProductId && <ProductDetail productId={selectedProductId} />}
      <RecommendationPanel sessionId={sessionId} />
    </div>
  );
}
