import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
import aiosqlite
import sys
import threading
import re
from flask import Flask, request, jsonify
from config import Config
from database import PointsDatabase
from datetime import datetime

# Email validation regex
EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Points Bot Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 40px; }
            .status { color: green; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
            .card h3 { margin-top: 0; color: #333; }
            .commands { background: #fff3cd; border-left-color: #ffc107; }
            .dashboard-link { display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            .dashboard-link:hover { background: #0056b3; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f8f9fa; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Discord Points Bot Dashboard</h1>
                <p>Bot Status: <span class="status">Online ✅</span></p>
                <p>Bot Name: Pipi-bot#5480</p>
                <a href="/dashboard" class="dashboard-link">🎛️ Manage Points</a>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 Features</h3>
                    <ul>
                        <li>Points Management System</li>
                        <li>Leaderboard System</li>
                        <li>Silent Admin Commands</li>
                        <li>SQLite Database</li>
                        <li>Web Dashboard</li>
                    </ul>
                </div>
                
                <div class="card commands">
                    <h3>⚡ Slash Commands Available</h3>
                    <p><strong>/mypoints</strong> - Check your points (private)</p>
                    <p><strong>/pointsboard</strong> - View leaderboard</p>
                    <p><strong>/submitemail</strong> - Submit email (private)</p>
                    <p><strong>/updateemail</strong> - Update submitted email</p>
                    <p><strong>/myemail</strong> - Check email status</p>
                    <p><strong>/pipihelp</strong> - Show all commands</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/dashboard")
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .nav { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }
            .nav a { display: inline-block; margin: 0 15px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .nav a:hover { background: #0056b3; }
            .nav a.active { background: #28a745; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .card h3 { margin-top: 0; color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
            button:hover { background: #0056b3; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
            .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f8f9fa; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/" >← Home</a>
                <a href="#" onclick="showSection('emails')" class="active">Email Submissions</a>
                <a href="#" onclick="showSection('points')">Points Management</a>
                <a href="#" onclick="showSection('database')">Database Admin</a>
                <a href="#" onclick="showSection('achievements')">Achievements</a>
                <a href="#" onclick="showSection('analytics')">Analytics</a>
            </div>
            
            <!-- Email Submissions Section -->
            <div id="emails-section">
                <div class="card">
                    <h3>📧 Email Submissions Management</h3>
                    <p>Manage user email submissions for order verification and point distribution</p>
                    
                    <div class="form-group">
                        <button onclick="loadEmailSubmissions()" class="refresh-btn">🔄 Refresh Submissions</button>
                        <button onclick="exportEmailSubmissions()" class="export-btn">📥 Export to CSV</button>
                        <button onclick="clearProcessedEmails()" class="clear-btn" style="background: #dc3545; margin-left: 10px;">🗑️ Clear Processed</button>
                    </div>
                    
                    <div class="stats-grid" style="margin: 20px 0;">
                        <div class="stat-box">
                            <div class="stat-number" id="pending-count">-</div>
                            <div>Pending Submissions</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="processed-count">-</div>
                            <div>Processed Submissions</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="total-emails">-</div>
                            <div>Total Submissions</div>
                        </div>
                    </div>
                    
                    <div id="email-submissions-container">
                        <div class="loading">Loading email submissions...</div>
                    </div>
                </div>
            </div>
            
            <!-- Points Management Section -->
            <div id="points-section" class="hidden">
                <div class="grid">
                    <div class="card">
                        <h3>🎛️ Manage Points</h3>
                        <form id="pointsForm">
                            <div class="form-group">
                                <label for="action">Action:</label>
                                <select id="action" name="action" required>
                                    <option value="">Select action...</option>
                                    <option value="add">Add Points</option>
                                    <option value="remove">Remove Points</option>
                                    <option value="set">Set Points</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="user_id">User ID:</label>
                                <input type="text" id="user_id" name="user_id" placeholder="Discord User ID" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="amount">Points:</label>
                                <input type="number" id="amount" name="amount" min="1" max="1000000" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="reason">Reason (Optional):</label>
                                <input type="text" id="reason" name="reason" placeholder="Why are you making this change?">
                            </div>
                            
                            <button type="submit">Execute</button>
                        </form>
                        <div id="points-result"></div>
                    </div>
                    
                    <div class="card">
                        <h3>📊 Quick Stats</h3>
                        <div id="quick-stats">Loading...</div>
                        <button onclick="refreshStats()">Refresh Stats</button>
                    </div>
                </div>
            </div>
            
            <!-- Database Admin Section -->
            <div id="database-section" class="hidden">
                <div class="card">
                    <h3>🗄️ Database Administration</h3>
                    <div class="grid">
                        <div>
                            <h4>Recent Transactions</h4>
                            <div id="recent-transactions">Loading...</div>
                            <button onclick="loadTransactions()">Refresh Transactions</button>
                        </div>
                        <div>
                            <h4>Database Statistics</h4>
                            <div id="db-stats">Loading...</div>
                            <button onclick="loadDatabaseStats()">Refresh DB Stats</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Achievements Section -->
            <div id="achievements-section" class="hidden">
                <div class="grid">
                    <div class="card">
                        <h3>🏆 Add Achievement</h3>
                        <form id="achievementForm">
                            <div class="form-group">
                                <label for="ach_user_id">User ID:</label>
                                <input type="text" id="ach_user_id" name="user_id" required>
                            </div>
                            <div class="form-group">
                                <label for="ach_type">Achievement Type:</label>
                                <select id="ach_type" name="type" required>
                                    <option value="milestone">Milestone</option>
                                    <option value="special">Special Event</option>
                                    <option value="participation">Participation</option>
                                    <option value="achievement">General Achievement</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="ach_name">Achievement Name:</label>
                                <input type="text" id="ach_name" name="name" placeholder="e.g., First 1000 Points" required>
                            </div>
                            <div class="form-group">
                                <label for="ach_points">Bonus Points:</label>
                                <input type="number" id="ach_points" name="points" min="0" value="0">
                            </div>
                            <button type="submit">Add Achievement</button>
                        </form>
                        <div id="achievement-result"></div>
                    </div>
                    
                    <div class="card">
                        <h3>🏆 Recent Achievements</h3>
                        <div id="recent-achievements">Loading...</div>
                        <button onclick="loadAchievements()">Refresh</button>
                    </div>
                </div>
            </div>
            
            <!-- Analytics Section -->
            <div id="analytics-section" class="hidden">
                <div class="card">
                    <h3>📈 User Analytics</h3>
                    <form id="userAnalyticsForm">
                        <div class="form-group">
                            <label for="analytics_user_id">User ID for Detailed Analysis:</label>
                            <input type="text" id="analytics_user_id" name="user_id" placeholder="Discord User ID">
                            <button type="submit">Analyze User</button>
                        </div>
                    </form>
                    <div id="user-analytics-result"></div>
                </div>
            </div>
        </div>
        
        <script>
            function showSection(section) {
                // Hide all sections
                document.querySelectorAll('[id$="-section"]').forEach(el => el.classList.add('hidden'));
                // Show selected section
                document.getElementById(section + '-section').classList.remove('hidden');
                // Update nav
                document.querySelectorAll('.nav a').forEach(el => el.classList.remove('active'));
                event.target.classList.add('active');
            }
            
            function refreshStats() {
                fetch('/api/quick_stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('quick-stats').innerHTML = 
                        '<div class="stats-grid">' +
                        '<div class="stat-box"><div class="stat-number">' + data.total_users + '</div><div>Total Users</div></div>' +
                        '<div class="stat-box"><div class="stat-number">' + data.total_points + '</div><div>Total Points</div></div>' +
                        '<div class="stat-box"><div class="stat-number">' + data.total_transactions + '</div><div>Transactions</div></div>' +
                        '</div>';
                });
            }
            
            // Load initial stats
            refreshStats();
            
            function loadTransactions() {
                fetch('/api/recent_transactions')
                .then(response => response.json())
                .then(data => {
                    let html = '<table><tr><th>User ID</th><th>Amount</th><th>Type</th><th>Reason</th><th>Time</th></tr>';
                    if (data.transactions && data.transactions.length > 0) {
                        data.transactions.forEach(tx => {
                            html += '<tr><td>' + tx.user_id + '</td><td>' + tx.amount + '</td><td>' + tx.type + '</td><td>' + (tx.reason || 'N/A') + '</td><td>' + tx.timestamp + '</td></tr>';
                        });
                    } else {
                        html += '<tr><td colspan="5">No transactions found</td></tr>';
                    }
                    html += '</table>';
                    document.getElementById('recent-transactions').innerHTML = html;
                });
            }
            
            function loadDatabaseStats() {
                fetch('/api/database_stats')
                .then(response => response.json())
                .then(data => {
                    let html = '<div class="stats-grid">';
                    html += '<div class="stat-box"><div class="stat-number">' + data.tables.points.rows + '</div><div>Users</div></div>';
                    html += '<div class="stat-box"><div class="stat-number">' + data.tables.transactions.rows + '</div><div>Transactions</div></div>';
                    html += '<div class="stat-box"><div class="stat-number">' + data.tables.achievements.rows + '</div><div>Achievements</div></div>';
                    html += '<div class="stat-box"><div class="stat-number">' + data.total_points + '</div><div>Total Points</div></div>';
                    html += '</div>';
                    document.getElementById('db-stats').innerHTML = html;
                });
            }
            
            function loadAchievements() {
                fetch('/api/recent_achievements')
                .then(response => response.json())
                .then(data => {
                    let html = '<table><tr><th>User ID</th><th>Type</th><th>Achievement</th><th>Points</th><th>Date</th></tr>';
                    if (data.achievements && data.achievements.length > 0) {
                        data.achievements.forEach(ach => {
                            html += '<tr><td>' + ach.user_id + '</td><td>' + ach.achievement_type + '</td><td>' + ach.achievement_name + '</td><td>' + ach.points_earned + '</td><td>' + ach.earned_at + '</td></tr>';
                        });
                    } else {
                        html += '<tr><td colspan="5">No achievements found</td></tr>';
                    }
                    html += '</table>';
                    document.getElementById('recent-achievements').innerHTML = html;
                });
            }
            
            // Form handlers
            document.getElementById('pointsForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                fetch('/api/manage_points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    const resultDiv = document.getElementById('points-result');
                    if (data.success) {
                        resultDiv.innerHTML = '<div class="success">' + data.message + '</div>';
                        refreshStats();
                    } else {
                        resultDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                    }
                });
            });
            
            document.getElementById('achievementForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                fetch('/api/add_achievement', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    const resultDiv = document.getElementById('achievement-result');
                    if (data.success) {
                        resultDiv.innerHTML = '<div class="success">' + data.message + '</div>';
                        loadAchievements();
                        refreshStats();
                        document.getElementById('achievementForm').reset();
                    } else {
                        resultDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                    }
                });
            });
            
            document.getElementById('userAnalyticsForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                fetch('/api/user_analytics', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    const resultDiv = document.getElementById('user-analytics-result');
                    if (data.success) {
                        const analytics = data.analytics;
                        let html = '<div class="card"><h4>User Analytics for ' + analytics.user_id + '</h4>';
                        html += '<div class="stats-grid">';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.current_balance + '</div><div>Current Balance</div></div>';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.total_earned + '</div><div>Total Earned</div></div>';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.total_spent + '</div><div>Total Spent</div></div>';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.highest_balance + '</div><div>Highest Balance</div></div>';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.transaction_count + '</div><div>Transactions</div></div>';
                        html += '<div class="stat-box"><div class="stat-number">' + analytics.rank + '</div><div>Server Rank</div></div>';
                        html += '</div></div>';
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                    }
                });
            });

            // Email submissions functions
            async function loadEmailSubmissions() {
                try {
                    const response = await fetch('/api/email_submissions');
                    const data = await response.json();
                    
                    if (data.success) {
                        displayEmailSubmissions(data.submissions, data.stats);
                    } else {
                        document.getElementById('email-submissions-container').innerHTML = 
                            '<div style="color: red; padding: 10px;">Failed to load email submissions</div>';
                    }
                } catch (error) {
                    document.getElementById('email-submissions-container').innerHTML = 
                        '<div style="color: red; padding: 10px;">Error: ' + error.message + '</div>';
                }
            }

            function displayEmailSubmissions(submissions, stats) {
                document.getElementById('pending-count').textContent = stats.pending || 0;
                document.getElementById('processed-count').textContent = stats.processed || 0;
                document.getElementById('total-emails').textContent = stats.total || 0;
                
                const container = document.getElementById('email-submissions-container');
                
                if (!submissions || submissions.length === 0) {
                    container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No email submissions found</div>';
                    return;
                }
                
                let html = '<table><thead><tr>';
                html += '<th>Discord User</th><th>User ID</th><th>Email</th><th>Status</th>';
                html += '<th>Submitted</th><th>Actions</th></tr></thead><tbody>';
                
                submissions.forEach(sub => {
                    const statusColor = sub.status === 'pending' ? '#ffc107' : '#28a745';
                    html += '<tr>';
                    html += '<td><strong>' + sub.discord_username + '</strong></td>';
                    html += '<td><code style="font-size: 11px;">' + sub.discord_user_id + '</code></td>';
                    html += '<td><strong>' + sub.email_address + '</strong></td>';
                    html += '<td><span style="background: ' + statusColor + '; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">' + sub.status.toUpperCase() + '</span></td>';
                    html += '<td style="font-size: 12px;">' + new Date(sub.submitted_at).toLocaleString() + '</td>';
                    html += '<td>';
                    if (sub.status === 'pending') {
                        html += '<button onclick="markEmailProcessed(' + sub.id + ')" style="background: #28a745; font-size: 12px; padding: 4px 8px; margin-right: 5px; color: white; border: none; border-radius: 3px;">✓ Processed</button>';
                    }
                    html += '<button onclick="deleteEmailSubmission(' + sub.id + ')" style="background: #dc3545; font-size: 12px; padding: 4px 8px; color: white; border: none; border-radius: 3px;">🗑️ Delete</button>';
                    html += '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            }

            async function markEmailProcessed(submissionId) {
                if (!confirm('Mark this email submission as processed?')) return;
                
                try {
                    const response = await fetch('/api/process_email_submission', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ submission_id: submissionId })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadEmailSubmissions();
                        alert('Email submission marked as processed!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function deleteEmailSubmission(submissionId) {
                if (!confirm('Delete this email submission? This cannot be undone.')) return;
                
                try {
                    const response = await fetch('/api/delete_email_submission', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ submission_id: submissionId })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadEmailSubmissions();
                        alert('Email submission deleted!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function exportEmailSubmissions() {
                try {
                    const response = await fetch('/api/export_email_submissions');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'email_submissions_' + new Date().toISOString().split('T')[0] + '.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    alert('Email submissions exported successfully!');
                } catch (error) {
                    alert('Error exporting: ' + error.message);
                }
            }

            async function clearProcessedEmails() {
                if (!confirm('Delete all processed email submissions? This cannot be undone.')) return;
                
                try {
                    const response = await fetch('/api/clear_processed_emails', {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadEmailSubmissions();
                        alert('Processed emails cleared!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            // Load email submissions when page loads
            document.addEventListener('DOMContentLoaded', function() {
                loadEmailSubmissions();
            });

        </script>
    </body>
    </html>
    """

@app.route("/api/manage_points", methods=["POST"])
def manage_points():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        action = data.get('action')
        user_id_str = data.get('user_id')
        amount_str = data.get('amount')
        
        if not all([action, user_id_str, amount_str]):
            return jsonify({"success": False, "error": "Missing required fields"})
        
        try:
            user_id = int(user_id_str)
            amount = int(amount_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid user ID or amount format"})
        
        # Validate inputs
        if action not in ['add', 'remove', 'set']:
            return jsonify({"success": False, "error": "Invalid action"})
        
        if amount <= 0 or amount > 1000000:
            return jsonify({"success": False, "error": "Amount must be between 1 and 1,000,000"})
        
        # Simple approach: create a new database instance for Flask operations
        try:
            from database import PointsDatabase
            db = PointsDatabase()
            
            # Run the async database operation
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Initialize database connection
                loop.run_until_complete(db.initialize())
                
                reason = data.get('reason', 'Dashboard operation')
                admin_id = 0  # Dashboard admin ID
                
                if action == 'add':
                    success = loop.run_until_complete(db.update_points(user_id, amount, admin_id, reason))
                    if success:
                        new_balance = loop.run_until_complete(db.get_points(user_id))
                        message = f"Successfully added {amount:,} points. New balance: {new_balance:,}"
                    else:
                        return jsonify({"success": False, "error": "Failed to add points to database"})
                elif action == 'remove':
                    current_balance = loop.run_until_complete(db.get_points(user_id))
                    if current_balance < amount:
                        return jsonify({"success": False, "error": f"User only has {current_balance:,} points"})
                    success = loop.run_until_complete(db.update_points(user_id, -amount, admin_id, reason))
                    if success:
                        new_balance = loop.run_until_complete(db.get_points(user_id))
                        message = f"Successfully removed {amount:,} points. New balance: {new_balance:,}"
                    else:
                        return jsonify({"success": False, "error": "Failed to remove points from database"})
                else:  # set
                    success = loop.run_until_complete(db.set_points(user_id, amount, admin_id, reason))
                    if success:
                        message = f"Successfully set points to {amount:,}"
                    else:
                        return jsonify({"success": False, "error": "Failed to set points in database"})
                        
                # Close database connection
                loop.run_until_complete(db.close())
                        
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Database operation error: {e}")
            return jsonify({"success": False, "error": f"Database error: {str(e)}"})
        
        # Log the dashboard action
        logger.info(f"Dashboard API request: {action} {amount} points for user {user_id}")
        
        return jsonify({"success": True, "message": message})
        
    except Exception as e:
        logger.error(f"Error in manage_points API: {e}")
        return jsonify({"success": False, "error": "Internal server error"})

@app.route("/api/quick_stats")
def quick_stats():
    """API endpoint for quick dashboard stats"""
    try:
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get real database stats
            stats = loop.run_until_complete(db.get_database_stats())
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({
                "total_users": stats.get('total_users', 0),
                "total_points": stats.get('total_points', 0),
                "total_transactions": stats.get('total_transactions', 0),
                "total_achievements": stats.get('total_achievements', 0)
            })
            
        finally:
            loop.close()
                
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        return jsonify({
            "total_users": 0,
            "total_points": 0,
            "total_transactions": 0,
            "total_achievements": 0
        })

@app.route("/api/recent_achievements")
def recent_achievements():
    """API endpoint for recent achievements"""
    try:
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get recent achievements from database
            achievements_data = loop.run_until_complete(db.get_achievements(limit=10))
            
            # Format achievements for API response
            achievements = []
            for ach in achievements_data:
                achievements.append({
                    "id": ach[0],
                    "user_id": str(ach[1]),
                    "achievement_type": ach[2],
                    "achievement_name": ach[3],
                    "points_earned": ach[4],
                    "earned_at": ach[5]
                })
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"achievements": achievements})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting recent achievements: {e}")
        return jsonify({"achievements": []})

@app.route("/api/database_stats")
def database_stats():
    """API endpoint for detailed database statistics"""
    try:
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get database statistics
            stats = loop.run_until_complete(db.get_database_stats())
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            # Format response with real data
            return jsonify({
                "tables": {
                    "points": {"rows": stats.get('total_users', 0)},
                    "transactions": {"rows": stats.get('total_transactions', 0)},
                    "achievements": {"rows": stats.get('total_achievements', 0)},
                    "user_stats": {"rows": stats.get('total_users', 0)}
                },
                "total_points": stats.get('total_points', 0),
                "most_active_user": stats.get('most_active_user')
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({
            "tables": {"points": {"rows": 0}, "transactions": {"rows": 0}, "achievements": {"rows": 0}, "user_stats": {"rows": 0}},
            "total_points": 0,
            "most_active_user": None
        })

@app.route("/api/recent_transactions")
def recent_transactions():
    """API endpoint for recent transactions"""
    try:
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get recent transactions from database
            transactions_data = loop.run_until_complete(db.get_transactions(limit=10))
            
            # Format transactions for API response
            transactions = []
            for tx in transactions_data:
                transactions.append({
                    "id": tx[0],
                    "user_id": str(tx[1]),
                    "amount": tx[2],
                    "type": tx[3],
                    "admin_id": tx[4],
                    "reason": tx[5] or "No reason provided",
                    "old_balance": tx[6],
                    "new_balance": tx[7],
                    "timestamp": tx[8]
                })
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"transactions": transactions})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting recent transactions: {e}")
        return jsonify({"transactions": []})

@app.route("/api/add_achievement", methods=["POST"])
def add_achievement():
    """API endpoint for adding achievements"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id_str = data.get('user_id')
        ach_type = data.get('type')
        ach_name = data.get('name')
        points_str = data.get('points', '0')
        
        if not all([user_id_str, ach_type, ach_name]):
            return jsonify({"success": False, "error": "Missing required fields"})
        
        try:
            user_id = int(user_id_str)
            points = int(points_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid user ID or points format"})
        
        # Connect to database and add achievement
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Add achievement to database
            success = loop.run_until_complete(db.add_achievement(user_id, ach_type, ach_name, points))
            
            if success:
                # If achievement has bonus points, add them to user's balance
                if points > 0:
                    loop.run_until_complete(db.update_points(user_id, points, 0, f"Achievement bonus: {ach_name}"))
                
                message = f"Added achievement '{ach_name}' to user {user_id}"
                if points > 0:
                    message += f" with {points} bonus points"
            else:
                return jsonify({"success": False, "error": "Failed to add achievement to database"})
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": message})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error adding achievement: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/user_analytics", methods=["POST"])
def user_analytics():
    """API endpoint for user analytics"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id_str = data.get('user_id')
        if not user_id_str:
            return jsonify({"success": False, "error": "User ID is required"})
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid user ID format"})
        
        from database import PointsDatabase
        db = PointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get user analytics from database
            analytics_data = loop.run_until_complete(db.get_user_analytics(user_id))
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if analytics_data:
                return jsonify({
                    "success": True,
                    "analytics": {
                        "user_id": str(user_id),
                        "current_balance": analytics_data.get('current_balance', 0),
                        "total_earned": analytics_data.get('total_earned', 0),
                        "total_spent": analytics_data.get('total_spent', 0),
                        "highest_balance": analytics_data.get('highest_balance', 0),
                        "transaction_count": analytics_data.get('transaction_count', 0),
                        "rank": analytics_data.get('rank', 'N/A'),
                        "achievements_count": analytics_data.get('achievements_count', 0),
                        "last_activity": analytics_data.get('last_activity', 'Never')
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"No data found for user {user_id}"
                })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/email_submissions", methods=["GET"])
def get_email_submissions():
    """API endpoint to get all email submissions"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def fetch_submissions():
                async with aiosqlite.connect('points.db') as db:
                    # Get all submissions
                    cursor = await db.execute('''
                        SELECT id, discord_user_id, discord_username, email_address, 
                               submitted_at, status, processed_at, admin_notes
                        FROM email_submissions 
                        ORDER BY submitted_at DESC
                    ''')
                    submissions = await cursor.fetchall()
                    
                    # Get stats
                    stats_cursor = await db.execute('''
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                            SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed
                        FROM email_submissions
                    ''')
                    stats = await stats_cursor.fetchone()
                    
                    return submissions, stats
            
            submissions_data, stats_data = loop.run_until_complete(fetch_submissions())
            
            submissions = []
            for row in submissions_data:
                submissions.append({
                    'id': row[0],
                    'discord_user_id': row[1],
                    'discord_username': row[2],
                    'email_address': row[3],
                    'submitted_at': row[4],
                    'status': row[5],
                    'processed_at': row[6],
                    'admin_notes': row[7]
                })
            
            stats = {
                'total': stats_data[0] if stats_data else 0,
                'pending': stats_data[1] if stats_data else 0,
                'processed': stats_data[2] if stats_data else 0
            }
            
            return jsonify({
                "success": True,
                "submissions": submissions,
                "stats": stats
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting email submissions: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/process_email_submission", methods=["POST"])
def process_email_submission():
    """API endpoint to mark email submission as processed"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        submission_id = data.get('submission_id')
        if not submission_id:
            return jsonify({"success": False, "error": "Submission ID is required"})
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def mark_processed():
                async with aiosqlite.connect('points.db') as db:
                    await db.execute('''
                        UPDATE email_submissions 
                        SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (submission_id,))
                    await db.commit()
                    return True
            
            success = loop.run_until_complete(mark_processed())
            
            if success:
                return jsonify({"success": True, "message": "Email submission marked as processed"})
            else:
                return jsonify({"success": False, "error": "Failed to update submission"})
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing email submission: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/delete_email_submission", methods=["POST"])
def delete_email_submission():
    """API endpoint to delete email submission"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        submission_id = data.get('submission_id')
        if not submission_id:
            return jsonify({"success": False, "error": "Submission ID is required"})
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def delete_submission():
                async with aiosqlite.connect('points.db') as db:
                    await db.execute('DELETE FROM email_submissions WHERE id = ?', (submission_id,))
                    await db.commit()
                    return True
            
            success = loop.run_until_complete(delete_submission())
            
            if success:
                return jsonify({"success": True, "message": "Email submission deleted"})
            else:
                return jsonify({"success": False, "error": "Failed to delete submission"})
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error deleting email submission: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/export_email_submissions", methods=["GET"])
def export_email_submissions():
    """API endpoint to export email submissions as CSV"""
    try:
        import asyncio
        import csv
        from io import StringIO
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def fetch_all_submissions():
                async with aiosqlite.connect('points.db') as db:
                    cursor = await db.execute('''
                        SELECT discord_user_id, discord_username, email_address, 
                               submitted_at, status, processed_at, admin_notes
                        FROM email_submissions 
                        ORDER BY submitted_at DESC
                    ''')
                    return await cursor.fetchall()
            
            submissions = loop.run_until_complete(fetch_all_submissions())
            
            # Create CSV content
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Discord_User_ID', 'Discord_Username', 'Email_Address', 'Submitted_At', 'Status', 'Processed_At', 'Admin_Notes'])
            
            # Write data
            for row in submissions:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Return as downloadable file
            from flask import Response
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={"Content-disposition": f"attachment; filename=email_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error exporting email submissions: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/clear_processed_emails", methods=["POST"])
def clear_processed_emails():
    """API endpoint to delete all processed email submissions"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def clear_processed():
                async with aiosqlite.connect('points.db') as db:
                    cursor = await db.execute('DELETE FROM email_submissions WHERE status = "processed"')
                    await db.commit()
                    return cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            
            deleted_count = loop.run_until_complete(clear_processed())
            
            return jsonify({
                "success": True, 
                "message": f"Deleted {deleted_count} processed email submissions"
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error clearing processed emails: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/status")
def status():
    return {
        "status": "online",
        "bot_name": "Pipi-bot",
        "features": ["points_management", "leaderboard", "admin_commands", "web_dashboard", "database_admin", "achievements"],
        "database": "sqlite_enhanced"
    }

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

class PointsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None  # We'll create a custom help command
        )
        
        self.db = PointsDatabase()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        await self.db.initialize()
        
    async def on_ready(self):
        """Called when the bot has successfully connected to Discord"""
        if self.user:
            logger.info(f'Bot is ready! Logged in as {self.user} (ID: {self.user.id})')
            
            # Set bot status for slash commands
            activity = discord.Game(name="/pipihelp for commands | /mypoints | /pointsboard")
            await self.change_presence(activity=activity)
            
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}")
        
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
            
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument. Use `{Config.COMMAND_PREFIX}pipihelp` for command usage.")
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided. Please check your input and try again.")
            
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("❌ User not found. Please mention a valid user.")
            
        else:
            logger.error(f"Unexpected error in command {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

# Initialize bot
bot = PointsBot()

# Function to store user email (for the privacy slash command)
async def store_user_email(user_id: int, email: str):
    """Store user email in database"""
    async with aiosqlite.connect(bot.db.db_path) as db:
        # Create table if not exists
        await db.execute('''
            CREATE TABLE IF NOT EXISTS email_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_user_id INTEGER NOT NULL,
                discord_username TEXT NOT NULL,
                email_address TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                processed_at TIMESTAMP,
                admin_notes TEXT
            )
        ''')
        
        # Check if user already submitted an email
        cursor = await db.execute('''
            SELECT id FROM email_submissions 
            WHERE discord_user_id = ? AND status = 'pending'
        ''', (user_id,))
        
        existing = await cursor.fetchone()
        
        if existing:
            # Update existing submission
            await db.execute('''
                UPDATE email_submissions 
                SET email_address = ?, submitted_at = CURRENT_TIMESTAMP
                WHERE discord_user_id = ? AND status = 'pending'
            ''', (email, user_id))
        else:
            # Create new submission
            user = bot.get_user(user_id)
            username = user.display_name if user else f"User {user_id}"
            
            await db.execute('''
                INSERT INTO email_submissions (discord_user_id, discord_username, email_address)
                VALUES (?, ?, ?)
            ''', (user_id, username, email))
        
        await db.commit()

# Slash Commands
@bot.tree.command(name="mypoints", description="Check your points balance (sent privately)")
async def mypoints_slash(interaction: discord.Interaction):
    """Check your points balance via DM"""
    try:
        balance = await bot.db.get_points(interaction.user.id)
        
        embed = discord.Embed(
            title="💰 Your Points Balance",
            description=f"You currently have **{balance:,} points**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Always respond ephemerally for privacy
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Also try to send DM
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
    except Exception as e:
        logger.error(f"Error in mypoints slash command: {e}")
        await interaction.response.send_message("❌ An error occurred while checking your points balance.", ephemeral=True)

@bot.tree.command(name="pointsboard", description="Show the points leaderboard")
@app_commands.describe(limit="Number of users to show (max 25)")
async def pointsboard_slash(interaction: discord.Interaction, limit: int = 10):
    """Show the points leaderboard"""
    try:
        # Validate limit
        if limit <= 0:
            limit = 10
        elif limit > 25:
            limit = 25
            
        top_users = await bot.db.get_leaderboard(limit)
        
        if not top_users:
            await interaction.response.send_message("📊 No users found in the leaderboard.")
            return
            
        embed = discord.Embed(
            title="🏆 Points Leaderboard",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, (user_id, balance) in enumerate(top_users, 1):
            # Try to get user from the current guild first, then global cache
            user = interaction.guild.get_member(user_id) if interaction.guild else None
            if not user:
                user = bot.get_user(user_id)
            
            if user:
                username = user.display_name
            else:
                # Try to fetch user from Discord API as last resort
                try:
                    user = await bot.fetch_user(user_id)
                    username = user.display_name
                except:
                    username = f"User {user_id}"
            
            # Add medals for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
                
            description += f"{medal} **{username}** - {balance:,} points\n"
            
        embed.description = description
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in pointsboard slash command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching the leaderboard.")

@bot.tree.command(name="submitemail", description="Submit your email address (visible only to you)")
@app_commands.describe(email="Your email address")
async def submitemail_slash(interaction: discord.Interaction, email: str):
    """Submit your email address with privacy protection"""
    # Validate email format
    if not EMAIL_RE.fullmatch(email.strip()):
        await interaction.response.send_message(
            "❌ That doesn't look like a valid email. Please try again.",
            ephemeral=True
        )
        return

    try:
        # Store the email
        await store_user_email(interaction.user.id, email.strip())

        # Ephemeral confirmation
        await interaction.response.send_message(
            "✅ Your email has been successfully submitted, thank you!",
            ephemeral=True
        )

        # Also send a DM so they have a copy
        try:
            await interaction.user.send(f"✅ I have received your email: {email}")
        except discord.Forbidden:
            # Could not send DM (maybe DMs are closed)
            pass
            
    except Exception as e:
        logger.error(f"Error in submitemail slash command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while submitting your email. Please try again later.",
            ephemeral=True
        )

@bot.tree.command(name="updateemail", description="Update your previously submitted email address")
@app_commands.describe(email="Your new email address")
async def updateemail_slash(interaction: discord.Interaction, email: str):
    """Update your previously submitted email address"""
    # Validate email format
    if not EMAIL_RE.fullmatch(email.strip()):
        await interaction.response.send_message(
            "❌ That doesn't look like a valid email. Please try again.",
            ephemeral=True
        )
        return
        
    try:
        async with aiosqlite.connect(bot.db.db_path) as db:
            # Check if user has an existing submission
            cursor = await db.execute('''
                SELECT id, email_address FROM email_submissions 
                WHERE discord_user_id = ? AND status = 'pending'
            ''', (interaction.user.id,))
            
            existing = await cursor.fetchone()
            
            if not existing:
                await interaction.response.send_message(
                    "❌ No email submission found. Use `/submitemail` first.",
                    ephemeral=True
                )
                return
            
            submission_id, old_email = existing
            new_email = email.strip().lower()
            
            # Update the email address
            await db.execute('''
                UPDATE email_submissions 
                SET email_address = ?, submitted_at = CURRENT_TIMESTAMP,
                    admin_notes = COALESCE(admin_notes, '') || 'Updated from: ' || ? || ' | '
                WHERE id = ?
            ''', (new_email, old_email, submission_id))
            
            await db.commit()
            
            await interaction.response.send_message(
                f"✅ Email updated successfully from `{old_email}` to `{new_email}`",
                ephemeral=True
            )
            
            # Send DM confirmation
            try:
                await interaction.user.send(f"✅ Your email has been updated to: {new_email}")
            except discord.Forbidden:
                pass
        
    except Exception as e:
        logger.error(f"Error in updateemail slash command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while updating your email. Please try again later.",
            ephemeral=True
        )

@bot.tree.command(name="myemail", description="Check your current email submission status")
async def myemail_slash(interaction: discord.Interaction):
    """Check your current email submission status"""
    try:
        async with aiosqlite.connect(bot.db.db_path) as db:
            # Check for this user's submissions
            cursor = await db.execute('''
                SELECT email_address, submitted_at, status, processed_at
                FROM email_submissions 
                WHERE discord_user_id = ?
                ORDER BY submitted_at DESC
                LIMIT 1
            ''', (interaction.user.id,))
            
            submission = await cursor.fetchone()
        
        if not submission:
            embed = discord.Embed(
                title="📧 No Email Submission",
                description="You haven't submitted an email yet.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="How to submit:", 
                value="`/submitemail your-email@example.com`", 
                inline=False
            )
        else:
            email, submitted_at, status, processed_at = submission
            embed = discord.Embed(
                title="📧 Your Email Submission",
                description=f"**Email:** {email}",
                color=discord.Color.blue()
            )
            # Set color based on status
            if status == 'processed':
                embed.color = discord.Color.green()
                status_emoji = "✅"
            elif status == 'pending':
                embed.color = discord.Color.blue()
                status_emoji = "⏳"
            else:
                embed.color = discord.Color.red()
                status_emoji = "❌"
            
            embed.add_field(name="Status", value=f"{status_emoji} {status.title()}", inline=True)
            embed.add_field(name="Submitted", value=submitted_at, inline=True)
            if processed_at:
                embed.add_field(name="Processed", value=processed_at, inline=True)
            
            # Only show update option if still pending
            if status == 'pending':
                embed.add_field(
                    name="Need to change?", 
                    value="`/updateemail new-email@example.com`", 
                    inline=False
                )
            elif status == 'processed':
                embed.add_field(
                    name="Status Info", 
                    value="Your email has been processed by admin. Points may have been awarded!", 
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in myemail slash command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while checking your email status.",
            ephemeral=True
        )

@bot.tree.command(name="pipihelp", description="Show help information for all commands")
async def pipihelp_slash(interaction: discord.Interaction):
    """Show help information for all commands"""
    embed = discord.Embed(
        title="🤖 Points Bot Help",
        description="Manage member points with these slash commands:",
        color=discord.Color.blue()
    )
    
    # User commands
    embed.add_field(
        name="👤 User Commands",
        value="`/mypoints` - Check your points balance (private)\n"
              "`/pointsboard [limit]` - Show points leaderboard\n"
              "`/submitemail <email>` - Submit order email (private)\n"
              "`/updateemail <email>` - Update your submitted email\n"
              "`/myemail` - Check your email submission status\n"
              "`/pipihelp` - Show this help message",
        inline=False
    )
    
    embed.set_footer(text="Bot made with ❤️ | All personal data is kept private")
    await interaction.response.send_message(embed=embed)

# Admin slash commands
@bot.tree.command(name="status", description="Show bot status and statistics")
@app_commands.default_permissions(administrator=True)
async def status_slash(interaction: discord.Interaction):
    """Show bot status and statistics (Admin only)"""
    try:
        total_users = await bot.db.get_total_users()
        total_points = await bot.db.get_total_points()
        
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🔌 Status", value="Online ✅", inline=True)
        embed.add_field(name="👥 Total Users", value=f"{total_users:,}", inline=True)
        embed.add_field(name="💰 Total Points", value=f"{total_points:,}", inline=True)
        embed.add_field(name="🌐 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🏠 Servers", value=f"{len(bot.guilds)}", inline=True)
        embed.add_field(name="👤 Users", value=f"{len(bot.users)}", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in status slash command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching bot status.")

# Web Interface with admin dashboard continues below...
# All old prefix commands have been replaced with modern slash commands above

# Email regex for validation
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')




# Flask web server runner
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# Main execution
async def main():
    try:
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'your_bot_token_here':
            logger.error('Bot token not configured!')
            return
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info('Flask web server started on port 5000')
        async with bot:
            await bot.start(Config.BOT_TOKEN)
    except Exception as e:
        logger.error(f'Error starting bot: {e}')
    finally:
        if bot.db:
            await bot.db.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot shutdown requested')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
