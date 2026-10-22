import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:5000";

export default function RecommendationPanel({ sessionId }) {
  const [recommendations, setRecommendations] = useState({ markov: [], gru4rec: [] });
  const [model, setModel] = useState("markov");
  const [products, setProducts] = useState({}); // item_id -> product DTO | null

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/api/recommend/${sessionId}`);
        setRecommendations(res.data);
      } catch (err) {
        // bo qua loi khi API/redis chua co du lieu
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // thu tu goi y den tu model (markov/gru4rec), KHONG duoc sap xep/loc lai o day -
  // chi lay them ten/anh de hien thi cho dung item_id model da tra ve
  const items = recommendations[model] || [];

  useEffect(() => {
    const missingIds = items.filter((id) => !(id in products));
    if (missingIds.length === 0) return;

    axios
      .post(`${API_URL}/api/products/batch`, { item_ids: missingIds })
      .then((res) => {
        setProducts((prev) => ({ ...prev, ...res.data }));
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  return (
    <div className="recommendation-panel">
      <h2>Goi y cho ban</h2>
      <div>
        <label>
          <input
            type="radio"
            checked={model === "markov"}
            onChange={() => setModel("markov")}
          />
          Markov Chain
        </label>
        <label>
          <input
            type="radio"
            checked={model === "gru4rec"}
            onChange={() => setModel("gru4rec")}
          />
          GRU4Rec
        </label>
      </div>
      <ul>
        {items.map((itemId) => {
          const product = products[itemId];
          return (
            <li key={itemId}>
              {product
                ? `${product.display_name} — ${product.category_display_name}`
                : `San pham #${itemId}`}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
