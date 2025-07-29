import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
import asyncpg
import sys
import threading
import re
import os
from flask import Flask, request, jsonify
from config import Config
from database_postgresql import PostgreSQLPointsDatabase
from enhanced_achievements import check_and_award_achievements, get_user_achievements, get_recent_achievements, ACHIEVEMENT_TYPES
from datetime import datetime

# Email validation regex - improved pattern
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

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
app.secret_key = os.getenv("SESSION_SECRET", "default_session_secret_change_in_production")

@app.route("/")
def home():
    """Root health check endpoint that returns 200 status code for deployment health checks"""
    try:
        # Return a simple success response for health checks
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
        """, 200
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        # Even on error, return 200 for health checks with minimal response
        return "OK", 200

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
                <a href="#" onclick="showSection('overview')" class="active">📊 Overview</a>
                <a href="#" onclick="showSection('users')">👥 User Management</a>
                <a href="#" onclick="showSection('emails')">📧 Email Submissions</a>
                <a href="#" onclick="showSection('messages')">💬 Direct Messages</a>
            </div>
            
            <!-- Overview Section (NEW) -->
            <div id="overview-section">
                <div class="grid">
                    <div class="card">
                        <h3>📊 Database Overview</h3>
                        <div class="stats-grid">
                            <div class="stat-box">
                                <div class="stat-number" id="overview-total-users">-</div>
                                <div>Total Users</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number" id="overview-total-points">-</div>
                                <div>Total Points</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number" id="overview-pending-emails">-</div>
                                <div>Pending Emails</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-number" id="overview-achievements">-</div>
                                <div>Achievements Earned</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>🏆 Recent Achievements</h3>
                        <div id="recent-achievements-list">Loading achievements...</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📈 Recent Activity</h3>
                    <div id="recent-transactions-list">Loading transactions...</div>
                </div>
            </div>

            <!-- User Management Section -->
            <div id="users-section" class="hidden">
                <div class="card">
                    <h3>👥 User Management</h3>
                    <p>Unified management of users, points, and email submissions with search functionality</p>
                    
                    <div class="form-group">
                        <label for="user-search">🔍 Search Users (by Username, Email, or User ID):</label>
                        <input type="text" id="user-search" placeholder="Enter username, email, or user ID..." onkeyup="searchUsers()" style="margin-bottom: 10px;">
                        <button onclick="loadUsers()" class="refresh-btn">🔄 Refresh Users</button>
                        <button onclick="addNewUser()" class="export-btn" style="background: #17a2b8;">➕ Add New User</button>
                        <button onclick="exportUsers()" class="export-btn">📥 Export Users</button>
                    </div>
                    
                    <div class="stats-grid" style="margin: 20px 0;">
                        <div class="stat-box">
                            <div class="stat-number" id="total-users-count">-</div>
                            <div>Total Users</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="users-with-email">-</div>
                            <div>Users with Email</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="users-with-points">-</div>
                            <div>Users with Points</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="total-points-distributed">-</div>
                            <div>Total Points</div>
                        </div>
                    </div>
                    
                    <div id="users-container">
                        <div class="loading">Loading users...</div>
                    </div>
                </div>
            </div>

            <!-- Email Submissions Section -->
            <div id="emails-section" class="hidden">
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
            
            <!-- Direct Messages Section -->
            <div id="messages-section" class="hidden">
                <div class="card">
                    <h3>💬 Direct Messages Management</h3>
                    <p>Send direct messages to users and view message history with delivery tracking</p>
                    
                    <div class="grid">
                        <div class="card">
                            <h4>📤 Send New Message</h4>
                            <form id="sendMessageForm">
                                <div class="form-group">
                                    <label for="dm-user-lookup">User Lookup:</label>
                                    <input type="text" id="dm-user-lookup" placeholder="Enter User ID, Username, or Email Address" required style="margin-bottom: 5px;">
                                    <button type="button" onclick="lookupUser()" style="background: #28a745; font-size: 12px; padding: 4px 8px;">🔍 Find User</button>
                                    <div id="user-lookup-result" style="margin-top: 5px; font-size: 12px;"></div>
                                </div>
                                
                                <div class="form-group" style="display: none;" id="confirmed-user-section">
                                    <label for="dm-user-id">Confirmed User:</label>
                                    <input type="text" id="dm-user-id" name="user_id" readonly style="background: #f8f9fa;">
                                    <div id="confirmed-user-info" style="font-size: 12px; color: #666; margin-top: 2px;"></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="dm-message-type">Message Type:</label>
                                    <select id="dm-message-type" name="message_type" required>
                                        <option value="general">📢 General</option>
                                        <option value="order_status">📦 Order Status</option>
                                        <option value="error_alert">⚠️ Error Alert</option>
                                        <option value="important">🚨 Important Notice</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label for="dm-message">Message Content:</label>
                                    <textarea id="dm-message" name="message" rows="4" placeholder="Enter your message..." required></textarea>
                                </div>
                                
                                <button type="submit">Send Message</button>
                            </form>
                            <div id="send-message-result"></div>
                        </div>
                        
                        <div class="card">
                            <h4>📊 Message Statistics</h4>
                            <div class="stats-grid">
                                <div class="stat-box">
                                    <div class="stat-number" id="total-messages-sent">-</div>
                                    <div>Total Messages</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-number" id="messages-delivered">-</div>
                                    <div>Delivered</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-number" id="messages-failed">-</div>
                                    <div>Failed</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-number" id="messages-pending">-</div>
                                    <div>Pending</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h4>📬 Message History</h4>
                        <div class="form-group">
                            <button onclick="loadMessageHistory()" class="refresh-btn">🔄 Refresh History</button>
                            <button onclick="exportMessageHistory()" class="export-btn">📥 Export History</button>
                        </div>
                        
                        <div id="message-history-container">
                            <div class="loading">Loading message history...</div>
                        </div>
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
                
                // Load data for the selected section
                if (section === 'users') {
                    loadUsers();
                } else if (section === 'emails') {
                    loadEmailSubmissions();
                } else if (section === 'messages') {
                    loadMessageHistory();
                    loadMessageStats();
                } else if (section === 'database') {
                    loadTransactions();
                    loadDatabaseStats();
                } else if (section === 'achievements') {
                    loadAchievements();
                }
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
            
            // Load initial overview data on page load (overview section is default)
            loadOverviewData();
            
            function loadOverviewData() {
                // Load overview stats
                fetch('/api/quick_stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('overview-total-users').textContent = data.total_users || 0;
                    document.getElementById('overview-total-points').textContent = (data.total_points || 0).toLocaleString();
                    document.getElementById('overview-achievements').textContent = data.total_achievements || 0;
                });
                
                // Load pending email count
                fetch('/api/email_submissions')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.stats) {
                        document.getElementById('overview-pending-emails').textContent = data.stats.pending || 0;
                    }
                });
                
                // Load recent achievements
                fetch('/api/recent_achievements')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    if (data.achievements && data.achievements.length > 0) {
                        data.achievements.slice(0, 5).forEach(ach => {
                            html += '<div style="padding: 8px; border-bottom: 1px solid #eee;">';
                            html += '<strong>User ' + ach.user_id.slice(-4) + '</strong> earned <strong>' + ach.achievement_name + '</strong>';
                            html += '<div style="font-size: 12px; color: #666;">+' + ach.points_earned + ' points • ' + new Date(ach.earned_at).toLocaleDateString() + '</div>';
                            html += '</div>';
                        });
                    } else {
                        html = '<div style="padding: 20px; text-align: center; color: #666;">No recent achievements</div>';
                    }
                    document.getElementById('recent-achievements-list').innerHTML = html;
                });
                
                // Load recent transactions
                fetch('/api/recent_transactions')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    if (data.transactions && data.transactions.length > 0) {
                        data.transactions.slice(0, 8).forEach(tx => {
                            const color = tx.amount > 0 ? '#28a745' : '#dc3545';
                            html += '<div style="padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between;">';
                            html += '<div>User ' + tx.user_id.slice(-4) + ' • ' + (tx.reason || tx.type) + '</div>';
                            html += '<div style="color: ' + color + '; font-weight: bold;">' + (tx.amount > 0 ? '+' : '') + tx.amount + '</div>';
                            html += '</div>';
                        });
                    } else {
                        html = '<div style="padding: 20px; text-align: center; color: #666;">No recent transactions</div>';
                    }
                    document.getElementById('recent-transactions-list').innerHTML = html;
                });
            }
            
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

            // User Management Functions
            let allUsers = [];
            
            async function loadUsers() {
                try {
                    const response = await fetch('/api/users');
                    const data = await response.json();
                    allUsers = data.users || [];
                    
                    // Update stats
                    document.getElementById('total-users-count').textContent = data.stats.total_users || 0;
                    document.getElementById('users-with-email').textContent = data.stats.users_with_email || 0;
                    document.getElementById('users-with-points').textContent = data.stats.users_with_points || 0;
                    document.getElementById('total-points-distributed').textContent = data.stats.total_points || 0;
                    
                    displayUsers(allUsers);
                } catch (error) {
                    console.error('Error loading users:', error);
                    document.getElementById('users-container').innerHTML = '<div style="color: red;">Error loading users</div>';
                }
            }

            function searchUsers() {
                const searchTerm = document.getElementById('user-search').value.toLowerCase().trim();
                
                if (!searchTerm) {
                    displayUsers(allUsers);
                    return;
                }
                
                const filteredUsers = allUsers.filter(user => {
                    return (user.username && user.username.toLowerCase().includes(searchTerm)) ||
                           (user.email && user.email.toLowerCase().includes(searchTerm)) ||
                           (user.user_id && user.user_id.includes(searchTerm));
                });
                
                displayUsers(filteredUsers);
            }

            function displayUsers(users) {
                const container = document.getElementById('users-container');
                
                if (!users || users.length === 0) {
                    container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No users found</div>';
                    return;
                }

                let html = '<table><thead><tr>';
                html += '<th>Discord User</th><th>User ID</th><th>Points</th><th>Email</th>';
                html += '<th>Email Status</th><th>Actions</th></tr></thead><tbody>';
                
                users.forEach(user => {
                    const emailStatusColor = user.email_status === 'pending' ? '#ffc107' : user.email_status === 'processed' ? '#28a745' : '#6c757d';
                    const emailDisplay = user.email || 'No email';
                    
                    html += '<tr>';
                    html += '<td><strong>' + (user.username || 'Unknown') + '</strong></td>';
                    html += '<td><code style="font-size: 11px;">' + user.user_id + '</code></td>';
                    html += '<td><strong>' + (user.points || 0).toLocaleString() + '</strong></td>';
                    html += '<td>' + emailDisplay + '</td>';
                    html += '<td>';
                    if (user.email) {
                        html += '<span style="background: ' + emailStatusColor + '; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">' + (user.email_status || 'unknown').toUpperCase() + '</span>';
                    } else {
                        html += '<span style="color: #6c757d;">No Email</span>';
                    }
                    html += '</td>';
                    html += '<td>';
                    html += '<button onclick="editUser(' + "'" + user.user_id + "'" + ')" style="background: #007bff; font-size: 12px; padding: 4px 8px; margin-right: 5px; color: white; border: none; border-radius: 3px;">✏️ Edit Points</button>';
                    html += '<button onclick="editUserProfile(' + "'" + user.user_id + "'" + ')" style="background: #6f42c1; font-size: 12px; padding: 4px 8px; margin-right: 5px; color: white; border: none; border-radius: 3px;">👤 Edit Profile</button>';
                    if (user.email && user.email_status === 'pending') {
                        html += '<button onclick="processUserEmail(' + "'" + user.user_id + "'" + ')" style="background: #28a745; font-size: 12px; padding: 4px 8px; margin-right: 5px; color: white; border: none; border-radius: 3px;">✓ Process Email</button>';
                    }
                    html += '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            }

            async function editUser(userId) {
                const user = allUsers.find(u => u.user_id === userId);
                if (!user) {
                    alert('User not found');
                    return;
                }
                
                const newPoints = prompt('Set points for ' + (user.username || 'User ' + userId) + ':', user.points || 0);
                if (newPoints === null) return;
                
                const points = parseInt(newPoints);
                if (isNaN(points) || points < 0) {
                    alert('Please enter a valid number of points (0 or greater)');
                    return;
                }
                
                try {
                    const response = await fetch('/api/set_user_points', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            user_id: userId,
                            points: points,
                            reason: 'Admin set via user management'
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadUsers();
                        alert('Points updated successfully!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function editUserProfile(userId) {
                const user = allUsers.find(u => u.user_id === userId);
                if (!user) {
                    alert('User not found');
                    return;
                }
                
                const currentUsername = user.username && user.username !== `User ${userId}` ? user.username : '';
                const currentEmail = user.email || '';
                
                const newUsername = prompt('Set username for User ' + userId + ':', currentUsername);
                if (newUsername === null) return;
                
                const newEmail = prompt('Set email address for ' + (newUsername || 'User ' + userId) + ':', currentEmail);
                if (newEmail === null) return;
                
                // Basic email validation
                if (newEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
                    alert('Please enter a valid email address');
                    return;
                }
                
                try {
                    const response = await fetch('/api/update_user_profile', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            user_id: userId,
                            username: newUsername.trim(),
                            email: newEmail.trim()
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadUsers();
                        alert('User profile updated successfully!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function processUserEmail(userId) {
                const user = allUsers.find(u => u.user_id === userId);
                if (!user || !user.email) {
                    alert('User or email not found');
                    return;
                }
                
                if (!confirm('Mark email as processed for ' + (user.username || 'User ' + userId) + '?')) return;
                
                try {
                    const response = await fetch('/api/process_user_email', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: userId })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadUsers();
                        alert('Email processed successfully!');
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function addNewUser() {
                const userId = prompt('Enter Discord User ID (17-19 digits):');
                if (!userId || userId.trim() === '') return;
                
                // Basic validation for Discord user ID
                if (!/^\d{17,19}$/.test(userId.trim())) {
                    alert('Please enter a valid Discord User ID (17-19 digits)');
                    return;
                }
                
                const username = prompt('Enter username (optional):') || '';
                const email = prompt('Enter email address (optional):') || '';
                const points = prompt('Set initial points (default: 0):') || '0';
                
                // Validate email if provided
                if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                    alert('Please enter a valid email address');
                    return;
                }
                
                // Validate points
                const pointsValue = parseInt(points);
                if (isNaN(pointsValue) || pointsValue < 0) {
                    alert('Please enter a valid number of points (0 or greater)');
                    return;
                }
                
                try {
                    const response = await fetch('/api/add_new_user', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            user_id: userId.trim(),
                            username: username.trim(),
                            email: email.trim(),
                            points: pointsValue
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadUsers();
                        alert('New user added successfully!\\n\\n' + result.message);
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function exportUsers() {
                try {
                    const response = await fetch('/api/export_users');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'users_export_' + new Date().toISOString().split('T')[0] + '.csv';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } catch (error) {
                    alert('Error exporting users: ' + error.message);
                }
            }

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

                // Add bulk actions toolbar
                let html = '<div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;">';
                html += '<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">';
                html += '<label style="font-weight: bold; margin-right: 10px;"><input type="checkbox" id="select-all" onchange="toggleSelectAll()"> Select All</label>';
                html += '<button onclick="bulkAction(' + "'process'" + ')" style="background: #28a745; color: white; border: none; padding: 8px 12px; border-radius: 4px; font-size: 12px; cursor: pointer;">✓ Mark Selected as Processed</button>';
                html += '<button onclick="bulkAction(' + "'delete'" + ')" style="background: #dc3545; color: white; border: none; padding: 8px 12px; border-radius: 4px; font-size: 12px; cursor: pointer;">🗑️ Delete Selected</button>';
                html += '<span id="selected-count" style="margin-left: 10px; font-size: 12px; color: #666;">0 selected</span>';
                html += '</div></div>';
                
                html += '<table><thead><tr>';
                html += '<th style="width: 40px;">Select</th><th>Discord User</th><th>User ID</th><th>Email</th><th>Server Roles</th><th>Status</th>';
                html += '<th>Submitted</th><th>Actions</th></tr></thead><tbody>';
                
                submissions.forEach(sub => {
                    const statusColor = sub.status === 'pending' ? '#ffc107' : '#28a745';
                    let serverRoles = sub.server_roles;
                    let roleColor = '#6366f1';
                    
                    if (!serverRoles || serverRoles.trim() === '') {
                        serverRoles = 'Member only';
                        roleColor = '#9ca3af';
                    }
                    
                    html += '<tr>';
                    html += '<td><input type="checkbox" class="submission-checkbox" value="' + sub.id + '" onchange="updateSelectedCount()"></td>';
                    html += '<td><strong>' + sub.discord_username + '</strong></td>';
                    html += '<td><code style="font-size: 11px;">' + sub.discord_user_id + '</code></td>';
                    html += '<td><strong>' + sub.email_address + '</strong></td>';
                    html += '<td style="font-size: 11px; max-width: 200px; word-wrap: break-word;"><span style="color: ' + roleColor + '; font-weight: 500;">' + serverRoles + '</span></td>';
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

            function toggleSelectAll() {
                const selectAll = document.getElementById('select-all');
                const checkboxes = document.querySelectorAll('.submission-checkbox');
                
                checkboxes.forEach(checkbox => {
                    checkbox.checked = selectAll.checked;
                });
                
                updateSelectedCount();
            }

            function updateSelectedCount() {
                const checkboxes = document.querySelectorAll('.submission-checkbox:checked');
                const count = checkboxes.length;
                document.getElementById('selected-count').textContent = count + ' selected';
                
                // Update "Select All" checkbox state
                const allCheckboxes = document.querySelectorAll('.submission-checkbox');
                const selectAllCheckbox = document.getElementById('select-all');
                if (selectAllCheckbox) {
                    if (count === 0) {
                        selectAllCheckbox.indeterminate = false;
                        selectAllCheckbox.checked = false;
                    } else if (count === allCheckboxes.length) {
                        selectAllCheckbox.indeterminate = false;
                        selectAllCheckbox.checked = true;
                    } else {
                        selectAllCheckbox.indeterminate = true;
                    }
                }
            }

            async function bulkAction(action) {
                const selectedCheckboxes = document.querySelectorAll('.submission-checkbox:checked');
                const selectedIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
                
                if (selectedIds.length === 0) {
                    alert('Please select at least one submission');
                    return;
                }

                let confirmMessage = '';
                if (action === 'process') {
                    confirmMessage = `Mark ${selectedIds.length} selected submissions as processed?`;
                } else if (action === 'delete') {
                    confirmMessage = `Delete ${selectedIds.length} selected submissions? This cannot be undone.`;
                }

                if (!confirm(confirmMessage)) return;

                try {
                    const response = await fetch('/api/bulk_email_action', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            action: action,
                            submission_ids: selectedIds 
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        loadEmailSubmissions();
                        alert(result.message);
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
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

            // Direct Messages Functions
            async function loadMessageHistory() {
                try {
                    const response = await fetch('/api/message_history');
                    const data = await response.json();
                    
                    const container = document.getElementById('message-history-container');
                    
                    if (!data.messages || data.messages.length === 0) {
                        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No messages found</div>';
                        return;
                    }
                    
                    let html = '<table><thead><tr>';
                    html += '<th>Date</th><th>Admin</th><th>Recipient</th><th>Type</th><th>Message</th><th>Status</th></tr></thead><tbody>';
                    
                    data.messages.forEach(msg => {
                        const statusColor = msg.delivery_status === 'delivered' ? '#28a745' : 
                                          msg.delivery_status === 'failed' ? '#dc3545' : '#ffc107';
                        const statusIcon = msg.delivery_status === 'delivered' ? '✅' : 
                                         msg.delivery_status === 'failed' ? '❌' : '⏳';
                        
                        html += '<tr>';
                        html += '<td>' + new Date(msg.sent_at).toLocaleString() + '</td>';
                        html += '<td>' + msg.sender_admin_name + '</td>';
                        html += '<td>' + msg.recipient_username + '</td>';
                        html += '<td>' + msg.message_type.replace('_', ' ').toUpperCase() + '</td>';
                        html += '<td style="max-width: 300px; word-wrap: break-word;">' + 
                               msg.message_content.substring(0, 100) + 
                               (msg.message_content.length > 100 ? '...' : '') + '</td>';
                        html += '<td><span style="color: ' + statusColor + ';">' + statusIcon + ' ' + 
                               msg.delivery_status.toUpperCase() + '</span>';
                        if (msg.delivery_error) {
                            html += '<br><small style="color: #dc3545;">' + msg.delivery_error + '</small>';
                        }
                        html += '</td>';
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                    container.innerHTML = html;
                } catch (error) {
                    console.error('Error loading message history:', error);
                    document.getElementById('message-history-container').innerHTML = 
                        '<div style="color: red;">Error loading message history</div>';
                }
            }
            
            async function loadMessageStats() {
                try {
                    const response = await fetch('/api/message_stats');
                    const data = await response.json();
                    
                    document.getElementById('total-messages-sent').textContent = data.total || 0;
                    document.getElementById('messages-delivered').textContent = data.delivered || 0;
                    document.getElementById('messages-failed').textContent = data.failed || 0;
                    document.getElementById('messages-pending').textContent = data.pending || 0;
                } catch (error) {
                    console.error('Error loading message stats:', error);
                }
            }
            
            async function exportMessageHistory() {
                try {
                    const response = await fetch('/api/export_messages');
                    const data = await response.json();
                    
                    if (!data.messages || data.messages.length === 0) {
                        alert('No messages to export');
                        return;
                    }
                    
                    // Create CSV content
                    const headers = ['Date', 'Admin', 'Admin ID', 'Recipient', 'Recipient ID', 'Type', 'Message', 'Status', 'Error'];
                    let csvContent = headers.join(',') + '\\n';
                    
                    data.messages.forEach(msg => {
                        const row = [
                            '"' + new Date(msg.sent_at).toISOString() + '"',
                            '"' + msg.sender_admin_name + '"',
                            '"' + msg.sender_admin_id + '"',
                            '"' + msg.recipient_username + '"',
                            '"' + msg.recipient_user_id + '"',
                            '"' + msg.message_type + '"',
                            '"' + msg.message_content.replace(/"/g, '""') + '"',
                            '"' + msg.delivery_status + '"',
                            '"' + (msg.delivery_error || '') + '"'
                        ];
                        csvContent += row.join(',') + '\\n';
                    });
                    
                    // Download CSV
                    const blob = new Blob([csvContent], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'admin_messages_' + new Date().toISOString().split('T')[0] + '.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    alert('Message history exported successfully!');
                } catch (error) {
                    alert('Error exporting: ' + error.message);
                }
            }
            
            // User Lookup Function
            async function lookupUser() {
                const lookup = document.getElementById('dm-user-lookup').value.trim();
                const resultDiv = document.getElementById('user-lookup-result');
                const confirmedSection = document.getElementById('confirmed-user-section');
                
                if (!lookup) {
                    resultDiv.innerHTML = '<span style="color: #dc3545;">Please enter a User ID, username, or email address</span>';
                    return;
                }
                
                resultDiv.innerHTML = '<span style="color: #007bff;">🔍 Searching...</span>';
                
                try {
                    const response = await fetch('/api/lookup_user', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lookup: lookup })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success && result.user) {
                        const user = result.user;
                        resultDiv.innerHTML = '<span style="color: #28a745;">✅ User found!</span>';
                        
                        // Show confirmed user section
                        document.getElementById('dm-user-id').value = user.user_id;
                        document.getElementById('confirmed-user-info').innerHTML = 
                            '<strong>' + user.username + '</strong><br>' +
                            'Email: ' + (user.email || 'No email') + '<br>' +
                            'Points: ' + (user.points || 0).toLocaleString();
                        confirmedSection.style.display = 'block';
                    } else {
                        resultDiv.innerHTML = '<span style="color: #dc3545;">❌ ' + (result.error || 'User not found') + '</span>';
                        confirmedSection.style.display = 'none';
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<span style="color: #dc3545;">❌ Error: ' + error.message + '</span>';
                    confirmedSection.style.display = 'none';
                }
            }

            // Send Message Form Handler
            document.addEventListener('DOMContentLoaded', function() {
                loadEmailSubmissions();
                
                // Add event listener for send message form
                const sendForm = document.getElementById('sendMessageForm');
                if (sendForm) {
                    sendForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        
                        const formData = new FormData(sendForm);
                        const data = {
                            user_id: formData.get('user_id'),
                            message_type: formData.get('message_type'),
                            message: formData.get('message')
                        };
                        
                        if (!data.user_id || !data.message) {
                            alert('Please find a user first using the lookup function, then fill in the message');
                            return;
                        }
                        
                        try {
                            const response = await fetch('/api/send_dm', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(data)
                            });
                            
                            const result = await response.json();
                            const resultDiv = document.getElementById('send-message-result');
                            
                            if (result.success) {
                                resultDiv.innerHTML = '<div class="success">' + result.message + '</div>';
                                sendForm.reset();
                                loadMessageHistory();
                                loadMessageStats();
                            } else {
                                resultDiv.innerHTML = '<div class="error">Error: ' + result.error + '</div>';
                            }
                        } catch (error) {
                            document.getElementById('send-message-result').innerHTML = 
                                '<div class="error">Error: ' + error.message + '</div>';
                        }
                    });
                }
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
            user_id = user_id_str.strip()  # Keep as string to preserve Discord ID precision
            amount = int(amount_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid amount format"})
        
        # Validate inputs
        if action not in ['add', 'remove', 'set']:
            return jsonify({"success": False, "error": "Invalid action"})
        
        if amount <= 0 or amount > 1000000:
            return jsonify({"success": False, "error": "Amount must be between 1 and 1,000,000"})
        
        # Simple approach: create a new database instance for Flask operations
        try:
            from database_postgresql import PostgreSQLPointsDatabase
            db = PostgreSQLPointsDatabase()
            
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
                        # Check for new achievements
                        new_achievements = loop.run_until_complete(check_and_award_achievements(db, user_id, new_balance))
                        achievement_msg = f" (+{len(new_achievements)} achievements)" if new_achievements else ""
                        message = f"Successfully added {amount:,} points. New balance: {new_balance:,}{achievement_msg}"
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
                        # Check for new achievements after setting points
                        new_achievements = loop.run_until_complete(check_and_award_achievements(db, user_id, amount))
                        achievement_msg = f" (+{len(new_achievements)} achievements)" if new_achievements else ""
                        message = f"Successfully set points to {amount:,}{achievement_msg}"
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
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
                "total_users": stats['tables']['points']['rows'],
                "total_points": stats['total_points'],
                "total_transactions": stats['tables']['transactions']['rows'],
                "total_achievements": stats['tables']['achievements']['rows']
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
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
            
            # Format response with actual database data
            return jsonify({
                "tables": {
                    "points": {"rows": stats['tables']['points']['rows']},
                    "transactions": {"rows": stats['tables']['transactions']['rows']},
                    "achievements": {"rows": stats['tables']['achievements']['rows']},
                    "user_stats": {"rows": stats['tables']['points']['rows']}  # Same as points table
                },
                "total_points": stats['total_points'],
                "most_active_user": None  # Can add this later if needed
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
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
            user_id = user_id_str.strip()  # Keep as string to preserve Discord ID precision
        except ValueError:
            return jsonify({"success": False, "error": "Invalid user ID format"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get user analytics and current balance from database
            analytics_data = loop.run_until_complete(db.get_user_analytics(user_id))
            current_balance = loop.run_until_complete(db.get_points(user_id))
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if analytics_data:
                # analytics_data is a tuple: (total_points_earned, total_points_spent, highest_balance, transactions_count, achievements_count, first_activity, last_activity)
                return jsonify({
                    "success": True,
                    "analytics": {
                        "user_id": str(user_id),
                        "current_balance": current_balance or 0,
                        "total_earned": analytics_data[0] or 0,
                        "total_spent": analytics_data[1] or 0,
                        "highest_balance": analytics_data[2] or 0,
                        "transaction_count": analytics_data[3] or 0,
                        "achievements_count": analytics_data[4] or 0,
                        "first_activity": str(analytics_data[5]) if analytics_data[5] else 'Never',
                        "last_activity": str(analytics_data[6]) if analytics_data[6] else 'Never',
                        "rank": 'N/A'  # Can calculate separately if needed
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
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get all email submissions from PostgreSQL
            submissions_data = loop.run_until_complete(db.get_email_submissions())
            
            submissions = []
            for row in submissions_data:
                # Get current Discord username for display
                current_username = row[2]  # Default to stored username
                try:
                    user = bot.get_user(row[1])
                    if not user:
                        user = loop.run_until_complete(bot.fetch_user(row[1]))
                    if user:
                        current_username = user.display_name
                except Exception as e:
                    logger.debug(f"Could not fetch user {row[1]}: {e}")
                    if not current_username or current_username.startswith('User '):
                        current_username = f"User {row[1]}"
                
                submissions.append({
                    'id': row[0],
                    'discord_user_id': row[1],
                    'discord_username': current_username,
                    'email_address': row[3],
                    'submitted_at': row[4].isoformat() if row[4] else None,
                    'status': row[5],
                    'processed_at': row[6].isoformat() if row[6] else None,
                    'admin_notes': row[7],
                    'server_roles': row[8] if len(row) > 8 else ""
                })
            
            # Get submission statistics
            stats_query = '''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed
                FROM email_submissions
            '''
            stats_result = loop.run_until_complete(db.execute_query(stats_query))
            stats_data = stats_result[0] if stats_result else (0, 0, 0)
            
            stats = {
                'total': stats_data[0],
                'pending': stats_data[1],
                'processed': stats_data[2]
            }
            
            # Close database connection
            loop.run_until_complete(db.close())
            
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
            # Use PostgreSQL database for processing
            from database_postgresql import PostgreSQLPointsDatabase
            db = PostgreSQLPointsDatabase()
            
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get email details before processing for notification
            get_query = '''
                SELECT discord_user_id, email_address FROM email_submissions 
                WHERE id = $1
            '''
            email_result = loop.run_until_complete(db.execute_query(get_query, submission_id))
            
            if not email_result:
                loop.run_until_complete(db.close())
                return jsonify({"success": False, "error": "Email submission not found"})
            
            user_id, user_email = email_result[0]
            
            # Mark submission as processed
            update_query = '''
                UPDATE email_submissions 
                SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            '''
            result = loop.run_until_complete(db.execute_query(update_query, submission_id))
            
            # Send DM notification about email processing
            notification_message = f"✅ **Email Processed**\n\nYour email submission **{user_email}** has been processed by an admin.\n\n📧 Status: **Completed**\n🕒 Processed at: **{datetime.now().strftime('%Y-%m-%d %H:%M')}**"
            send_admin_notification_dm_sync(user_id, notification_message, "email_processed")
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": "Email submission marked as processed"})
                
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
            # Use PostgreSQL database for deletion
            from database_postgresql import PostgreSQLPointsDatabase
            db = PostgreSQLPointsDatabase()
            
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get email details before deletion for notification
            get_query = '''
                SELECT discord_user_id, email_address, status FROM email_submissions 
                WHERE id = $1
            '''
            email_result = loop.run_until_complete(db.execute_query(get_query, submission_id))
            
            if not email_result:
                loop.run_until_complete(db.close())
                return jsonify({"success": False, "error": "Email submission not found"})
            
            user_id, user_email, status = email_result[0]
            
            # Delete submission
            delete_query = 'DELETE FROM email_submissions WHERE id = $1'
            result = loop.run_until_complete(db.execute_query(delete_query, submission_id))
            
            # Send DM notification about email deletion
            from datetime import datetime
            notification_message = f"🗑️ **Email Submission Removed**\n\nYour email submission **{user_email}** has been removed by an admin.\n\n📧 Previous Status: **{status.title()}**\n🕒 Removed at: **{datetime.now().strftime('%Y-%m-%d %H:%M')}**\n\n💡 You can submit a new email using `/submitemail` if needed."
            send_admin_notification_dm_sync(user_id, notification_message, "email_deleted")
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": "Email submission deleted"})
                
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
            # Use PostgreSQL database for export
            from database_postgresql import PostgreSQLPointsDatabase
            db = PostgreSQLPointsDatabase()
            
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get all submissions for export
            submissions = loop.run_until_complete(db.get_email_submissions())
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            # Create CSV content
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Discord_User_ID', 'Discord_Username', 'Email_Address', 'Submitted_At', 'Status', 'Processed_At', 'Admin_Notes'])
            
            # Write data with ' prefix for user IDs to preserve Excel formatting
            for row in submissions:
                # Add apostrophe prefix to user ID to prevent Excel from changing format
                formatted_row = list(row)
                formatted_row[1] = "'" + str(row[1])  # Add ' to user ID
                writer.writerow(formatted_row)
            
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

@app.route("/api/bulk_email_action", methods=["POST"])
def bulk_email_action():
    """API endpoint for bulk actions on email submissions"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        action = data.get('action')
        submission_ids = data.get('submission_ids', [])
        
        if not action or not submission_ids:
            return jsonify({"success": False, "error": "Action and submission_ids are required"})
        
        if action not in ['process', 'delete']:
            return jsonify({"success": False, "error": "Invalid action. Use 'process' or 'delete'"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            if action == 'process':
                # Mark submissions as processed
                for submission_id in submission_ids:
                    update_query = '''
                        UPDATE email_submissions 
                        SET status = 'processed', processed_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    '''
                    loop.run_until_complete(db.execute_query(update_query, submission_id))
                
                message = f"Successfully marked {len(submission_ids)} submissions as processed"
                
            elif action == 'delete':
                # Delete submissions
                for submission_id in submission_ids:
                    delete_query = 'DELETE FROM email_submissions WHERE id = $1'
                    loop.run_until_complete(db.execute_query(delete_query, submission_id))
                
                message = f"Successfully deleted {len(submission_ids)} submissions"
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": message})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in bulk email action: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/users")
def api_users():
    """API endpoint for unified user management"""
    try:
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get combined user data with points and email info
            query = '''
                SELECT 
                    COALESCE(p.user_id, es.discord_user_id) as user_id,
                    p.balance as points,
                    es.email_address,
                    es.status as email_status,
                    es.discord_username
                FROM points p
                FULL OUTER JOIN email_submissions es ON p.user_id = es.discord_user_id
                ORDER BY COALESCE(p.balance, 0) DESC
            '''
            
            users_data = loop.run_until_complete(db.execute_query(query))
            
            # Format users for API response
            users = []
            for user in users_data:
                users.append({
                    "user_id": user[0],
                    "points": user[1] or 0,
                    "email": user[2],
                    "email_status": user[3],
                    "username": user[4] or f"User {user[0]}"
                })
            
            # Get statistics
            stats_queries = {
                'total_users': 'SELECT COUNT(DISTINCT COALESCE(p.user_id, es.discord_user_id)) FROM points p FULL OUTER JOIN email_submissions es ON p.user_id = es.discord_user_id',
                'users_with_email': 'SELECT COUNT(*) FROM email_submissions',
                'users_with_points': 'SELECT COUNT(*) FROM points',
                'total_points': 'SELECT COALESCE(SUM(balance), 0) FROM points'
            }
            
            stats = {}
            for key, query in stats_queries.items():
                result = loop.run_until_complete(db.execute_query(query))
                stats[key] = result[0][0] if result and result[0] else 0
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({
                "success": True,
                "users": users,
                "stats": stats
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "users": [],
            "stats": {"total_users": 0, "users_with_email": 0, "users_with_points": 0, "total_points": 0}
        })

@app.route("/api/set_user_points", methods=["POST"])
def set_user_points():
    """API endpoint for setting user points"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id = data.get('user_id')
        points = data.get('points')
        reason = data.get('reason', 'Admin set points')
        
        if not user_id or points is None:
            return jsonify({"success": False, "error": "Missing user_id or points"})
        
        try:
            points = int(points)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid points format"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get current points before updating
            current_points = loop.run_until_complete(db.get_points(user_id))
            
            # Set user points
            success = loop.run_until_complete(db.set_points(user_id, points, admin_id=None, reason=reason))
            
            # Send DM notification if successful
            if success:
                notification_message = f"🔄 **Points Updated**\n\nYour points have been set to **{points:,} points**.\n\n📝 **Reason:** {reason or 'Admin adjustment'}"
                send_admin_notification_dm_sync(user_id, notification_message, "points_update")
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if success:
                return jsonify({"success": True, "message": f"Points set to {points} for user {user_id}"})
            else:
                return jsonify({"success": False, "error": "Failed to set points"})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error setting user points: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/process_user_email", methods=["POST"])
def process_user_email():
    """API endpoint for processing user email"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get email details before processing
            email_query = '''
                SELECT email_address FROM email_submissions 
                WHERE discord_user_id = $1 AND status = 'pending'
            '''
            email_result = loop.run_until_complete(db.execute_query(email_query, user_id))
            user_email = email_result[0][0] if email_result else "your email"
            
            # Update email status to processed
            query = '''
                UPDATE email_submissions 
                SET status = 'processed', processed_at = CURRENT_TIMESTAMP 
                WHERE discord_user_id = $1 AND status = 'pending'
            '''
            
            result = loop.run_until_complete(db.execute_query(query, user_id))
            
            # Send DM notification about email processing
            notification_message = f"✅ **Email Processed**\n\nYour email submission **{user_email}** has been processed by an admin.\n\n📧 Status: **Completed**\n🕒 Processed at: **{datetime.now().strftime('%Y-%m-%d %H:%M')}**"
            send_admin_notification_dm_sync(user_id, notification_message, "email_processed")
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": f"Email processed for user {user_id}"})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing user email: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/add_new_user", methods=["POST"])
def add_new_user():
    """API endpoint for adding a completely new user with points and optional email"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id = data.get('user_id', '').strip()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        points = data.get('points', 0)
        
        if not user_id:
            return jsonify({"success": False, "error": "User ID is required"})
        
        # Basic validation for Discord user ID format
        if not user_id.isdigit() or len(user_id) < 17 or len(user_id) > 19:
            return jsonify({"success": False, "error": "Invalid Discord User ID format"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            message_parts = []
            
            # Check if user already exists in points table
            points_check = loop.run_until_complete(db.execute_query('SELECT balance FROM points WHERE user_id = $1', user_id))
            if points_check:
                return jsonify({"success": False, "error": f"User {user_id} already exists with {points_check[0][0]} points"})
            
            # Add user to points table
            loop.run_until_complete(db.execute_query('''
                INSERT INTO points (user_id, balance, created_at, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', user_id, points))
            message_parts.append(f"✓ Added user with {points:,} points")
            
            # Add initial transaction record if points > 0
            if points > 0:
                loop.run_until_complete(db.execute_query('''
                    INSERT INTO transactions (user_id, amount, transaction_type, admin_id, reason, created_at)
                    VALUES ($1, $2, 'add', 'dashboard_admin', 'Initial points from admin dashboard', CURRENT_TIMESTAMP)
                ''', user_id, points))
                message_parts.append(f"✓ Recorded initial points transaction")
            
            # Add email submission if email provided
            if email:
                # Check if email already exists
                email_check = loop.run_until_complete(db.execute_query('SELECT discord_user_id FROM email_submissions WHERE email_address = $1', email))
                if email_check:
                    message_parts.append(f"⚠️ Email {email} already exists for user {email_check[0][0]}")
                else:
                    loop.run_until_complete(db.execute_query('''
                        INSERT INTO email_submissions (discord_user_id, discord_username, email_address, server_roles, status, submitted_at)
                        VALUES ($1, $2, $3, '', 'pending', CURRENT_TIMESTAMP)
                    ''', user_id, username or f"User {user_id}", email))
                    message_parts.append(f"✓ Added email submission: {email}")
            
            # Add to user_stats table
            loop.run_until_complete(db.execute_query('''
                INSERT INTO user_stats (user_id, total_earned, total_spent, highest_balance, transaction_count, last_activity, created_at)
                VALUES ($1, $2, 0, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', user_id, points, 1 if points > 0 else 0))
            message_parts.append(f"✓ Created user statistics profile")
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({
                "success": True, 
                "message": "\\n".join(message_parts),
                "user_id": user_id,
                "points": points,
                "email": email or None
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error adding new user: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/update_user_profile", methods=["POST"])
def update_user_profile():
    """API endpoint for updating user profile (username and email)"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id = data.get('user_id')
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        
        if not user_id:
            return jsonify({"success": False, "error": "Missing user_id"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Check if user already has an email submission
            check_query = 'SELECT id FROM email_submissions WHERE discord_user_id = $1'
            existing_submission = loop.run_until_complete(db.execute_query(check_query, user_id))
            
            if existing_submission:
                # Update existing email submission
                update_query = '''
                    UPDATE email_submissions 
                    SET discord_username = $1, email_address = $2, 
                        submitted_at = CASE WHEN email_address != $2 THEN CURRENT_TIMESTAMP ELSE submitted_at END,
                        status = CASE WHEN email_address != $2 THEN 'pending' ELSE status END
                    WHERE discord_user_id = $3
                '''
                loop.run_until_complete(db.execute_query(update_query, username, email, user_id))
                message = "User profile updated successfully"
            else:
                # Create new email submission if email is provided
                if email:
                    insert_query = '''
                        INSERT INTO email_submissions (discord_user_id, discord_username, email_address, server_roles, status, submitted_at)
                        VALUES ($1, $2, $3, $4, 'pending', CURRENT_TIMESTAMP)
                    '''
                    loop.run_until_complete(db.execute_query(insert_query, user_id, username, email, ""))
                    message = "User profile created with email submission"
                else:
                    # For username-only updates, we could store in a separate table or just return success
                    # For now, we'll require email to create a submission
                    message = "Username noted (email required for submission)"
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"success": True, "message": message})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/clear_processed_emails", methods=["POST"])
def clear_processed_emails():
    """API endpoint to delete all processed email submissions"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use PostgreSQL database
            from database_postgresql import PostgreSQLPointsDatabase
            db = PostgreSQLPointsDatabase()
            
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Delete processed emails
            delete_query = "DELETE FROM email_submissions WHERE status = 'processed'"
            result = loop.run_until_complete(db.execute_query(delete_query))
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            deleted_count = 0  # PostgreSQL doesn't easily return row count from delete
            
            return jsonify({
                "success": True, 
                "message": f"Deleted {deleted_count} processed email submissions"
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error clearing processed emails: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/send_dm", methods=["POST"])
def send_dm():
    """API endpoint for sending DMs through the web dashboard"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        user_id = data.get('user_id')
        message_type = data.get('message_type', 'general')
        message_content = data.get('message')
        
        if not all([user_id, message_content]):
            return jsonify({"success": False, "error": "Missing required fields"})
        
        # Validate message type
        valid_types = ['general', 'order_status', 'error_alert', 'important']
        if message_type not in valid_types:
            return jsonify({"success": False, "error": "Invalid message type"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Ensure user_id is a string for database operations
            user_id_str = str(user_id)
            
            # Check if user exists and get username
            user_data = loop.run_until_complete(db.execute_query('SELECT user_id FROM points WHERE user_id = $1', user_id_str))
            
            # Use the synchronous DM wrapper instead of complex async logic
            success = send_admin_notification_dm_sync(user_id_str, message_content, message_type)
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"DM sent successfully to user {user_id_str}"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to send DM. Check logs for details."
                })
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error sending DM via dashboard: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/message_history")
def message_history():
    """API endpoint for message history"""
    try:
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get message history from database
            messages_data = loop.run_until_complete(db.execute_query('''
                SELECT id, sender_admin_name, recipient_username, message_content, 
                       message_type, sent_at, delivery_status, delivery_error,
                       sender_admin_id, recipient_user_id
                FROM admin_messages 
                ORDER BY sent_at DESC 
                LIMIT 50
            '''))
            
            # Format messages for API response
            messages = []
            for msg in messages_data:
                messages.append({
                    "id": msg[0],
                    "sender_admin_name": msg[1],
                    "recipient_username": msg[2],
                    "message_content": msg[3],
                    "message_type": msg[4],
                    "sent_at": msg[5].isoformat() if msg[5] else None,
                    "delivery_status": msg[6],
                    "delivery_error": msg[7],
                    "sender_admin_id": msg[8],
                    "recipient_user_id": msg[9]
                })
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"messages": messages})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting message history: {e}")
        return jsonify({"messages": []})

@app.route("/api/message_stats")
def message_stats():
    """API endpoint for message statistics"""
    try:
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get message statistics
            stats_data = loop.run_until_complete(db.execute_query('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN delivery_status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN delivery_status = 'pending' THEN 1 END) as pending
                FROM admin_messages
            '''))
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if stats_data:
                stats = stats_data[0]
                return jsonify({
                    "total": stats[0],
                    "delivered": stats[1],
                    "failed": stats[2],
                    "pending": stats[3]
                })
            else:
                return jsonify({"total": 0, "delivered": 0, "failed": 0, "pending": 0})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        return jsonify({"total": 0, "delivered": 0, "failed": 0, "pending": 0})

@app.route("/api/export_messages")
def export_messages():
    """API endpoint for exporting message history"""
    try:
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Get all messages from database
            messages_data = loop.run_until_complete(db.execute_query('''
                SELECT id, sender_admin_name, sender_admin_id, recipient_username, 
                       recipient_user_id, message_content, message_type, sent_at, 
                       delivery_status, delivery_error
                FROM admin_messages 
                ORDER BY sent_at DESC
            '''))
            
            # Format messages for export
            messages = []
            for msg in messages_data:
                messages.append({
                    "id": msg[0],
                    "sender_admin_name": msg[1],
                    "sender_admin_id": msg[2],
                    "recipient_username": msg[3],
                    "recipient_user_id": msg[4],
                    "message_content": msg[5],
                    "message_type": msg[6],
                    "sent_at": msg[7].isoformat() if msg[7] else None,
                    "delivery_status": msg[8],
                    "delivery_error": msg[9] or ""
                })
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            return jsonify({"messages": messages})
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error exporting messages: {e}")
        return jsonify({"messages": []})

@app.route("/api/lookup_user", methods=["POST"])
def lookup_user():
    """API endpoint for user lookup by email, username, or user ID"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        lookup = data.get('lookup', '').strip()
        if not lookup:
            return jsonify({"success": False, "error": "Lookup value is required"})
        
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Try different lookup methods
            user_data = None
            
            # Method 1: Try exact user ID match
            if lookup.isdigit():
                user_query = '''
                    SELECT DISTINCT 
                        COALESCE(p.user_id, e.discord_user_id) as user_id,
                        COALESCE(e.discord_username, 'User ' || COALESCE(p.user_id, e.discord_user_id)) as username,
                        e.email_address as email,
                        COALESCE(p.balance, 0) as points
                    FROM points p 
                    FULL OUTER JOIN email_submissions e ON p.user_id = e.discord_user_id
                    WHERE COALESCE(p.user_id, e.discord_user_id) = $1
                '''
                result = loop.run_until_complete(db.execute_query(user_query, lookup))
                if result:
                    user_data = result[0]
            
            # Method 2: Try email address match
            if not user_data and '@' in lookup:
                email_query = '''
                    SELECT DISTINCT 
                        COALESCE(p.user_id, e.discord_user_id) as user_id,
                        COALESCE(e.discord_username, 'User ' || COALESCE(p.user_id, e.discord_user_id)) as username,
                        e.email_address as email,
                        COALESCE(p.balance, 0) as points
                    FROM email_submissions e
                    LEFT JOIN points p ON e.discord_user_id = p.user_id
                    WHERE LOWER(e.email_address) = LOWER($1)
                '''
                result = loop.run_until_complete(db.execute_query(email_query, lookup))
                if result:
                    user_data = result[0]
            
            # Method 3: Try username search (case-insensitive, partial match)
            if not user_data:
                username_query = '''
                    SELECT DISTINCT 
                        COALESCE(p.user_id, e.discord_user_id) as user_id,
                        COALESCE(e.discord_username, 'User ' || COALESCE(p.user_id, e.discord_user_id)) as username,
                        e.email_address as email,
                        COALESCE(p.balance, 0) as points
                    FROM email_submissions e
                    LEFT JOIN points p ON e.discord_user_id = p.user_id
                    WHERE LOWER(e.discord_username) LIKE LOWER($1)
                    UNION
                    SELECT DISTINCT 
                        p.user_id,
                        'User ' || p.user_id as username,
                        NULL as email,
                        p.balance as points
                    FROM points p
                    WHERE p.user_id NOT IN (SELECT discord_user_id FROM email_submissions WHERE discord_user_id IS NOT NULL)
                    AND ('User ' || p.user_id) LIKE $1
                    LIMIT 1
                '''
                search_term = f"%{lookup}%"
                result = loop.run_until_complete(db.execute_query(username_query, search_term))
                if result:
                    user_data = result[0]
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            if user_data:
                return jsonify({
                    "success": True,
                    "user": {
                        "user_id": str(user_data[0]),
                        "username": user_data[1],
                        "email": user_data[2],
                        "points": user_data[3]
                    }
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"No user found matching '{lookup}'. Try User ID, exact email address, or username."
                })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in user lookup: {e}")
        return jsonify({"success": False, "error": f"Database error: {str(e)}"})

@app.route("/status")
def status():
    return {
        "status": "online",
        "bot_name": "Pipi-bot",
        "features": ["points_management", "leaderboard", "admin_commands", "web_dashboard", "database_admin", "achievements"],
        "database": "sqlite_enhanced"
    }

@app.route("/health")
def health_check():
    """Health check endpoint for deployment monitoring - always returns 200"""
    try:
        # Basic health check - ensure bot is initialized and database is accessible
        if bot and hasattr(bot, 'user') and bot.user:
            return jsonify({
                "status": "healthy",
                "bot_status": "online",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }), 200
        else:
            # Still return 200 even if bot is starting up for deployment health checks
            return jsonify({
                "status": "healthy",
                "bot_status": "initializing",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }), 200
    except Exception as e:
        # Always return 200 for deployment health checks, log errors separately
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "healthy",
            "bot_status": "running",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "note": "Service operational"
        }), 200

@app.route("/healthz")
def healthz():
    """Alternative health check endpoint for Kubernetes/Cloud Run compatibility"""
    return jsonify({
        "status": "healthy",
        "service": "discord-bot",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200

@app.route("/api/bulk_points", methods=["POST"])
def bulk_points_management():
    """API endpoint for bulk points management with user ID template"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"})
        
        action = data.get('action')  # 'set', 'add', 'remove'
        users_data = data.get('users', [])  # List of {user_id: str, points: int}
        reason = data.get('reason', 'Bulk points operation')
        
        if not action or not users_data:
            return jsonify({"success": False, "error": "Missing action or users data"})
        
        # Connect to database
        from database_postgresql import PostgreSQLPointsDatabase
        db = PostgreSQLPointsDatabase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize database connection
            loop.run_until_complete(db.initialize())
            
            # Process bulk operations
            async def process_bulk_points():
                results = []
                for user_data in users_data:
                    user_id = str(user_data.get('user_id', '')).strip().lstrip("'")  # Remove ' prefix if present
                    points = user_data.get('points', 0)
                    
                    if not user_id or user_id == 'user_id':  # Skip header row if present
                        continue
                    
                    try:
                        points = int(points)
                        
                        # Get current points before operation for better notification messages
                        current_points = await db.get_points(user_id)
                        
                        if action == 'set':
                            success = await db.set_points(user_id, points, admin_id=None, reason=reason)
                            if success:
                                notification_message = f"🔄 **Points Set**\n\nYour points have been set to **{points:,} points**.\n\n📝 **Reason:** {reason or 'Admin adjustment'}"
                                # Use sync wrapper for Flask route context
                                send_admin_notification_dm_sync(user_id, notification_message, "points_set")
                        elif action == 'add':
                            success = await db.update_points(user_id, points, admin_id=None, reason=reason)
                            if success:
                                new_total = current_points + points
                                notification_message = f"➕ **Points Added**\n\nYou received **+{points:,} points**!\n\n💰 **New Total:** {new_total:,} points\n📝 **Reason:** {reason or 'Admin bonus'}"
                                # Use sync wrapper for Flask route context
                                send_admin_notification_dm_sync(user_id, notification_message, "points_added")
                        elif action == 'remove':
                            success = await db.update_points(user_id, -abs(points), admin_id=None, reason=reason)
                            if success:
                                new_total = max(0, current_points - abs(points))
                                notification_message = f"➖ **Points Removed**\n\n**{abs(points):,} points** have been deducted.\n\n💰 **New Total:** {new_total:,} points\n📝 **Reason:** {reason or 'Admin adjustment'}"
                                # Use sync wrapper for Flask route context
                                send_admin_notification_dm_sync(user_id, notification_message, "points_removed")
                        else:
                            success = False
                        
                        results.append({
                            "user_id": user_id,
                            "points": points,
                            "success": success,
                            "action": action
                        })
                    except Exception as e:
                        results.append({
                            "user_id": user_id, 
                            "success": False, 
                            "error": str(e)
                        })
                
                return results
            
            results = loop.run_until_complete(process_bulk_points())
            
            # Close database connection
            loop.run_until_complete(db.close())
            
            # Count successes and failures
            successes = sum(1 for r in results if r.get('success', False))
            failures = len(results) - successes
            
            return jsonify({
                "success": True,
                "results": results,
                "summary": {
                    "total": len(results),
                    "successes": successes,
                    "failures": failures
                },
                "message": f"Bulk {action} operation completed: {successes} successes, {failures} failures"
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in bulk points management: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/bulk_template")
def get_bulk_template():
    """API endpoint to get CSV template for bulk points management"""
    try:
        import csv
        from io import StringIO
        
        # Create template CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['user_id', 'points'])
        
        # Write example rows with ' prefix for user IDs
        writer.writerow(["'495044225994326033", "100"])
        writer.writerow(["'312257111033774090", "150"])
        writer.writerow(["'716944162402074680", "200"])
        
        csv_content = output.getvalue()
        output.close()
        
        # Return as downloadable template
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={"Content-disposition": "attachment; filename=bulk_points_template.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error creating bulk template: {e}")
        return jsonify({"success": False, "error": str(e)})


class PointsBot(commands.Bot):
    def __init__(self):
        # Use only non-privileged intents (slash commands work without message_content)
        intents = discord.Intents.default()
        # Privileged intents disabled - slash commands work without them
        # intents.message_content = True  # Privileged intent
        # intents.members = True  # Privileged intent
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None  # We'll create a custom help command
        )
        
        self.db = PostgreSQLPointsDatabase()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        await self.db.initialize()
        
        # Start periodic presence refresh task
        self.presence_refresh_task = self.loop.create_task(self.periodic_presence_refresh())
        
    async def on_ready(self):
        """Called when the bot has successfully connected to Discord"""
        if self.user:
            logger.info(f'Bot is ready! Logged in as {self.user} (ID: {self.user.id})')
            
            # Multiple attempts to set presence status
            try:
                # First attempt - basic online status
                await self.change_presence(status=discord.Status.online)
                logger.info("Set basic online status")
                
                # Wait a moment then set with activity
                await asyncio.sleep(2)
                activity = discord.Game(name="/pipihelp for commands | /mypoints | /pointsboard")
                await self.change_presence(status=discord.Status.online, activity=activity)
                logger.info("Bot presence set to online with activity status")
                
                # Additional attempt to force presence update
                await asyncio.sleep(1)
                await self.change_presence(status=discord.Status.online, activity=activity)
                logger.info("Presence update confirmed")
                
            except Exception as e:
                logger.error(f"Error setting bot presence: {e}")
            
            # Sync slash commands with retry mechanism
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
                
                # Log each synced command for debugging
                for cmd in synced:
                    logger.info(f"  - /{cmd.name}: {cmd.description}")
                    
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}")
                # Retry once after a delay
                try:
                    await asyncio.sleep(5)
                    synced = await self.tree.sync()
                    logger.info(f"Retry successful: Synced {len(synced)} slash commands")
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
        
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
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for slash commands"""
        logger.error(f"Slash command error in /{interaction.command.name if interaction.command else 'unknown'}: {error}")
        
        try:
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    f"❌ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                    ephemeral=True
                )
            elif isinstance(error, app_commands.MissingPermissions):
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command.",
                    ephemeral=True
                )
            elif isinstance(error, app_commands.BotMissingPermissions):
                await interaction.response.send_message(
                    "❌ Bot is missing required permissions to execute this command.",
                    ephemeral=True
                )
            else:
                # Generic error response
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred while processing this command. Please try again later.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ An error occurred while processing this command. Please try again later.",
                        ephemeral=True
                    )
        except Exception as response_error:
            logger.error(f"Failed to send error response: {response_error}")
    
    async def periodic_presence_refresh(self):
        """Periodically refresh bot presence to ensure it stays online"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                activity = discord.Game(name="/pipihelp for commands | /mypoints | /pointsboard")
                await self.change_presence(status=discord.Status.online, activity=activity)
                logger.debug("Periodic presence refresh completed")
                
                # Refresh every 30 minutes to prevent appearing offline
                await asyncio.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in periodic presence refresh: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error

# Initialize bot
bot = PointsBot()

# Function to store user email (for the privacy slash command)
def send_admin_notification_dm_sync(user_id, message_content, message_type="general"):
    """Synchronous wrapper for sending DM notifications from Flask routes"""
    import asyncio
    from datetime import datetime
    
    async def send_dm_async():
        """Internal async function to handle DM sending"""
        try:
            # Check if bot is ready
            if not bot.is_ready():
                logger.error(f"Bot not ready for DM to user {user_id}")
                return False
                
            # Convert user_id to int for Discord API
            discord_user_id = int(user_id)
            user = bot.get_user(discord_user_id)
            
            if not user:
                try:
                    # Set the bot's event loop context
                    user = await bot.fetch_user(discord_user_id)
                    logger.info(f"Successfully fetched user {user_id} for notification")
                except Exception as e:
                    logger.error(f"Error fetching user {user_id}: {e}")
                    return False
            
            # Store message in database first
            await bot.db.initialize()
            async with bot.db.pool.acquire() as conn:
                message_id = await conn.fetchval('''
                    INSERT INTO admin_messages (sender_admin_id, sender_admin_name, recipient_user_id, message_content, message_type, sent_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                ''', "0", "Dashboard Admin", str(user_id), message_content, message_type, datetime.now())
                
                # Try to send DM
                delivery_status = "pending"
                delivery_error = None
                
                try:
                    await user.send(message_content)
                    delivery_status = "delivered"
                    logger.info(f"✅ DM sent successfully to user {user_id}")
                except Exception as dm_error:
                    delivery_status = "failed"
                    delivery_error = str(dm_error)
                    logger.error(f"❌ Failed to send DM to user {user_id}: {dm_error}")
                
                # Update delivery status (table doesn't have delivered_at column)
                await conn.execute('''
                    UPDATE admin_messages 
                    SET delivery_status = $1, delivery_error = $2
                    WHERE id = $3
                ''', delivery_status, delivery_error, message_id)
                
                return delivery_status == "delivered"
                
        except Exception as e:
            logger.error(f"Error in DM notification: {e}")
            return False
    
    # Use bot's existing event loop if available
    try:
        if bot.loop and not bot.loop.is_closed():
            # Use bot's existing loop
            future = asyncio.run_coroutine_threadsafe(send_dm_async(), bot.loop)
            result = future.result(timeout=30)  # 30 second timeout
            return result
        else:
            # Fallback to new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(send_dm_async())
                return result
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error in sync DM wrapper: {e}")
        return False

async def send_admin_notification_dm(user_id, message_content, message_type="general"):
    """Send DM notification to a user and store in admin_messages table"""
    try:
        # Convert user_id to int for Discord API
        discord_user_id = int(user_id)
        user = bot.get_user(discord_user_id)
        
        if not user:
            try:
                user = await bot.fetch_user(discord_user_id)
                logger.info(f"Successfully fetched user {user_id} for notification")
            except discord.NotFound:
                logger.error(f"User {user_id} not found on Discord (account may be deleted)")
                return False
            except discord.Forbidden:
                logger.error(f"No permission to fetch user {user_id}")
                return False
            except Exception as e:
                logger.error(f"Error fetching user {user_id}: {e}")
                return False
        
        # Store message in database first
        await bot.db.initialize()
        async with bot.db.pool.acquire() as conn:
            message_id = await conn.fetchval('''
                INSERT INTO admin_messages (
                    sender_admin_id, sender_admin_name, recipient_user_id, 
                    recipient_username, message_content, message_type, 
                    delivery_status, sent_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
                RETURNING id
            ''', "0", "System Auto", str(user_id), user.display_name, 
                message_content, message_type, "sending")
        
        # Create embed message
        embed = discord.Embed(
            title=f"📬 {message_type.replace('_', ' ').title()}",
            description=message_content,
            color=discord.Color.blue()
        )
        embed.add_field(
            name="From",
            value="Admin Dashboard (Automated)",
            inline=True
        )
        
        # Try to send the DM
        try:
            # Also try sending a simple test message first to debug
            logger.info(f"Attempting to send DM to user {user_id} ({user.display_name})")
            await user.send(embed=embed)
            
            # Update delivery status to delivered
            async with bot.db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE admin_messages 
                    SET delivery_status = 'delivered' 
                    WHERE id = $1
                ''', message_id)
            
            logger.info(f"Auto DM sent successfully to user {user_id} ({user.display_name}): {message_type}")
            return True
            
        except discord.Forbidden:
            # Update delivery status with error
            async with bot.db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE admin_messages 
                    SET delivery_status = 'failed', delivery_error = 'User has DMs disabled or blocked bot'
                    WHERE id = $1
                ''', message_id)
            
            logger.warning(f"Could not send auto DM to user {user_id} ({user.display_name}): DMs disabled or bot blocked")
            return False
            
        except discord.HTTPException as e:
            # Update delivery status with error  
            async with bot.db.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE admin_messages 
                    SET delivery_status = 'failed', delivery_error = $2
                    WHERE id = $1
                ''', message_id, f"HTTP error: {e}")
            
            logger.error(f"HTTP error sending DM to user {user_id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending auto notification DM to user {user_id}: {e}")
        return False

async def store_user_email(user_id: int, email: str, roles: list = None):
    """Store user email and server roles in database - only one pending submission per user"""
    # Use the bot's PostgreSQL database connection
    await bot.db.initialize()
    
    # Get user info to store proper username
    user = bot.get_user(user_id)
    if not user:
        try:
            user = await bot.fetch_user(user_id)
        except:
            pass
    
    username = user.display_name if user else f"User {user_id}"
    
    # Convert roles list to comma-separated string with fallback
    roles_str = ", ".join(roles) if roles else "Member only"
    
    # Check if user already has ANY email submission (pending or processed)
    existing_query = '''
        SELECT id, status FROM email_submissions 
        WHERE discord_user_id = $1
        ORDER BY submitted_at DESC LIMIT 1
    '''
    existing_result = await bot.db.execute_query(existing_query, user_id)
    existing = existing_result[0] if existing_result else None
    
    if existing:
        submission_id, status = existing
        if status == 'processed':
            raise ValueError("You already have a processed email submission and cannot submit a new one.")
        elif status == 'pending':
            # Update existing pending submission
            update_query = '''
                UPDATE email_submissions 
                SET email_address = $1, discord_username = $2, server_roles = $3, submitted_at = CURRENT_TIMESTAMP
                WHERE id = $4
            '''
            await bot.db.execute_query(update_query, email, username, roles_str, submission_id)
            return f"updated_existing_{submission_id}"
    
    # Insert new submission
    insert_query = '''
        INSERT INTO email_submissions (discord_user_id, discord_username, email_address, server_roles, status)
        VALUES ($1, $2, $3, $4, 'pending')
    '''
    await bot.db.execute_query(insert_query, user_id, username, email, roles_str)
    return "new_submission"

# Slash Commands
@bot.tree.command(name="mypoints", description="Check your points balance (sent privately)")
async def mypoints_slash(interaction: discord.Interaction):
    """Check your points balance via DM"""
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Ensure database is initialized
        if not bot.db.pool:
            await bot.db.initialize()
        
        balance = await bot.db.get_points(str(interaction.user.id))
        
        embed = discord.Embed(
            title="💰 Your Points Balance",
            description=f"You currently have **{balance:,} points**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /pipihelp to see all available commands")
        
        # Use followup since we deferred
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in mypoints slash command: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while checking your points balance.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An error occurred while checking your points balance.", ephemeral=True)
        except Exception as follow_error:
            logger.error(f"Could not send error message: {follow_error}")

@bot.tree.command(name="pointsboard", description="Show the points leaderboard (Admin only)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(limit="Number of users to show (max 25)")
async def pointsboard_slash(interaction: discord.Interaction, limit: int = 10):
    """Show the points leaderboard"""
    try:
        # Acknowledge the interaction immediately to prevent timeout
        await interaction.response.defer()
        
        # Validate limit
        if limit <= 0:
            limit = 10
        elif limit > 25:
            limit = 25
            
        top_users = await bot.db.get_leaderboard(limit)
        
        if not top_users:
            await interaction.followup.send("📊 No users found in the leaderboard.")
            return
            
        embed = discord.Embed(
            title="🏆 Points Leaderboard",
            color=discord.Color.gold()
        )
        
        # Get total stats for overview
        total_users = await bot.db.get_total_users()
        total_points = await bot.db.get_total_points()
        
        description = f"📊 **Database Overview:**\n"
        description += f"👥 Total Users: {total_users:,}\n"
        description += f"💰 Total Points: {total_points:,}\n\n"
        description += f"🏆 **Top {min(limit, len(top_users))} Rankings:**\n"
        
        for i, (user_id, balance) in enumerate(top_users, 1):
            # Convert string user_id to int for Discord API
            try:
                discord_user_id = int(user_id)
            except (ValueError, TypeError):
                username = f"User {user_id}"
            else:
                # Try to get user from the current guild first, then global cache
                user = interaction.guild.get_member(discord_user_id) if interaction.guild else None
                if not user:
                    user = bot.get_user(discord_user_id)
                
                if user:
                    username = user.display_name
                else:
                    # Try to fetch user from Discord API as last resort
                    try:
                        user = await bot.fetch_user(discord_user_id)
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
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in pointsboard slash command: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while fetching the leaderboard.")
            else:
                await interaction.followup.send("❌ An error occurred while fetching the leaderboard.")
        except Exception as follow_error:
            logger.error(f"Could not send error message: {follow_error}")

@bot.tree.command(name="submitemail", description="Submit your email address (visible only to you)")
@app_commands.describe(email="Your email address")
async def submitemail_slash(interaction: discord.Interaction, email: str):
    """Submit your email address with privacy protection"""
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Validate email format
        if not EMAIL_RE.fullmatch(email.strip()):
            await interaction.followup.send(
                "❌ That doesn't look like a valid email. Please try again.",
                ephemeral=True
            )
            return

        # Ensure database is initialized
        if not bot.db.pool:
            await bot.db.initialize()
            
        # Check if user already has a pending submission using PostgreSQL
        existing_query = '''
            SELECT email_address, status FROM email_submissions 
            WHERE discord_user_id = $1
            ORDER BY submitted_at DESC LIMIT 1
        '''
        existing_result = await bot.db.execute_query(existing_query, str(interaction.user.id))
        existing = existing_result[0] if existing_result else None
        
        # Collect user's server roles with enhanced debugging
        user_roles = []
        roles_debug_info = "No guild context"
        
        if interaction.guild:
            try:
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    # Get role names (excluding @everyone)
                    role_names = [role.name for role in member.roles if role.name != "@everyone"]
                    user_roles = role_names
                    roles_debug_info = f"✓ SUCCESS: Found {len(role_names)} roles: {', '.join(role_names)}" if role_names else "✓ SUCCESS: User has no roles (only @everyone)"
                    logger.info(f"✓ Role collection SUCCESS for user {interaction.user.id}: {roles_debug_info}")
                else:
                    roles_debug_info = f"Member not found in guild {interaction.guild.name}"
                    logger.warning(f"Member {interaction.user.id} not found in guild cache, attempting fetch...")
                    # Try to fetch member
                    try:
                        member = await interaction.guild.fetch_member(interaction.user.id)
                        if member:
                            role_names = [role.name for role in member.roles if role.name != "@everyone"]
                            user_roles = role_names
                            roles_debug_info = f"✓ FETCH SUCCESS: Found {len(role_names)} roles: {', '.join(role_names)}" if role_names else "✓ FETCH SUCCESS: Member has no roles (only @everyone)"
                            logger.info(f"✓ Role collection FETCH SUCCESS for user {interaction.user.id}: {roles_debug_info}")
                    except Exception as fetch_error:
                        roles_debug_info = f"✗ FETCH FAILED: {fetch_error}"
                        logger.error(f"✗ Role collection FETCH FAILED for user {interaction.user.id}: {fetch_error}")
                        
            except Exception as e:
                roles_debug_info = f"✗ ERROR: {e}"
                logger.error(f"✗ Role collection ERROR for user {interaction.user.id}: {e}")
        else:
            logger.warning(f"✗ No guild context for user {interaction.user.id} email submission")
        
        # Ensure roles were collected or provide meaningful fallback
        if not user_roles and interaction.guild:
            user_roles = ["Member only"]
            roles_debug_info = "→ Using fallback: Member only"
            logger.info(f"→ Using fallback for user {interaction.user.id}: Member only")
        
        # Store the email with roles (will update if pending, or raise error if processed)
        await store_user_email(str(interaction.user.id), email.strip(), user_roles)

        if existing:
            old_email, status = existing
            if status == 'pending':
                await interaction.followup.send(
                    f"✅ Your email has been updated from `{old_email}` to `{email.strip()}`",
                    ephemeral=True
                )
            else:
                # This shouldn't happen due to the new logic, but just in case
                await interaction.followup.send(
                    "✅ Your email has been successfully submitted, thank you!",
                    ephemeral=True
                )
        else:
            await interaction.followup.send(
                "✅ Your email has been successfully submitted, thank you!",
                ephemeral=True
            )

        # Also send a DM so they have a copy
        try:
            action_word = "updated" if existing and existing[1] == 'pending' else "received"
            await interaction.user.send(f"✅ I have {action_word} your email: {email.strip()}")
        except discord.Forbidden:
            # Could not send DM (maybe DMs are closed)
            pass
            
    except ValueError as e:
        if str(e) == "ALREADY_PROCESSED" or "already have a processed email" in str(e):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ You have already submitted an email that has been processed by admin. "
                    "Each user can only submit one email for verification.",
                    ephemeral=True
                )
        else:
            logger.error(f"ValueError in submitemail slash command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while submitting your email. Please try again later.",
                    ephemeral=True
                )
    except Exception as e:
        logger.error(f"Error in submitemail slash command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ An error occurred while submitting your email. Please try again later.",
                ephemeral=True
            )

@bot.tree.command(name="updateemail", description="Update your previously submitted email address")
@app_commands.describe(email="Your new email address")
async def updateemail_slash(interaction: discord.Interaction, email: str):
    """Update your previously submitted email address"""
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Validate email format
        if not EMAIL_RE.fullmatch(email.strip()):
            await interaction.followup.send(
                "❌ That doesn't look like a valid email. Please try again.",
                ephemeral=True
            )
            return
        # Collect user's current server roles with enhanced debugging
        user_roles = []
        roles_debug_info = "No guild context"
        
        if interaction.guild:
            try:
                member = interaction.guild.get_member(interaction.user.id)
                if member:
                    # Get role names (excluding @everyone)
                    role_names = [role.name for role in member.roles if role.name != "@everyone"]
                    user_roles = role_names
                    roles_debug_info = f"✓ UPDATE SUCCESS: Found {len(role_names)} roles: {', '.join(role_names)}" if role_names else "✓ UPDATE SUCCESS: User has no roles (only @everyone)"
                    logger.info(f"✓ Role collection UPDATE SUCCESS for user {interaction.user.id}: {roles_debug_info}")
                else:
                    roles_debug_info = f"Member not found in guild {interaction.guild.name}"
                    logger.warning(f"Member {interaction.user.id} not found in guild cache for update, attempting fetch...")
                    # Try to fetch member
                    try:
                        member = await interaction.guild.fetch_member(interaction.user.id)
                        if member:
                            role_names = [role.name for role in member.roles if role.name != "@everyone"]
                            user_roles = role_names
                            roles_debug_info = f"✓ UPDATE FETCH SUCCESS: Found {len(role_names)} roles: {', '.join(role_names)}" if role_names else "✓ UPDATE FETCH SUCCESS: Member has no roles (only @everyone)"
                            logger.info(f"✓ Role collection UPDATE FETCH SUCCESS for user {interaction.user.id}: {roles_debug_info}")
                    except Exception as fetch_error:
                        roles_debug_info = f"✗ UPDATE FETCH FAILED: {fetch_error}"
                        logger.error(f"✗ Role collection UPDATE FETCH FAILED for user {interaction.user.id}: {fetch_error}")
                        
            except Exception as e:
                roles_debug_info = f"✗ UPDATE ERROR: {e}"
                logger.error(f"✗ Role collection UPDATE ERROR for user {interaction.user.id}: {e}")
        else:
            logger.warning(f"✗ No guild context for user {interaction.user.id} email update")
            
        # Ensure roles were collected or provide meaningful fallback
        if not user_roles and interaction.guild:
            user_roles = ["Member only"]
            roles_debug_info = "→ Using fallback for update: Member only"
            logger.info(f"→ Using fallback for user {interaction.user.id} update: Member only")
        
        # Ensure database is initialized and connected
        if not bot.db.pool:
            await bot.db.initialize()
        
        # Check if user has an existing submission using PostgreSQL
        async with bot.db.pool.acquire() as conn:
            existing_result = await conn.fetch('''
                SELECT id, email_address FROM email_submissions 
                WHERE discord_user_id = $1 AND status = 'pending'
            ''', str(interaction.user.id))
            
            existing = existing_result[0] if existing_result else None
            
            if not existing:
                await interaction.followup.send(
                    "❌ No email submission found. Use `/submitemail` first.",
                    ephemeral=True
                )
                return
            
            submission_id, old_email = existing[0], existing[1]
            new_email = email.strip().lower()
            
            # Update the email address and server roles using PostgreSQL
            await conn.execute('''
                UPDATE email_submissions 
                SET email_address = $1, submitted_at = CURRENT_TIMESTAMP,
                    server_roles = $2,
                    admin_notes = COALESCE(admin_notes, '') || 'Updated from: ' || $3 || ' | '
                WHERE id = $4
            ''', new_email, ', '.join(user_roles) if user_roles else 'Member only', old_email, submission_id)
            
            await interaction.followup.send(
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
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ An error occurred while updating your email. Please try again later.",
                ephemeral=True
            )

@bot.tree.command(name="myemail", description="Check your current email submission status")
async def myemail_slash(interaction: discord.Interaction):
    """Check your current email submission status - always fetches fresh data"""
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Get email submission data using PostgreSQL
        logger.info(f"Checking email status for user {interaction.user.id}")
        
        # Ensure database is initialized and get connection
        if not bot.db.pool:
            await bot.db.initialize()
            
        async with bot.db.pool.acquire() as conn:
            # Get all submissions for this user to see the full picture
            submissions = await conn.fetch('''
                SELECT id, email_address, submitted_at, status, processed_at, server_roles
                FROM email_submissions 
                WHERE discord_user_id = $1
                ORDER BY submitted_at DESC
            ''', str(interaction.user.id))
            
            submission_list = [tuple(row) for row in submissions]
            logger.info(f"User {interaction.user.id} has {len(submission_list)} total submissions in database")
            
            # Get the most recent submission
            submission = submission_list[0] if submission_list else None
            
            # Debug logging to track what we found
            if submission:
                sub_id, email, submitted_at, status, processed_at, server_roles = submission
                logger.info(f"User {interaction.user.id} latest submission: ID={sub_id}, Email={email}, Status={status}, Processed={processed_at}")
            else:
                logger.info(f"User {interaction.user.id} has no email submissions in database")
        
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
            sub_id, email, submitted_at, status, processed_at, server_roles = submission
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
            
            # Format dates to show only Y-M-D
            if hasattr(submitted_at, 'strftime'):
                submitted_date = submitted_at.strftime('%Y-%m-%d')
            else:
                # Handle string format dates
                submitted_date = str(submitted_at).split()[0] if submitted_at else "Unknown"
            
            embed.add_field(name="Submitted", value=submitted_date, inline=True)
            
            if processed_at:
                if hasattr(processed_at, 'strftime'):
                    processed_date = processed_at.strftime('%Y-%m-%d')
                else:
                    # Handle string format dates
                    processed_date = str(processed_at).split()[0]
                embed.add_field(name="Processed", value=processed_date, inline=True)
            
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
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in myemail slash command: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred while checking your email status.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred while checking your email status.",
                    ephemeral=True
                )
        except Exception:
            pass

@bot.tree.command(name="pipihelp", description="Show help information for all commands")
async def pipihelp_slash(interaction: discord.Interaction):
    """Show help information for all commands"""
    try:
        # Defer the response immediately to prevent timeout
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🤖 Points Bot Help",
            description="Manage member points with these slash commands:",
            color=discord.Color.blue()
        )
        
        # User commands - shown to everyone
        embed.add_field(
            name="👤 Available Commands",
            value="`/mypoints` - Check your points balance (private)\n"
                  "`/submitemail <email>` - Submit order email (private)\n"
                  "`/updateemail <email>` - Update your submitted email\n"
                  "`/myemail` - Check your email submission status\n"
                  "`/pipihelp` - Show this help message",
            inline=False
        )
        
        embed.set_footer(text="Bot made with ❤️ | All personal data is kept private")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in pipihelp slash command: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while showing help information.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An error occurred while showing help information.", ephemeral=True)
        except Exception as follow_error:
            logger.error(f"Could not send pipihelp error message: {follow_error}")

# Admin slash commands
@bot.tree.command(name="status", description="Show bot status and statistics")
@app_commands.default_permissions(administrator=True)
async def status_slash(interaction: discord.Interaction):
    """Show bot status and statistics (Admin only)"""
    try:
        # Defer to prevent timeout
        await interaction.response.defer()
        
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
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in status slash command: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while fetching bot status.")
            else:
                await interaction.followup.send("❌ An error occurred while fetching bot status.")
        except Exception as follow_error:
            logger.error(f"Could not send status error message: {follow_error}")

@bot.tree.command(name="refreshpresence", description="Force refresh bot online status")
@app_commands.default_permissions(administrator=True)
async def refresh_presence_slash(interaction: discord.Interaction):
    """Force refresh bot presence status (Admin only)"""
    try:
        await interaction.response.defer()
        
        # Force multiple presence updates to ensure Discord recognizes the online status
        await bot.change_presence(status=discord.Status.online)
        await asyncio.sleep(1)
        
        activity = discord.Game(name="/pipihelp for commands | /mypoints | /pointsboard")
        await bot.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(1)
        
        # Final confirmation
        await bot.change_presence(status=discord.Status.online, activity=activity)
        
        logger.info("Manual presence refresh executed")
        
        embed = discord.Embed(
            title="✅ Presence Refreshed",
            description="Bot presence status has been manually updated to **Online**",
            color=discord.Color.green()
        )
        embed.add_field(name="Action Taken", value="Multiple presence updates sent to Discord", inline=False)
        embed.add_field(name="Status", value="🟢 Online", inline=True)
        embed.add_field(name="Activity", value="Playing: /pipihelp for commands", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in refresh_presence slash command: {e}")
        await interaction.followup.send("❌ An error occurred while refreshing bot presence.")

@bot.tree.command(name="achievements", description="View user achievements")
@app_commands.describe(user="User to check achievements for (optional)")
async def achievements_slash(interaction: discord.Interaction, user: discord.User = None):
    """View achievements for yourself or another user"""
    try:
        target_user = user or interaction.user
        user_id = str(target_user.id)
        
        # Get user achievements
        achievements = await get_user_achievements(bot.db, user_id)
        
        embed = discord.Embed(
            title=f"🏆 {target_user.display_name}'s Achievements",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        if not achievements:
            embed.description = "No achievements earned yet! Keep using the bot to unlock rewards."
            embed.add_field(
                name="Available Achievements", 
                value="• First Points Earned (50 pts)\n• 100 Points Milestone (25 pts)\n• 500 Points Milestone (75 pts)\n• 1000 Points Milestone (150 pts)\n• High Roller - 2000+ points (300 pts)\n• Email Verified (100 pts)", 
                inline=False
            )
        else:
            total_achievement_points = sum(ach['points_earned'] for ach in achievements)
            
            embed.description = f"**{len(achievements)} achievements earned**\n**{total_achievement_points} bonus points from achievements**\n"
            
            achievement_text = ""
            for ach in achievements:
                achievement_type = ach['achievement_type']
                achievement_data = ACHIEVEMENT_TYPES.get(achievement_type, {})
                emoji = achievement_data.get('emoji', '🏆')
                
                achievement_text += f"{emoji} **{ach['achievement_name']}**\n"
                achievement_text += f"   +{ach['points_earned']} points • {ach['earned_at'].strftime('%b %d, %Y')}\n"
            
            embed.add_field(name="Earned Achievements", value=achievement_text[:1024], inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in achievements slash command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching achievements.")

@bot.tree.command(name="recentachievements", description="View recent achievements earned by all users")
async def recent_achievements_slash(interaction: discord.Interaction):
    """View recent achievements across all users"""
    try:
        recent_achievements = await get_recent_achievements(bot.db, 15)
        
        embed = discord.Embed(
            title="🎉 Recent Achievements",
            color=discord.Color.gold()
        )
        
        if not recent_achievements:
            embed.description = "No achievements earned recently. Be the first!"
        else:
            achievement_text = ""
            for ach in recent_achievements:
                user_id = ach['user_id']
                achievement_type = ach['achievement_type']
                achievement_data = ACHIEVEMENT_TYPES.get(achievement_type, {})
                emoji = achievement_data.get('emoji', '🏆')
                
                # Try to get Discord username
                try:
                    discord_user = bot.get_user(int(user_id))
                    if discord_user:
                        username = discord_user.display_name
                    else:
                        discord_user = await bot.fetch_user(int(user_id))
                        username = discord_user.display_name
                except:
                    username = f"User {user_id}"
                
                achievement_text += f"{emoji} **{username}** earned **{ach['achievement_name']}**\n"
                achievement_text += f"   +{ach['points_earned']} points • {ach['earned_at'].strftime('%b %d')}\n\n"
                
                if len(achievement_text) > 1500:  # Prevent embed overflow
                    break
            
            embed.description = achievement_text
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in recent achievements slash command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching recent achievements.")

@bot.tree.command(name="checkemail", description="Admin: Check any user's email submission status")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(user="Discord user to check email status for")
async def check_email_admin_slash(interaction: discord.Interaction, user: discord.User):
    """Admin command to check any user's email submission status"""
    try:
        # Use PostgreSQL instead of SQLite
        await bot.db.initialize()
        
        # Get all submissions for the specified user using PostgreSQL
        async with bot.db.pool.acquire() as conn:
            submissions = await conn.fetch('''
                SELECT id, email_address, submitted_at, status, processed_at, admin_notes, server_roles
                FROM email_submissions 
                WHERE discord_user_id = $1
                ORDER BY submitted_at DESC
            ''', str(user.id))
            
        embed = discord.Embed(
            title=f"📧 Email Status for {user.display_name}",
            description=f"User ID: {user.id}",
            color=discord.Color.blue()
        )
        
        if not submissions:
            embed.add_field(
                name="Status", 
                value="❌ No email submissions found", 
                inline=False
            )
        else:
            for i, submission in enumerate(submissions):
                sub_id, email, submitted_at, status, processed_at, admin_notes = submission[:6]  # Handle variable length tuples
                server_roles = submission[6] if len(submission) > 6 else 'Not collected'
                
                status_emoji = "✅" if status == 'processed' else "⏳" if status == 'pending' else "❌"
                
                embed.add_field(
                    name=f"Submission #{i+1} (ID: {sub_id})",
                    value=f"**Email:** {email}\n"
                          f"**Status:** {status_emoji} {status.title()}\n"
                          f"**Submitted:** {submitted_at}\n" +
                          (f"**Processed:** {processed_at}\n" if processed_at else "") +
                          (f"**Notes:** {admin_notes}\n" if admin_notes else ""),
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in checkemail admin command: {e}")
        await interaction.response.send_message("❌ An error occurred while checking email status.")


@bot.tree.command(name="viewmessages", description="Admin: View sent DM message history")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    user="Optional: Filter by specific user",
    message_type="Optional: Filter by message type",
    limit="Number of messages to show (default 10)"
)
@app_commands.choices(message_type=[
    app_commands.Choice(name="All Types", value="all"),
    app_commands.Choice(name="General", value="general"),
    app_commands.Choice(name="Order Status", value="order_status"),
    app_commands.Choice(name="Error Alert", value="error_alert"),
    app_commands.Choice(name="Important Notice", value="important")
])
async def view_messages_slash(interaction: discord.Interaction, user: discord.User = None, message_type: str = "all", limit: int = 10):
    """Admin command to view DM message history from database"""
    try:
        await bot.db.initialize()
        
        # Build query based on filters
        query = '''
            SELECT id, sender_admin_name, recipient_username, message_content, 
                   message_type, sent_at, delivery_status, delivery_error
            FROM admin_messages 
        '''
        params = []
        conditions = []
        
        if user:
            conditions.append("recipient_user_id = $" + str(len(params) + 1))
            params.append(str(user.id))
            
        if message_type and message_type != "all":
            conditions.append("message_type = $" + str(len(params) + 1))
            params.append(message_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY sent_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with bot.db.pool.acquire() as conn:
            messages = await conn.fetch(query, *params)
        
        if not messages:
            embed = discord.Embed(
                title="📬 No Messages Found",
                description="No admin messages match your criteria.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="📬 Admin Message History",
                description=f"Showing {len(messages)} messages",
                color=discord.Color.blue()
            )
            
            for msg in messages:
                msg_id, admin_name, recipient, content, msg_type, sent_at, status, error = msg
                
                status_emoji = "✅" if status == "delivered" else "❌" if status == "failed" else "⏳"
                
                field_value = f"**To:** {recipient}\n"
                field_value += f"**Type:** {msg_type.replace('_', ' ').title()}\n"
                field_value += f"**Status:** {status_emoji} {status.title()}\n"
                field_value += f"**Content:** {content[:100]}{'...' if len(content) > 100 else ''}\n"
                if error:
                    field_value += f"**Error:** {error}\n"
                field_value += f"**Sent:** {sent_at.strftime('%Y-%m-%d %H:%M')}"
                
                embed.add_field(
                    name=f"Message #{msg_id} by {admin_name}",
                    value=field_value,
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in viewmessages command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while retrieving message history.",
            ephemeral=True
        )

# Web Interface with admin dashboard continues below...
# All old prefix commands have been replaced with modern slash commands above






# Flask web server runner
def run_flask():
    # Use PORT environment variable for deployment, fallback to 5000 for Replit
    port = int(os.getenv('PORT', 5000))
    # For Replit external access, use 0.0.0.0
    host = '0.0.0.0'
    logger.info(f'Starting Flask server on {host}:{port}')
    try:
        app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f'Port {port} is in use, Flask server startup failed but continuing with Discord bot')
        else:
            logger.error(f'Flask server failed to start: {e}')
            raise

def main():
    """Main application entry point with enhanced error handling and proper startup"""
    try:
        # Load environment variables from .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info('Environment variables loaded from .env file')
        except ImportError:
            logger.info('python-dotenv not available, using system environment variables only')
        
        # Validate configuration
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'your_bot_token_here':
            logger.error('Bot token not configured! Please set BOT_TOKEN environment variable.')
            return
        
        # Start Flask web server in a daemon thread first
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info('Flask web server started on port 5000')
        
        # Run Discord bot in asyncio event loop
        async def start_bot():
            try:
                async with bot:
                    logger.info('Starting Discord bot...')
                    await bot.start(Config.BOT_TOKEN)
            except discord.LoginFailure:
                logger.error('Failed to login to Discord. Please check your BOT_TOKEN.')
            except discord.HTTPException as e:
                logger.error(f'Discord HTTP error: {e}')
            except Exception as e:
                logger.error(f'Unexpected error starting bot: {e}')
                raise
            finally:
                if bot.db:
                    try:
                        await bot.db.close()
                    except Exception as e:
                        logger.error(f'Error closing database: {e}')
        
        # Start the bot
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        logger.info('Bot shutdown requested by user')
    except Exception as e:
        logger.error(f'Critical error in main execution: {e}')
        raise

if __name__ == '__main__':
    main()
