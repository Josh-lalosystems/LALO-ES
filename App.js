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
    // Optimistically add the user's message
    setChatHistory(prev => [...prev, { sender: "user", text: chat }] );
    const prompt = chat;
    setChat("");

    // Call backend AI endpoint
    (async () => {
      try {
        const resp = await fetch('/api/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt })
        });
        if (!resp.ok) {
          const text = await resp.text();
          setChatHistory(prev => [...prev, { sender: 'system', text: `Error: ${resp.status} ${text}` }]);
          return;
        }
        const data = await resp.json();

        // Add AI response to chat history
        const aiText = data.response || data.result || '';
        setChatHistory(prev => [...prev, { sender: 'system', text: aiText }]);

        // Optionally update task plan if returned
        if (data.routing_info || data.interpretation) {
          setTaskPlan(data.interpretation || '');
        }

        // Store metadata/action history for side-panel display
        if (data.metadata && data.metadata.fallback_attempts && data.metadata.fallback_attempts.length > 0) {
          // Create a compact summary entry in action history for visibility
          const attempts = data.metadata.fallback_attempts;
          const final = attempts.find(a => a.chosen) || attempts[attempts.length-1];
          const summary = `Fallbacks: ${attempts.length} attempted — final=${final.model} (confidence=${(final.confidence||0).toFixed(2)})`;
          setActionHistory(prev => [...prev, { action: summary, time: new Date().toLocaleString() }]);
        }

      } catch (err) {
        setChatHistory(prev => [...prev, { sender: 'system', text: `Network error: ${err.message}` }]);
      }
    })();
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
          {/* Display a lightweight fallback summary under the chat when present in the latest action history */}
          <div style={{marginTop: 8}}>
            {actionHistory.length > 0 && (
              <div className="fallback-summary">
                <strong>Recent action:</strong> {actionHistory[actionHistory.length-1].action}
              </div>
            )}
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