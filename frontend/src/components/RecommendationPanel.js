import { useEffect, useState } from "react";
import axios from "axios";
import { shortName } from "../format";

const API_URL = "http://localhost:5000";

function formatTime(date) {
  return date.toLocaleTimeString("vi-VN", { hour12: false });
}

export default function RecommendationPanel({ sessionId, onSelect, hasHistory }) {
  const [recommendations, setRecommendations] = useState({ markov: [], gru4rec: [] });
  const [model, setModel] = useState("markov");
  const [products, setProducts] = useState({}); // item_id -> product DTO | null
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchReco = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/recommend/${sessionId}`);
        setRecommendations(res.data);
        setLastUpdated(new Date());
      } catch (err) {
        // bo qua loi khi API/redis chua co du lieu
      }
    };
    fetchReco();
    const interval = setInterval(fetchReco, 2000);
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
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold text-gray-800">Goi y cho ban</h2>
        <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 text-sm">
          {[
            { key: "markov", label: "Markov Chain" },
            { key: "gru4rec", label: "GRU4Rec" },
          ].map((opt) => (
            <button
              key={opt.key}
              onClick={() => setModel(opt.key)}
              className={`px-3 py-1 rounded-md transition ${
                model === opt.key ? "bg-indigo-600 text-white shadow-sm" : "text-gray-500 hover:text-gray-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <p className="text-xs text-gray-400 mb-4">
        {hasHistory ? "Dua tren hanh vi phien hien tai" : "Chua co hanh vi — dang hien pho bien"}
        {lastUpdated && ` · cap nhat luc ${formatTime(lastUpdated)}`}
      </p>

      {items.length === 0 ? (
        <p className="text-sm text-gray-400 py-6 text-center">
          He thong chua tra ve goi y nao cho phien nay.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {items.map((itemId) => {
            const product = products[itemId];
            return (
              <button
                key={itemId}
                onClick={() => onSelect && onSelect(itemId)}
                className="text-left bg-gray-50 rounded-lg border border-gray-100 overflow-hidden hover:shadow-sm hover:border-indigo-300 transition"
              >
                <div className="aspect-square bg-white flex items-center justify-center p-2">
                  <img
                    src={product ? product.image_url : "/placeholders/generic.svg"}
                    alt={product ? product.display_name : itemId}
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
                <div className="p-2">
                  <p className="text-xs text-gray-700 font-medium line-clamp-2 min-h-[2rem]">
                    {product ? shortName(product.display_name) : `San pham #${itemId}`}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
