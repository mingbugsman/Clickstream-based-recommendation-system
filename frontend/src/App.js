import { useState } from "react";
import ProductList from "./components/ProductList";
import ProductDetail from "./components/ProductDetail";
import RecommendationPanel from "./components/RecommendationPanel";
import ViewHistory from "./components/ViewHistory";
import Dashboard from "./components/Dashboard";
import { getSessionId } from "./tracking";

const TABS = [
  { key: "storefront", label: "Cua hang" },
  { key: "dashboard", label: "Dashboard" },
];

export default function App() {
  const [tab, setTab] = useState("storefront");
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [history, setHistory] = useState([]); // cac item_id da xem trong phien nay, theo thu tu
  const sessionId = getSessionId();

  const handleSelect = (productId) => {
    setSelectedProductId(productId);
    setHistory((prev) => (prev[prev.length - 1] === productId ? prev : [...prev, productId]));
  };

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Recsys Demo</h1>
          <nav className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 text-sm">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-1.5 rounded-md transition ${
                  tab === t.key ? "bg-indigo-600 text-white shadow-sm" : "text-gray-500 hover:text-gray-800"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {tab === "storefront" ? (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8 items-start">
            <ProductList onSelect={handleSelect} selectedId={selectedProductId} />

            {/* panel ben phai dinh lai khi cuon, de xem goi y khong phai keo xuong qua danh sach dai */}
            <div className="lg:sticky lg:top-24 space-y-6">
              <ViewHistory history={history} />

              {selectedProductId ? (
                <ProductDetail productId={selectedProductId} />
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-6 text-sm text-gray-400 text-center">
                  Chon mot san pham ben trai de xem chi tiet.
                </div>
              )}
              <RecommendationPanel sessionId={sessionId} onSelect={handleSelect} hasHistory={history.length > 0} />
            </div>
          </div>
        ) : (
          <Dashboard />
        )}
      </main>
    </div>
  );
}
