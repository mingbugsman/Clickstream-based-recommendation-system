import { useEffect, useState } from "react";
import axios from "axios";
import { shortName } from "../format";

const API_URL = "http://localhost:5000";

// Hien thi duong di hanh vi trong phien ("Da xem: A -> B -> C") de nguoi xem demo
// thay ro NHAN-QUA giua hanh dong vua lam va goi y ben duoi thay doi the nao -
// day la thong tin da co san o App.js (history), khong anh huong gi den model/API goi y.
export default function ViewHistory({ history }) {
  const [products, setProducts] = useState({});

  useEffect(() => {
    const missing = history.filter((id) => !(id in products));
    if (missing.length === 0) return;
    axios
      .post(`${API_URL}/api/products/batch`, { item_ids: missing })
      .then((res) => setProducts((prev) => ({ ...prev, ...res.data })))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [history]);

  if (history.length === 0) {
    return (
      <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg px-4 py-3">
        Chua co lich su tuong tac trong phien nay. Hay xem mot san pham ben trai.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
        Da xem trong phien nay
      </p>
      <div className="flex items-center flex-wrap gap-1.5 text-sm">
        {history.map((id, idx) => (
          <span key={`${id}-${idx}`} className="flex items-center gap-1.5">
            {idx > 0 && <span className="text-gray-300">→</span>}
            <span
              className={`px-2 py-0.5 rounded-md ${
                idx === history.length - 1
                  ? "bg-indigo-100 text-indigo-700 font-medium"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {products[id] ? shortName(products[id].display_name) : `#${id}`}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
