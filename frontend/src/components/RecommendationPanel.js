import { useEffect, useState } from "react";
import axios from "axios";

export default function RecommendationPanel({ sessionId }) {
  const [recommendations, setRecommendations] = useState({ markov: [], gru4rec: [] });
  const [model, setModel] = useState("markov");

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`http://localhost:5000/api/recommend/${sessionId}`);
        setRecommendations(res.data);
      } catch (err) {
        // bo qua loi khi API/redis chua co du lieu
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const items = recommendations[model] || [];

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
        {items.map((itemId) => (
          <li key={itemId}>{itemId}</li>
        ))}
      </ul>
    </div>
  );
}
