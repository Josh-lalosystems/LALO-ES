/*
 * Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
 *
 * PROPRIETARY AND CONFIDENTIAL
 *
 * This file is part of LALO AI Platform and is protected by copyright law.
 * Unauthorized copying, modification, distribution, or use of this software,
 * via any medium, is strictly prohibited without the express written permission
 * of LALO AI SYSTEMS, LLC.
 */

import React, { useState } from "react";
import "./App.css";

function App() {
  const [chat, setChat] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [taskPlan, setTaskPlan] = useState("");
  const [actionHistory, setActionHistory] = useState([]);
  const [connectedSources, setConnectedSources] = useState([
    { name: "OneDrive", status: "Connected" },
    { name: "SharePoint", status: "Not Connected" },
  ]);

  const handleSend = () => {
  if (chat.trim() === "") return; // Ensure chat is not empty
    setChatHistory([...chatHistory, { sender: "user", text: chat }]);
    setChat("");
    // TODO: Send chat to backend and update taskPlan, etc.
  };

  const handleApprove = () => {
    setActionHistory([...actionHistory, { action: taskPlan, time: new Date().toLocaleString() }]);
    setTaskPlan("");
    // TODO: Notify backend of approval
  };

  return (
    <div className="dashboard">
      <div className="main-panel">
        <div className="chat-window">
          <div className="chat-history">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={msg.sender === "user" ? "chat-user" : "chat-system"}>
                {msg.text}
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input
              value={chat}
              onChange={e => setChat(e.target.value)}
              placeholder="Type your message..."
              onKeyDown={e => e.key === "Enter" && handleSend()}
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
        <div className="task-panel">
          <h3>Task Plan & Approval</h3>
          <div className="task-content">{taskPlan || "No task plan yet."}</div>
          {taskPlan && <button onClick={handleApprove}>Approve Plan</button>}
        </div>
      </div>
      <div className="side-panel">
        <div className="history-panel">
          <h4>Action History</h4>
          <ul>
            {actionHistory.map((item, idx) => (
              <li key={idx}>{item.action} <span className="timestamp">{item.time}</span></li>
            ))}
          </ul>
        </div>
        <div className="sources-panel">
          <h4>Connected Sources</h4>
          <ul>
            {connectedSources.map((src, idx) => (
              <li key={idx}>
                {src.name}: <span className={src.status === "Connected" ? "connected" : "not-connected"}>{src.status}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;