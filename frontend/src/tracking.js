import { v4 as uuidv4 } from "uuid";
import axios from "axios";

function getSessionId() {
  let sid = localStorage.getItem("session_id");
  if (!sid) {
    sid = uuidv4();
    localStorage.setItem("session_id", sid);
  }
  return sid;
}

export function trackEvent(itemId, eventType) {
  const payload = {
    session_id: getSessionId(),
    item_id: itemId,
    event_type: eventType, // "view" | "addtocart"
    timestamp: Date.now(),
  };
  axios.post("http://localhost:5000/api/track", payload).catch(() => {});
}

export { getSessionId };
