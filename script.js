// =====================================================
// GLOBAL VARIABLES & TEAMS DATA
// =====================================================
let currentTeam = null;
let currentPlayer = null;
let currentFormat = 't20';
const teamsData = {};

// Performance Optimization: Purana data save rakhne ke liye
const prevState = {
    score: null,
    overs: null,
    last_ball: null,
    pship: null,
    lastWicket: null,
    batman1Score: null,
    batman2Score: null,
    status: null
};

// =====================================================
// DOM ELEMENTS
// =====================================================
const leftCircle = document.getElementById('leftCircle');
const rightCircle = document.getElementById('rightCircle');
const playing11 = document.getElementById('playing11');
const playing11Card = document.getElementById('playing11Card');
const teamTitle = document.getElementById('teamTitle');
const playersGrid = document.getElementById('playersGrid');
const statsOverlay = document.getElementById('statsOverlay');
const statsCard = document.getElementById('statsCard');
const statsClose = document.getElementById('statsClose');
const formatTabs = document.getElementById('formatTabs');

const team1flagbtn = document.getElementById('team1flag');
const team2flagbtn = document.getElementById('team2flag');

const team1NameTxt = document.getElementById('team1nametxt');
const team1Score = document.getElementById('team1score');
const team1Over = document.getElementById('team1over');
const team2NameTxt = document.getElementById('team2nametxt');
const team2Score = document.getElementById('team2score');
const team2Over = document.getElementById('team2over');

const batman1Head = document.getElementById('batman1head');
const batman1Body = document.getElementById('batman1body');
const batman2Head = document.getElementById('batman2head'); 
const batman2Body = document.getElementById('batman2body');
const batman3Head = document.getElementById('batman3head'); 
const batman3Body = document.getElementById('batman3body');

const batman1Name = document.getElementById('batman1name');
const batman1Score = document.getElementById('batman1score');
const batman2Name = document.getElementById('batman2name');
const batman2Score = document.getElementById('batman2score');
const bowlerName = document.getElementById('bowlername');
const bowlerScore = document.getElementById('bowlerscore');
const statusText = document.getElementById('status');
const liveText = document.getElementById('livetext');

const pshipText = document.getElementById('pship');
const lastWicketText = document.getElementById('lastwicket');

const p1_4s = document.querySelector('.part-1 span:nth-of-type(2)');
const p1_6s = document.querySelector('.part-1 span:nth-of-type(4)');
const p1_sr = document.querySelector('.part-1 span:nth-of-type(6)');
const p2_4s = document.querySelector('.part-2 span:nth-of-type(2)');
const p2_6s = document.querySelector('.part-2 span:nth-of-type(4)');
const p2_sr = document.querySelector('.part-2 span:nth-of-type(6)');
const p3_econ = document.querySelector('.part-3 span:nth-of-type(2)');
const commMarquee = document.querySelector('.bottom-bar marquee');

const infoOverlay = document.getElementById('infoOverlay');
const infoClose = document.getElementById('infoClose');
const matchInfoHeader = document.getElementById('matchInfoHeader');
const weatherLocation = document.getElementById('weatherLocation');
const weatherTemp = document.getElementById('weatherTemp');
const weatherCond = document.getElementById('weatherCondition');
const weatherIcon = document.querySelector('.weather-img');
const humidityText = document.getElementById('weatherHumidity');
const rainChanceText = document.getElementById('weatherRain');

const paceWickets = document.getElementById('paceWickets');
const spinWickets = document.getElementById('spinWickets');
const pacePercentText = document.getElementById('pacePercText');
const spinPercentText = document.getElementById('spinPercText');
const paceProgressBar = document.getElementById('paceProgress');

const formatMatchBlocks = document.querySelectorAll('.format-match');
const compGrid = document.querySelector('.comparison-grid');

// =====================================================
// HELPER FUNCTIONS (DOM & Image Error Handle)
// =====================================================
function updateDOM(element, newValue, stateKey, animate = false) {
    if (element && prevState[stateKey] !== newValue) {
        element.textContent = newValue;
        prevState[stateKey] = newValue;
        
        if (animate) {
            element.classList.remove('score-pop');
            void element.offsetWidth; // Reflow trick
            element.classList.add('score-pop');
        }
    }
}

function safeImageSrc(element, src, fallback = 'https://cricketvectors.akamaized.net/players/org/MP.png') {
    if (element && element.getAttribute('src') !== src) {
        element.src = src || fallback;
        element.onerror = () => { element.src = fallback; };
    }
}

// =====================================================
// FETCH AND LOAD DATA
// =====================================================
async function loadMatchData() {
  try {
    const response = await fetch('data.json?t=' + new Date().getTime());
    if (!response.ok) throw new Error('Failed to load data.json');
    const data = await response.json();

    // 1. Teams & Names
    let h2h = data.head_to_head;
    if (h2h && data.live_score) {
        let isTeam1Batting = (data.live_score.team === h2h.team1.name);
        safeImageSrc(team1flagbtn, h2h.team1.flag_url, '');
        safeImageSrc(team2flagbtn, h2h.team2.flag_url, '');
        if (team1NameTxt) team1NameTxt.textContent = data.live_score.team;
        if (team2NameTxt) team2NameTxt.textContent = isTeam1Batting ? h2h.team2.name : h2h.team1.name;
    }

    // 2. Scoreboard & Live Text Logic (50px / 80px)
    if (data.live_score) {
      updateDOM(team1Score, data.live_score.score, 'score', true);
      updateDOM(team1Over, data.live_score.overs, 'overs', false);
      
      if (data.live_score.last_ball !== undefined && liveText) {
          if (prevState.last_ball !== data.live_score.last_ball) {
              liveText.textContent = data.live_score.last_ball;
              prevState.last_ball = data.live_score.last_ball;
              
              let currentText = data.live_score.last_ball.toString().trim().toLowerCase();
              if (currentText === "won") {
                  liveText.style.fontSize = "50px";
              } else {
                  liveText.style.fontSize = "80px";
              }
          }
      }
      
      updateDOM(statusText, data.live_score.status, 'status', false);
    }
    
    if (team2Score) team2Score.textContent = "BOWLING";
    if (team2Over && data.bowler) team2Over.textContent = data.bowler.overs;

    updateDOM(pshipText, data.partnership, 'pship', false);
    updateDOM(lastWicketText, data.last_wicket, 'lastWicket', false);

    // 3. Batter 1
    if (data.batsmen && data.batsmen.length > 0) {
      safeImageSrc(batman1Head, data.batsmen[0].head_image_url);
      safeImageSrc(batman1Body, data.batsmen[0].jersey_image_url, 'https://cricketvectors.akamaized.net/jersey/limited/org/52.png');
      if (batman1Name) batman1Name.textContent = data.batsmen[0].name;
      
      let p1Score = `${data.batsmen[0].runs}(${data.batsmen[0].balls})`;
      updateDOM(batman1Score, p1Score, 'batman1Score', true);
      
      if (p1_4s) p1_4s.textContent = data.batsmen[0]["4s"];
      if (p1_6s) p1_6s.textContent = data.batsmen[0]["6s"];
      if (p1_sr) p1_sr.textContent = data.batsmen[0]["sr"];
    }

    // 4. Batter 2
    if (data.batsmen && data.batsmen.length > 1) {
      safeImageSrc(batman2Head, data.batsmen[1].head_image_url);
      safeImageSrc(batman2Body, data.batsmen[1].jersey_image_url, 'https://cricketvectors.akamaized.net/jersey/limited/org/52.png');
      if (batman2Name) batman2Name.textContent = data.batsmen[1].name;
      
      let p2Score = `${data.batsmen[1].runs}(${data.batsmen[1].balls})`;
      updateDOM(batman2Score, p2Score, 'batman2Score', true);

      if (p2_4s) p2_4s.textContent = data.batsmen[1]["4s"];
      if (p2_6s) p2_6s.textContent = data.batsmen[1]["6s"];
      if (p2_sr) p2_sr.textContent = data.batsmen[1]["sr"];
    }

    // 5. Bowler
    if (data.bowler) {
      safeImageSrc(batman3Head, data.bowler.head_image_url);
      safeImageSrc(batman3Body, data.bowler.jersey_image_url, 'https://cricketvectors.akamaized.net/jersey/limited/org/52.png');
      if (bowlerName) bowlerName.textContent = data.bowler.name;
      if (bowlerScore) bowlerScore.textContent = `${data.bowler.figures}(${data.bowler.overs})`;
      if (p3_econ) p3_econ.textContent = data.bowler["econ"];
    }

    // 6. Commentary Marquee
    if (data.commentary && data.commentary.length > 0 && commMarquee) {
      const commString = data.commentary.map(c => `OVER ${c.over} RUN ${c.runs} ${c.description}`).join('  |  ');
      if(commMarquee.textContent !== commString) commMarquee.textContent = commString;
    }

    // 7. Info Overlay (Weather & Venue)
    if(matchInfoHeader && data.match_info) {
        matchInfoHeader.innerHTML = `${data.match_info}<br><span style="font-size: 20px; color:#aaa; font-weight: 500;">${data.toss}</span>`;
    }

    if (data.weather) {
      if (weatherLocation) weatherLocation.textContent = data.weather.location;
      if (weatherTemp) weatherTemp.textContent = data.weather.temperature;
      if (weatherCond) weatherCond.textContent = data.weather.condition;
      if (humidityText) humidityText.textContent = data.weather.humidity + " (Humidity)";
      if (rainChanceText) rainChanceText.textContent = data.weather.rain_chance;
      
      if (weatherIcon) {
        const cnd = data.weather.condition.toLowerCase();
        if (cnd.includes('sun') || cnd.includes('clear')) weatherIcon.textContent = '☀️';
        else if (cnd.includes('rain') || cnd.includes('drizz')) weatherIcon.textContent = '🌧️';
        else if (cnd.includes('storm')) weatherIcon.textContent = '⛈️';
        else weatherIcon.textContent = '⛅';
      }
    }

    if (data.venue_stats) {
      if (paceWickets) paceWickets.textContent = data.venue_stats.pace_wickets;
      if (spinWickets) spinWickets.textContent = data.venue_stats.spin_wickets;
      if (pacePercentText) pacePercentText.textContent = data.venue_stats.pace_percentage;
      if (spinPercentText) spinPercentText.textContent = data.venue_stats.spin_percentage;
      if (paceProgressBar) paceProgressBar.style.setProperty('--progress', data.venue_stats.pace_percentage);
    }

    // 8. Team Form & Comparison
    if (data.team_form && formatMatchBlocks.length > 0) {
      const formKeys = Object.keys(data.team_form);
      formKeys.forEach((teamName, index) => {
        if (formatMatchBlocks[index]) {
          const nameElement = formatMatchBlocks[index].querySelector('.form-team-name');
          const imgElement = formatMatchBlocks[index].querySelector('.form-team-img');
          if (nameElement) nameElement.textContent = teamName;
          if (imgElement) imgElement.src = data.team_form[teamName].flag_url;

          const formContainer = formatMatchBlocks[index].querySelector('.d-flex.justify-content-center');
          if (formContainer) {
            formContainer.innerHTML = '';
            data.team_form[teamName].form.forEach(result => {
              const matchDiv = document.createElement('div');
              if (result === 'W') matchDiv.className = 'win match';
              else if (result === 'L') matchDiv.className = 'loss match';
              else matchDiv.className = 'draw match';
              matchDiv.innerHTML = `<span>${result}</span>`;
              formContainer.appendChild(matchDiv);
            });
          }
        }
      });
    }

    if (compGrid && h2h && data.team_comparison) {
        let gridHtml = `
            <div class="comp-row header">
              <div class="comp-team"><img src="${h2h.team1.flag_url}" width="36"> ${h2h.team1.name}</div>
              <div class="comp-metric">Head to Head</div>
              <div class="comp-team">${h2h.team2.name} <img src="${h2h.team2.flag_url}" width="36"></div>
            </div>
            <div class="comp-row">
              <div class="comp-val">${h2h.team1.wins}</div>
              <div class="comp-metric-name">Wins</div>
              <div class="comp-val">${h2h.team2.wins}</div>
            </div>
            <div class="comp-row header mt-15">
              <div class="comp-team"></div>
              <div class="comp-metric">Team Comparison</div>
              <div class="comp-team"></div>
            </div>
        `;
        data.team_comparison.forEach(comp => {
            gridHtml += `
            <div class="comp-row">
                <div class="comp-val">${comp.team1_value}</div>
                <div class="comp-metric-name">${comp.metric}</div>
                <div class="comp-val">${comp.team2_value}</div>
            </div>`;
        });
        compGrid.innerHTML = gridHtml;
    }

    // 9. Generate Playing XI Data
    if (data.playing_xi) {
      const teamKeys = Object.keys(data.playing_xi);
      
      teamKeys.forEach((key, index) => {
        const playingXiArray = data.playing_xi[key] || [];
        let teamFlag = "";
        if(h2h && h2h.team1.name === key) teamFlag = h2h.team1.flag_url;
        if(h2h && h2h.team2.name === key) teamFlag = h2h.team2.flag_url;
        
        teamsData[key] = {
          teamName: key + " PLAYING XI",
          teamLogo: teamFlag || "https://cricketvectors.akamaized.net/Teams/R.png", 
          themeClass: index === 0 ? "csk" : "lumbini", 
          players: playingXiArray.map(player => {
            const isCap = player.name.includes("(C)");
            const cleanName = player.name.replace(" (C)", "").replace(" (WK)", "");
            
            const playerStats = {
              t20: { batting: { matches: "-", runs: "-", highScore: "-", average: "-", strikeRate: "-", fifties: "-", hundreds: "-" }, bowling: { wickets: "-", economy: "-", bestBowling: "-", average: "-", overs: "-" } },
              odi: { batting: { matches: "-", runs: "-", highScore: "-", average: "-", strikeRate: "-", fifties: "-", hundreds: "-" }, bowling: { wickets: "-", economy: "-", bestBowling: "-", average: "-", overs: "-" } },
              test: { batting: { matches: "-", runs: "-", highScore: "-", average: "-", strikeRate: "-", fifties: "-", hundreds: "-" }, bowling: { wickets: "-", economy: "-", bestBowling: "-", average: "-", overs: "-" } }
            };

            if (player.batting_stats && Array.isArray(player.batting_stats)) {
              player.batting_stats.forEach(stat => {
                let formatKey = null;
                if (stat.Format === "T20I" || stat.Format === "T20" || stat.Format === "T20-Blast" || stat.Format === "CPL" || stat.Format === "IPL" || stat.Format === "ABU DHABI") {
                    formatKey = "t20";
                } else if (stat.Format === "ODI") {
                    formatKey = "odi";
                } else if (stat.Format === "Test") {
                    formatKey = "test";
                }

                if (formatKey) {
                  if (playerStats[formatKey].batting.matches === "-" || stat.Format === "T20I" || stat.Format === "Test" || stat.Format === "ODI") {
                      playerStats[formatKey].batting = {
                        matches: stat.Mat || "-",
                        runs: stat.R || "-",
                        highScore: stat.HS || "-",
                        average: stat.Avg || "-",
                        strikeRate: stat.SR || "-",
                        fifties: stat["50s"] || "-",
                        hundreds: stat["100s"] || "-"
                      };
                  }
                }
              });
            }

            return {
              name: cleanName.toUpperCase(),
              role: player.role ? player.role.toUpperCase() : "PLAYER",
              country: key,
              head: player.head_image_url || 'https://cricketvectors.akamaized.net/players/org/MP.png',
              body: player.jersey_image_url || 'https://cricketvectors.akamaized.net/jersey/limited/org/52.png',
              isCaptain: isCap,
              stats: playerStats
            };
          })
        };
      });

      // Saving Keys Globally for Click Listeners
      window.team1Key = teamKeys[0];
      window.team2Key = teamKeys[1] || teamKeys[0];
    }

  } catch (error) {
    console.error("Error loading JSON:", error);
  }
}

// =====================================================
// PLAYING 11 & STATS RENDER FUNCTIONS
// =====================================================
function renderTeam(teamKey) {
  currentTeam = teamsData[teamKey];
  if (!currentTeam) return;

  teamTitle.textContent = `${currentTeam.teamName}`;
  playing11Card.className = `playing11-card ${currentTeam.themeClass}`;
  playersGrid.innerHTML = '';
  
  currentTeam.players.forEach((player, index) => {
    const playerCard = document.createElement('div');
    playerCard.className = `player-card${player.isCaptain ? ' captain' : ''}`;
    playerCard.dataset.playerIndex = index;
    
    playerCard.innerHTML = `
      <div class="player-image">
        <img src="${player.head}" class="player-head" alt="Player" onerror="this.src='https://cricketvectors.akamaized.net/players/org/MP.png'">
        <img src="${currentTeam.teamLogo}" class="team-logo" alt="Team">
        <img src="${player.body}" class="player-body" alt="Jersey" onerror="this.src='https://cricketvectors.akamaized.net/jersey/limited/org/52.png'">
      </div>
      <div class="player-info">
        <div class="player-role">${player.role}</div>
        <div class="player-name">${player.name}</div>
      </div>
    `;
    
    playerCard.addEventListener('click', function(e) {
      e.stopPropagation();
      showPlayerStats(parseInt(this.dataset.playerIndex));
    });
    
    playersGrid.appendChild(playerCard);
  });
}

function showPlayerStats(playerIndex) {
  currentPlayer = currentTeam.players[playerIndex];
  
  statsCard.className = `stats-card ${currentTeam.themeClass}`;
  
  document.getElementById('statsTeamLogo').src = currentTeam.teamLogo;
  document.getElementById('statsPlayerHead').src = currentPlayer.head;
  document.getElementById('statsPlayerBody').src = currentPlayer.body;
  document.getElementById('statsNameBox').textContent = currentPlayer.name;
  document.getElementById('statsRoleBox').textContent = currentPlayer.role;
  document.getElementById('statsCountryBox').textContent = currentPlayer.country;
  
  document.getElementById('statsPlayerName').textContent = currentPlayer.name;
  document.getElementById('statsPlayerRole').textContent = currentPlayer.role;
  
  const captainBadge = document.getElementById('statsCaptainBadge');
  if (currentPlayer.isCaptain) {
    captainBadge.classList.add('show');
  } else {
    captainBadge.classList.remove('show');
  }
  
  currentFormat = 't20';
  document.querySelectorAll('.format-tab').forEach(tab => {
    tab.classList.remove('active');
    if (tab.dataset.format === 't20') tab.classList.add('active');
  });
  
  updateStats();
  statsOverlay.classList.add('active');
}

function updateStats() {
  if (!currentPlayer) return;
  const stats = currentPlayer.stats[currentFormat];
  const batting = stats.batting;
  const bowling = stats.bowling;
  
  document.getElementById('battingStats').innerHTML = `
    <div class="stat-box"><div class="stat-value">${batting.matches}</div><div class="stat-label">Matches</div></div>
    <div class="stat-box"><div class="stat-value">${batting.runs}</div><div class="stat-label">Runs</div></div>
    <div class="stat-box"><div class="stat-value">${batting.highScore}</div><div class="stat-label">High Score</div></div>
    <div class="stat-box"><div class="stat-value">${batting.average}</div><div class="stat-label">Average</div></div>
    <div class="stat-box"><div class="stat-value">${batting.strikeRate}</div><div class="stat-label">Strike Rate</div></div>
    <div class="stat-box"><div class="stat-value">${batting.fifties}</div><div class="stat-label">50s</div></div>
    <div class="stat-box"><div class="stat-value">${batting.hundreds}</div><div class="stat-label">100s</div></div>
  `;
  
  document.getElementById('bowlingStats').innerHTML = `
    <div class="stat-box"><div class="stat-value">${bowling.wickets}</div><div class="stat-label">Wickets</div></div>
    <div class="stat-box"><div class="stat-value">${bowling.economy}</div><div class="stat-label">Economy</div></div>
    <div class="stat-box"><div class="stat-value">${bowling.bestBowling}</div><div class="stat-label">Best</div></div>
    <div class="stat-box"><div class="stat-value">${bowling.average}</div><div class="stat-label">Average</div></div>
    <div class="stat-box"><div class="stat-value">${bowling.overs}</div><div class="stat-label">Overs</div></div>
  `;
}

// =====================================================
// EVENT LISTENERS
// =====================================================
leftCircle.addEventListener('click', () => { if(window.team1Key) { renderTeam(window.team1Key); playing11.classList.add('active'); }});
team1flagbtn.addEventListener('click', () => { if(window.team1Key) { renderTeam(window.team1Key); playing11.classList.add('active'); }});
rightCircle.addEventListener('click', () => { if(window.team2Key) { renderTeam(window.team2Key); playing11.classList.add('active'); }});
team2flagbtn.addEventListener('click', () => { if(window.team2Key) { renderTeam(window.team2Key); playing11.classList.add('active'); }});

playing11.addEventListener('click', (e) => {
  if (e.target === playing11) playing11.classList.remove('active');
});

statsClose.addEventListener('click', () => statsOverlay.classList.remove('active'));

statsOverlay.addEventListener('click', (e) => {
  if (e.target === statsOverlay) statsOverlay.classList.remove('active');
});

formatTabs.addEventListener('click', (e) => {
  if (e.target.classList.contains('format-tab')) {
    document.querySelectorAll('.format-tab').forEach(tab => tab.classList.remove('active'));
    e.target.classList.add('active');
    currentFormat = e.target.dataset.format;
    updateStats();
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    statsOverlay.classList.remove('active');
    playing11.classList.remove('active');
    if(infoOverlay) infoOverlay.classList.remove('active');
  }
});

// Info overlay toggles (Weather/Form)
if(liveText) {
  liveText.addEventListener('click', () => {
    infoOverlay.classList.add('active');
  });
}

if(infoClose) {
  infoClose.addEventListener('click', () => {
    infoOverlay.classList.remove('active');
  });
}

if(infoOverlay) {
  infoOverlay.addEventListener('click', (e) => {
    if (e.target === infoOverlay) {
      infoOverlay.classList.remove('active');
    }
  });
}

// =====================================================
// INITIALIZATION
// =====================================================
loadMatchData();
setInterval(loadMatchData, 1000);