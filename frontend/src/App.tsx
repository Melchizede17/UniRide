import { useEffect, useState } from "react";
import { checkHealth } from "./services/api";
import "./App.css";

function App() {
  const [status, setStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    checkHealth()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <section id="center">
      <h1>UniRide</h1>
      <p>Backend connectivity: {status}</p>
    </section>
  );
}

export default App;
