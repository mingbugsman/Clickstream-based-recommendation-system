import { useEffect, useRef, useState } from "react";
import axios from "axios";

const PAGE_SIZE = 24;
const API_URL = "http://localhost:5000";

export default function ProductList({ onSelect }) {
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
    <div className="product-list">
      <h2>San pham</h2>
      <ul>
        {items.map((p) => (
          <li key={p.item_id} onClick={() => onSelect(p.item_id)}>
            {p.display_name} — {p.category_display_name}
          </li>
        ))}
      </ul>
      {loading && <p>Dang tai...</p>}
      {!hasMore && items.length > 0 && <p>Da het san pham.</p>}
      <div ref={sentinelRef} style={{ height: 1 }} />
    </div>
  );
}
