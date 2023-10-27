import React, { useEffect, useState } from 'react';

function Leaderboard() {
	  const [topScores, setTopScores] = useState([]);

	  useEffect(() => {
		      fetch('/leaderboard')
		        .then(response => response.text())
		        .then(data => {
				        const parser = new DOMParser();
				        const leaderboard = parser.parseFromString(data, 'text/html');
				        const rows = leaderboard.getElementsByTagName('tr');
				        const scores = [];
				        for (let i = 1; i < rows.length; i++) {
						          const player = rows[i].getElementsByTagName('td')[0].innerText;
						          const score = rows[i].getElementsByTagName('td')[1].innerText;
						          scores.push({ player, score });
						        }
				        setTopScores(scores);
				      })
		        .catch(error => console.error(error));
		    }, []);

	  return (
		      <div>
		        <h1>Leaderboard</h1>
		        <table>
		          <thead>
		            <tr>
		              <th>Player</th>
		              <th>Score</th>
		            </tr>
		          </thead>
		          <tbody>
		            {topScores.map((score, index) => (
				                <tr key={index}>
				                  <td>{score.player}</td>
				                  <td>{score.score}</td>
				                </tr>
				              ))}
		          </tbody>
		        </table>
		      </div>
		    );
}

export default Leaderboard;

