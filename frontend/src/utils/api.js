import axios from "axios";

console.log("Connecting to backend at:", "http://localhost:8000");

const api = axios.create({
  baseURL: "http://localhost:8000", // ✅ this works in dev mode
});

export default api;
