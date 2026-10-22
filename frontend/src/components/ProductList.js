import { useEffect, useRef, useState } from "react";
import axios from "axios";

const PAGE_SIZE = 24;
const API_URL = "http://localhost:5000";

export default function ProductList({ onSelect }) {
  const [items, setItems] = useState([]);
  const [cursor, setCursor] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const sentinelRef = useRef(null);

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/products`, {
        params: { cursor, limit: PAGE_SIZE },
      });
      setItems((prev) => [...prev, ...res.data.items]);
      setHasMore(res.data.next_cursor !== null);
      setCursor(res.data.next_cursor ?? cursor);
    } catch (err) {
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  // tai trang dau tien
  useEffect(() => {
    loadMore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // infinite scroll: tai them khi sentinel o cuoi danh sach lot vao viewport
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
  }, [cursor, hasMore, loading]);

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
