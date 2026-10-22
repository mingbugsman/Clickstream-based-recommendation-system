import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { shortName } from "../format";

const PAGE_SIZE = 24;
const API_URL = "http://localhost:5000";

export default function ProductList({ onSelect, selectedId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  // dung ref (khong phai state) de loadMore luon doc duoc gia tri MOI NHAT ngay lap tuc,
  // tranh race condition: IntersectionObserver co the goi loadMore() nhieu lan truoc khi
  // state (cursor/hasMore/loading) kip cap nhat qua re-render, gay tai trung trang dau
  const cursorRef = useRef(0);
  const hasMoreRef = useRef(true);
  const loadingRef = useRef(false);
  const sentinelRef = useRef(null);

  const loadMore = async () => {
    if (loadingRef.current || !hasMoreRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/products`, {
        params: { cursor: cursorRef.current, limit: PAGE_SIZE },
      });
      setItems((prev) => [...prev, ...res.data.items]);
      const nextCursor = res.data.next_cursor;
      hasMoreRef.current = nextCursor !== null;
      setHasMore(hasMoreRef.current);
      if (nextCursor !== null) cursorRef.current = nextCursor;
    } catch (err) {
      hasMoreRef.current = false;
      setHasMore(false);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  };

  // thiet lap IntersectionObserver 1 lan duy nhat; no tu kich hoat tai trang dau
  // ngay khi sentinel nam trong viewport, khong can goi loadMore() rieng luc mount
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-800 mb-4">San pham</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {items.map((p) => (
          <button
            key={p.item_id}
            onClick={() => onSelect(p.item_id)}
            className={`group text-left bg-white rounded-xl border overflow-hidden transition shadow-sm hover:shadow-md hover:-translate-y-0.5 ${
              selectedId === p.item_id ? "ring-2 ring-indigo-500 border-indigo-500" : "border-gray-200"
            }`}
          >
            <div className="aspect-square bg-gray-50 flex items-center justify-center p-4">
              <img
                src={p.image_url}
                alt={p.display_name}
                className="max-h-full max-w-full object-contain"
              />
            </div>
            <div className="p-3">
              <p className="text-xs text-indigo-600 font-medium truncate">
                {p.category_display_name}
              </p>
              <p className="text-sm text-gray-800 font-medium line-clamp-2 mt-0.5 min-h-[2.5rem]">
                {shortName(p.display_name)}
              </p>
              <p className="text-xs text-gray-400 mt-1">{p.price_note}</p>
            </div>
          </button>
        ))}
      </div>

      {loading && (
        <p className="text-center text-sm text-gray-400 py-6">Dang tai them san pham...</p>
      )}
      {!hasMore && items.length > 0 && (
        <p className="text-center text-sm text-gray-400 py-6">Da hien thi toan bo san pham.</p>
      )}
      <div ref={sentinelRef} className="h-1" />
    </div>
  );
}
