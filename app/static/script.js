// IPL Match Predictor JavaScript

// Initialize Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Setup modals
    const venueModal = new bootstrap.Modal(document.getElementById('venue-analyzer-modal'));
    const playerModal = new bootstrap.Modal(document.getElementById('player-analyzer-modal'));
    const teamModal = new bootstrap.Modal(document.getElementById('team-analyzer-modal'));
    
    // Add event listeners for analyzer buttons
    const venueAnalyzerBtn = document.getElementById('venue-analyzer-btn');
    if (venueAnalyzerBtn) {
        venueAnalyzerBtn.addEventListener('click', function() {
            // Redirect to venue analyzer page
            window.location.href = '/venueanalyzer/';
        });
    }
    const playerAnalyzerBtn = document.getElementById('player-analyzer-btn');
    if (playerAnalyzerBtn) {
        playerAnalyzerBtn.addEventListener('click', function() {
            // Redirect to player analyzer page
            window.location.href = '/playeranalyzer/';
        });
    }
    const teamAnalyzerBtn = document.getElementById('team-analyzer-btn');
    if (teamAnalyzerBtn) {
        teamAnalyzerBtn.addEventListener('click', function() {
            // Redirect to team analyzer page
            window.location.href = '/teamanalyzer/';
        });
    }
    document.getElementById('player-analyzer-btn').addEventListener('click', function() {
        playerModal.show();
    });
    
    document.getElementById('team-analyzer-btn').addEventListener('click', function() {
        teamModal.show();
    });
    
    // Add event listeners for team selection
    document.getElementById('team1').addEventListener('change', function() {
        fetchPlayers(this.value, 'team1-players', 'team1_players');
        updateHeadToHead();
    });
    
    document.getElementById('team2').addEventListener('change', function() {
        fetchPlayers(this.value, 'team2-players', 'team2_players');
        updateHeadToHead();
    });
    
    // Add event listener for prediction form submission
    document.getElementById('prediction-form').addEventListener('submit', submitPrediction);
    
    // Add animations for UI elements
    animateElements();
});

// Fetch players for a team
async function fetchPlayers(teamName, containerId, fieldName) {
    if (!teamName) return;
    
    const container = document.getElementById(containerId);
    container.innerHTML = '<div class="text-center p-3"><div class="loader" style="width: 30px; height: 30px;"></div><p>Loading players...</p></div>';
    
    try {
        const response = await fetch(`/get_players/${encodeURIComponent(teamName)}`);
        const data = await response.json();
        
        container.innerHTML = '';
        
        if (data.players.length === 0) {
            container.innerHTML = '<p class="text-danger">No players found</p>';
            return;
        }
        
        // Group players by role
        const playersByRole = {};
        data.players.forEach(player => {
            const role = player.role.toLowerCase();
            if (!playersByRole[role]) {
                playersByRole[role] = [];
            }
            playersByRole[role].push(player);
        });
        
        // Create checkboxes grouped by role
        for (const role in playersByRole) {
            const roleDiv = document.createElement('div');
            roleDiv.className = 'mb-3';
            
            const roleTitle = document.createElement('h6');
            roleTitle.className = 'mt-2 mb-2';
            roleTitle.textContent = `${role[0].toUpperCase() + role.slice(1)}:`;
            roleDiv.appendChild(roleTitle);
            
            const rolePlayersDiv = document.createElement('div');
            rolePlayersDiv.className = 'role-players';
            
            playersByRole[role].forEach(player => {
                const div = document.createElement('div');
                div.className = 'form-check';
                
                const input = document.createElement('input');
                input.className = 'form-check-input';
                input.type = 'checkbox';
                input.name = fieldName;
                input.value = player.name;
                input.id = `${fieldName}_${player.name.replace(/\s+/g, '_')}`;
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.setAttribute('for', `${fieldName}_${player.name.replace(/\s+/g, '_')}`);
                label.textContent = player.name;
                
                div.appendChild(input);
                div.appendChild(label);
                rolePlayersDiv.appendChild(div);
            });
            
            roleDiv.appendChild(rolePlayersDiv);
            container.appendChild(roleDiv);
        }
    } catch (error) {
        console.error("Error fetching players:", error);
        container.innerHTML = '<p class="text-danger">Error loading players. Please try again.</p>';
    }
}

// Submit prediction request
async function submitPrediction(e) {
    e.preventDefault();
    
    // Validate team selection
    const team1 = document.getElementById('team1').value;
    const team2 = document.getElementById('team2').value;
    
    if (team1 === team2) {
        alert('Please select different teams');
        return;
    }
    
    // Validate player selection (at least 11 players per team)
    const team1Players = document.querySelectorAll('input[name="team1_players"]:checked');
    const team2Players = document.querySelectorAll('input[name="team2_players"]:checked');
    
    if (team1Players.length < 11) {
        alert('Please select at least 11 players for Team 1');
        return;
    }
    
    if (team2Players.length < 11) {
        alert('Please select at least 11 players for Team 2');
        return;
    }
    
    // Get venue
    const venue = document.getElementById('venue').value;
    
    if (!venue) {
        alert('Please select a venue');
        return;
    }
    
    // Show loading indicator with animation
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    // Scroll to loading indicator
    document.getElementById('loading').scrollIntoView({ behavior: 'smooth' });
    
    // Create form data
    const formData = new FormData();
    formData.append('team1', team1);
    formData.append('team2', team2);
    
    // Add selected players
    team1Players.forEach(player => {
        formData.append('team1_players', player.value);
    });
    
    team2Players.forEach(player => {
        formData.append('team2_players', player.value);
    });
    
    formData.append('venue', venue);
    
    try {
        // Send prediction request
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log("Prediction result:", result);
        
        // Verify result structure
        if (!result.prediction || !result.prediction.winner) {
            console.error("Invalid response structure:", result);
            throw new Error("Invalid prediction response format");
        }
        
        displayResults(result);
    } catch (error) {
        console.error("Prediction error:", error);
        alert('Error making prediction: ' + error.message);
        document.getElementById('loading').style.display = 'none';
    }
}
// //load venue data
// // Update your loadVenueAnalyzer function in script.js
// async function loadVenueAnalyzer() {
//     const venueContent = document.getElementById('venue-analysis-content');
//     if (!venueContent) {
//         console.error('Venue analysis content element not found');
//         return;
//     }
    
//     venueContent.innerHTML = '<div class="text-center p-3"><div class="loader" style="width: 30px; height: 30px;"></div><p>Loading venue data...</p></div>';
    
//     try {
//         // Get list of venues from your venue router
//         const response = await fetch('/api/venues');
//         const data = await response.json();
        
//         // Create venue selection UI
//         let html = `
//             <div class="mb-4">
//                 <label for="venue-selector" class="form-label">Select a venue to analyze:</label>
//                 <select id="venue-selector" class="form-select">
//                     <option value="" selected disabled>-- Select Venue --</option>
//         `;
        
//         data.venues.forEach(venue => {
//             html += `<option value="${venue}">${venue}</option>`;
//         });
        
//         html += `
//                 </select>
//             </div>
//             <div id="venue-details" class="mt-4">
//                 <div class="alert alert-info">Select a venue to see detailed statistics</div>
//             </div>
//         `;
        
//         venueContent.innerHTML = html;
        
//         // Add event listener for venue selection
//         document.getElementById('venue-selector').addEventListener('change', function() {
//             fetchVenueDetails(this.value);
//         });
        
//     } catch (error) {
//         console.error("Error loading venues:", error);
//         venueContent.innerHTML = '<div class="alert alert-danger">Error loading venue data. Please try again.</div>';
//     }
// }

// // fetch details for a specific venue
// async function fetchVenueDetails(venueId) {
//     const venueDetails = document.getElementById('venue-details');
//     venueDetails.innerHTML = '<div class="text-center p-3"><div class="loader" style="width: 30px; height: 30px;"></div><p>Loading venue details...</p></div>';
    
//     try {
//         const response = await fetch(`/venues/${venueId}`);
//         const data = await response.json();
        
//         // Create HTML for venue statistics
//         let html = `
//             <div class="card">
//                 <div class="card-header">
//                     <h5>${data.name}</h5>
//                 </div>
//                 <div class="card-body">
//                     <div class="row">
//                         <div class="col-md-6">
//                             <h6>Venue Statistics</h6>
//                             <ul class="list-group">
//                                 <li class="list-group-item d-flex justify-content-between align-items-center">
//                                     Total Matches
//                                     <span class="badge bg-primary rounded-pill">${data.total_matches || 0}</span>
//                                 </li>
//                                 <li class="list-group-item d-flex justify-content-between align-items-center">
//                                     Average First Innings Score
//                                     <span class="badge bg-primary rounded-pill">${data.avg_first_innings_score || 0}</span>
//                                 </li>
//                                 <li class="list-group-item d-flex justify-content-between align-items-center">
//                                     Average Second Innings Score
//                                     <span class="badge bg-primary rounded-pill">${data.avg_second_innings_score || 0}</span>
//                                 </li>
//                             </ul>
//                         </div>
//                         <div class="col-md-6">
//                             <h6>Winning Pattern</h6>
//                             <div class="pie-chart-placeholder mb-3" style="height: 150px; background-color: #f8f9fa; border-radius: 5px;">
//                                 <!-- You can replace this with an actual chart -->
//                                 <div class="p-3">
//                                     <p>Batting First Wins: ${data.batting_first_wins || 0}</p>
//                                     <p>Batting Second Wins: ${data.batting_second_wins || 0}</p>
//                                 </div>
//                             </div>
//                         </div>
//                     </div>
                    
//                     <h6 class="mt-3">Team Performance at this Venue</h6>
//                     <table class="table table-striped">
//                         <thead>
//                             <tr>
//                                 <th>Team</th>
//                                 <th>Matches</th>
//                                 <th>Wins</th>
//                                 <th>Win %</th>
//                             </tr>
//                         </thead>
//                         <tbody>
//         `;
        
//         // Add team stats rows
//         if (data.team_stats && Array.isArray(data.team_stats)) {
//             data.team_stats.forEach(team => {
//                 const winPercentage = team.matches > 0 ? 
//                     ((team.wins / team.matches) * 100).toFixed(1) : 0;
                
//                 html += `
//                     <tr>
//                         <td>${team.name}</td>
//                         <td>${team.matches}</td>
//                         <td>${team.wins}</td>
//                         <td>${winPercentage}%</td>
//                     </tr>
//                 `;
//             });
//         }
        
//         html += `
//                         </tbody>
//                     </table>
//                 </div>
//             </div>
//         `;
        
//         venueDetails.innerHTML = html;
//     } catch (error) {
//         console.error("Error fetching venue details:", error);
//         venueDetails.innerHTML = '<div class="alert alert-danger">Error loading venue details. Please try again.</div>';
//     }
// }

// Update head-to-head statistics
async function updateHeadToHead() {
    const team1 = document.getElementById('team1').value;
    const team2 = document.getElementById('team2').value;
    
    if (!team1 || !team2 || team1 === team2) return;
    
    const container = document.getElementById('head2head-container');
    container.innerHTML = '<div class="text-center p-3"><div class="loader" style="width: 30px; height: 30px;"></div><p>Loading head-to-head stats...</p></div>';
    
    try {
        const response = await fetch(`/get_head_to_head/${encodeURIComponent(team1)}/${encodeURIComponent(team2)}`);
        const data = await response.json();
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">Head-to-Head Stats</div>
                <div class="card-body">
                    <div class="head-to-head">
                        <div class="team-score">${data.team_a_wins}</div>
                        <div class="vs-badge">vs</div>
                        <div class="team-score">${data.team_b_wins}</div>
                    </div>
                    <p class="text-center mb-0">Total matches: ${data.total_matches}</p>
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-danger">Error loading head-to-head stats</div>';
    }
}

// Display prediction results
function displayResults(data) {
    // Hide loading indicator and show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    
    try {
        // Make sure we have the required data
        if (!data.prediction || !data.prediction.winner || !data.team1 || !data.team2) {
            throw new Error("Missing required data in prediction response");
        }
        
        // Update winner with animation
        const winnerElement = document.getElementById('winner-name');
        winnerElement.textContent = data.prediction.winner;
        winnerElement.style.opacity = 0;
        setTimeout(() => {
            winnerElement.style.transition = "opacity 1s ease";
            winnerElement.style.opacity = 1;
        }, 300);
        
        // Set the winner's probability
        const winnerProb = data.prediction.winner === data.team1 ? 
            data.prediction.team1_probability : 
            data.prediction.team2_probability;
        
        document.getElementById('winner-tagline').textContent = 
            `has a ${winnerProb}% chance of winning this match`;
        
        // Update probability bar with animation
        const team1ProbFill = document.getElementById('team1-prob-fill');
        const team2ProbFill = document.getElementById('team2-prob-fill');
        const team1ProbLabel = document.getElementById('team1-prob-label');
        const team2ProbLabel = document.getElementById('team2-prob-label');
        
        // Set probability labels
        team1ProbLabel.textContent = `${data.team1}: ${data.prediction.team1_probability}%`;
        team2ProbLabel.textContent = `${data.team2}: ${data.prediction.team2_probability}%`;
        
        // Animate probability bars
        setTimeout(() => {
            team1ProbFill.style.width = `${data.prediction.team1_probability}%`;
            team2ProbFill.style.width = `${data.prediction.team2_probability}%`;
        }, 500);
        
        // Position labels for better visibility
        if (data.prediction.team1_probability < 20) {
            team1ProbLabel.style.left = '100%';
            team1ProbLabel.style.color = '#333';
            team1ProbLabel.style.textShadow = 'none';
        } else {
            team1ProbLabel.style.left = ''; // Reset to default
            team1ProbLabel.style.color = 'white';
            team1ProbLabel.style.textShadow = '0 1px 2px rgba(0,0,0,0.2)';
        }
        
        if (data.prediction.team2_probability < 20) {
            team2ProbLabel.style.right = '100%';
            team2ProbLabel.style.color = '#333';
            team2ProbLabel.style.textShadow = 'none';
        } else {
            team2ProbLabel.style.right = ''; // Reset to default
            team2ProbLabel.style.color = 'white';
            team2ProbLabel.style.textShadow = '0 1px 2px rgba(0,0,0,0.2)';
        }
        
        // Update team names
        document.getElementById('team1-name').textContent = data.team1;
        document.getElementById('team2-name').textContent = data.team2;
        document.getElementById('stats-team1').textContent = data.team1;
        document.getElementById('stats-team2').textContent = data.team2;
        
        // Update players display with animations
        displayTeamPlayers(data);
        
        // Update stats
        updateStatistics(data);
        
        // Scroll to results
        document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error("Error displaying results:", error);
        alert("Error displaying prediction results: " + error.message);
        document.getElementById('results').style.display = 'none';
    }
}

// Display team players with role-based styling
function displayTeamPlayers(data) {
    const team1PlayersDiv = document.getElementById('team1-players-display');
    const team2PlayersDiv = document.getElementById('team2-players-display');
    
    team1PlayersDiv.innerHTML = '';
    team2PlayersDiv.innerHTML = '';
    
    if (Array.isArray(data.team1_players)) {
        data.team1_players.forEach((player, index) => {
            const span = document.createElement('span');
            span.className = 'player-badge role-batsman'; // Default to batsman role
            span.textContent = player;
            
            // Add fade-in animation
            span.style.opacity = 0;
            span.style.transform = 'translateY(10px)';
            team1PlayersDiv.appendChild(span);
            
            setTimeout(() => {
                span.style.transition = "all 0.3s ease";
                span.style.opacity = 1;
                span.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    }
    
    if (Array.isArray(data.team2_players)) {
        data.team2_players.forEach((player, index) => {
            const span = document.createElement('span');
            span.className = 'player-badge role-batsman'; // Default to batsman role
            span.textContent = player;
            
            // Add fade-in animation
            span.style.opacity = 0;
            span.style.transform = 'translateY(10px)';
            team2PlayersDiv.appendChild(span);
            
            setTimeout(() => {
                span.style.transition = "all 0.3s ease";
                span.style.opacity = 1;
                span.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    }
}

// Update match statistics
function updateStatistics(data) {
    if (data.stats) {
        document.getElementById('team1-elo').textContent = data.stats.team1_avg_elo || '-';
        document.getElementById('team2-elo').textContent = data.stats.team2_avg_elo || '-';
        document.getElementById('team1-form').textContent = data.stats.team1_avg_form || '-';
        document.getElementById('team2-form').textContent = data.stats.team2_avg_form || '-';
        document.getElementById('h2h-record').textContent = data.stats.head_to_head ? 
            `${data.team1} ${data.stats.head_to_head} ${data.team2}` : '-';
    }
    
    document.getElementById('match-venue').textContent = data.venue || '-';
}

// Reset the prediction form
function resetForm() {
    document.getElementById('prediction-form').reset();
    document.getElementById('team1-players').innerHTML = '<p class="text-muted">Select a team first to see players</p>';
    document.getElementById('team2-players').innerHTML = '<p class="text-muted">Select a team first to see players</p>';
    document.getElementById('head2head-container').innerHTML = '';
    document.getElementById('results').style.display = 'none';
}

// Animate UI elements
function animateElements() {
    // Add subtle animation to team sections
    const teamSections = document.querySelectorAll('.team-section');
    teamSections.forEach((section, index) => {
        section.style.opacity = 0;
        section.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            section.style.transition = "all 0.5s ease";
            section.style.opacity = 1;
            section.style.transform = 'translateY(0)';
        }, 300 * index);
    });
}