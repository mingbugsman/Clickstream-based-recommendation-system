import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:5000";

const EVENT_STYLE = {
  view: "bg-blue-50 text-blue-700",
  addtocart: "bg-green-50 text-green-700",
  transaction: "bg-amber-50 text-amber-700",
};

function timeAgo(ts) {
  const diffSec = Math.max(0, Math.floor((Date.now() - ts) / 1000));
  if (diffSec < 5) return "vua xong";
  if (diffSec < 60) return `${diffSec}s truoc`;
  return `${Math.floor(diffSec / 60)}p truoc`;
}

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [tick, setTick] = useState(0); // ep re-render de "thoi gian truoc" cap nhat

  useEffect(() => {
    const fetchEvents = () => {
      axios
        .get(`${API_URL}/api/events/recent`, { params: { limit: 20 } })
        .then((res) => setEvents(res.data))
        .catch(() => {});
    };
    fetchEvents();
    const interval = setInterval(fetchEvents, 2000);
    const tickInterval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => {
      clearInterval(interval);
      clearInterval(tickInterval);
    };
  }, []);

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-lg font-semibold text-gray-800 mb-1">Real-time Event Monitor</h2>
      <p className="text-sm text-gray-400 mb-4">
        Cac su kien <code>view</code> / <code>addtocart</code> vua duoc gui len he thong (API →
        Kafka → Spark). Danh sach nay chi phuc vu quan sat demo, khong phai nguon du lieu goi y
        chinh thuc.
      </p>

      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100" key={tick}>
        {events.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">
            Chua co su kien nao. Hay sang tab Cua hang va xem/them san pham vao gio.
          </p>
        )}
        {events.map((ev, idx) => (
          <div key={`${ev.session_id}-${ev.timestamp}-${idx}`} className="flex items-center gap-3 px-4 py-3">
            <span
              className={`text-xs font-medium px-2 py-1 rounded-full shrink-0 ${
                EVENT_STYLE[ev.event_type] || "bg-gray-100 text-gray-600"
              }`}
            >
              {ev.event_type}
            </span>
            <span className="text-sm text-gray-700 shrink-0">San pham #{ev.item_id}</span>
            <span className="text-xs text-gray-400 truncate flex-1">
              session {String(ev.session_id).slice(0, 8)}…
            </span>
            <span className="text-xs text-gray-400 shrink-0">{timeAgo(ev.timestamp)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
