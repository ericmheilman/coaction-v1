import React, { useState, useEffect } from 'react';
import './App.css';

function RankingRow({ row }) {
  return (
    <tr>
      {row.map((cell, index) => (
        <td key={index}>{cell}</td>
      ))}
    </tr>
  );
}

function App() {
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    fetch('http://54.85.97.240:5000/leaderboard')
      .then(response => response.json())
      .then(data => setLeaderboard(data));
  }, []);

  return (
    <div className="container-wrap">
      <section id="leaderboard">
        <nav className="ladder-nav">
          <div className="ladder-title">
            <h1>Coaction Testnet Leaderboard</h1>
          </div>
        </nav>
        <table id="rankings" className="leaderboard-results" width="100%">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Name</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((entry, index) => (
              <tr key={index}>
                <td>{index + 1}</td>
                <td>{entry.player}</td>
                <td>{entry.score.toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;
