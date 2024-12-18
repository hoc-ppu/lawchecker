import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./components/App.tsx";
// import "./js/bootstrap.bundle.min.js";
import * as bootstrap from 'bootstrap'
import "./js/ui.js";
import "./css/bootstrap.min.css";
import "./css/style.css";

// Function to wait for an event with a timeout
const waitForEvent = (eventName: string, timeout = 1000) => {
  const positiveMsg = `${eventName} event fired within ${timeout}ms`;
  const negativeMsg = `${eventName} event did not fire within ${timeout}ms`;

  return new Promise((resolve) => {
    let eventFired = false;

    const timer = setTimeout(() => {
      if (!eventFired) {
        console.warn(`Timeout: ${negativeMsg}`);
        resolve(negativeMsg);
      }
    }, timeout);

    const onEvent = () => {
      eventFired = true;
      clearTimeout(timer);
      resolve(positiveMsg);
    };

    window.addEventListener(eventName, onEvent, { once: true });
  });
};

// Was getting strange bugs where sometimes the pywebviewready event was firing
// before react got going and sometimes a while after. So I think it might be
// safer to just wait for the eventfor a few seconds. Render the app weather or
// not if fired though as we still want to preview it in the browser.
waitForEvent("pywebviewready")
  .then((msg) => {
    console.log(msg);
    createRoot(document.getElementById("root")!).render(
      <StrictMode>
        <App />
      </StrictMode>
    );
  })
  .catch((error) => {
    console.error("An unexpected error occurred:");
    console.error(error.message);
    // Could render a fallback UI...
  });
