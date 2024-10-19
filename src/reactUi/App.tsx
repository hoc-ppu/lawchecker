import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import Sidebar from "./Sidebar";

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="page">
      <Sidebar />
      <div className="main-content-top-level">
        <div className="top-title-container">
          <h1>Pup App</h1>
        </div>
      </div>
    </div>
  );
}

export default App;
