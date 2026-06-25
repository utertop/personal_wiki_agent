import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

/** 挂载 React 应用入口，保持首屏直接进入 Chat 工作台。 */
function bootstrap() {
  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

bootstrap();
