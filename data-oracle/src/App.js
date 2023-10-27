import React, { useState, useEffect } from 'react';
import './App.css';

function RankingRow({ row }) {
  return (
    <tr>
      <td>{row.rank}</td>
      <td className="address">{row.address || 'X'}</td>
      <td>{row.protocol || 'X'}</td>
      <td>{row.delegatedStake || 'X'}</td>
      <td>{row.delegationPoints || 'X'}</td>
      <td>{row.referralPoints || '0'}</td>
      <td>{row.totalPoints || 'X'}</td>
    </tr>
  );
}

function App() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [searchValue, setSearchValue] = useState('');

  useEffect(() => {
    fetch('http://54.85.97.240:5000/leaderboard')
      .then(response => response.json())
      .then(data => {
        const formattedLeaderboard = data.map((entry, index) => ({
          rank: index + 1,
          address: entry.player.split(' ')[0],
          protocol: entry.player.split(' ')[1],
          delegatedStake: formatStakedValue(parseFloat(entry.staked_value)), // Convert to a numeric value before formatting
          delegationPoints: entry.score.toLocaleString('en-US', { maximumFractionDigits: 0 }),
          referralPoints: '0',
          totalPoints: entry.score.toLocaleString('en-US', { maximumFractionDigits: 0 }),
        }));
        setLeaderboard(formattedLeaderboard);
      });
  }, []);

  const formatStakedValue = (value) => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    });
    return formatter.format(value);
  };


  const handleSearchChange = (event) => {
    setSearchValue(event.target.value);
  };

  const filteredLeaderboard = leaderboard.filter(entry => {
    const searchTerms = Object.values(entry).map(value => (value ? value.toString().toLowerCase() : ''));
    return searchTerms.some(term => term.includes(searchValue.toLowerCase()));
  });

  return (
    <div className="container-wrap">
      <section id="leaderboard">
        <nav className="ladder-nav">
          <div className="ladder-title">
            <h1>COACTION NETWORK AIRDROP LEADERBOARD</h1>
          </div>
          <div className="ladder-search">
            <input
              type="text"
              id="search-leaderboard"
              className="live-search-box"
              placeholder="Search address..."
              value={searchValue}
              onChange={handleSearchChange}
            />
          </div>
        </nav>

        <table id="rankings" className="leaderboard-results" width="100%">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Address</th>
              <th>Protocol</th>
              <th>Delegated Stake</th>
              <th>Delegation Points</th>
              <th>Referral Points</th>
              <th>Total Points</th>
            </tr>
          </thead>
          <tbody>
            {filteredLeaderboard.map((entry, index) => (
              <RankingRow key={index} row={entry} />
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;
