import discord
from discord.ext import commands
import logging
import asyncio
import sys
import threading
from flask import Flask, request, jsonify
from config import Config
from database import PointsDatabase

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
                    <h3>⚡ Quick Commands</h3>
                    <p><strong>!silentadd @user 100</strong> - Add points quietly</p>
                    <p><strong>!silentremove @user 50</strong> - Remove points quietly</p>
                    <p><strong>!pointsboard</strong> - View leaderboard</p>
                    <p><strong>!pipihelp</strong> - Show all commands</p>
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
                <a href="#" onclick="showSection('points')" class="active">Points Management</a>
                <a href="#" onclick="showSection('database')">Database Admin</a>
                <a href="#" onclick="showSection('achievements')">Achievements</a>
                <a href="#" onclick="showSection('analytics')">Analytics</a>
            </div>
            
            <!-- Points Management Section -->
            <div id="points-section">
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
        logger.info(f'Bot is ready! Logged in as {self.user} (ID: {self.user.id})')
        
        # Set bot status
        activity = discord.Game(name=f"{Config.COMMAND_PREFIX}pipihelp for commands")
        await self.change_presence(activity=activity)
        
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

@bot.command(name='points', aliases=['balance', 'p'])
async def check_points(ctx, member: discord.Member = None):
    """Check your points balance or another user's balance"""
    try:
        # If no member specified, check the command author's points
        target_user = member or ctx.author
        
        balance = await bot.db.get_points(target_user.id)
        
        if target_user == ctx.author:
            embed = discord.Embed(
                title="💰 Your Points Balance",
                description=f"You currently have **{balance:,} points**",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="💰 Points Balance",
                description=f"{target_user.mention} has **{balance:,} points**",
                color=discord.Color.blue()
            )
            
        embed.set_thumbnail(url=target_user.display_avatar.url)
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in check_points command: {e}")
        await ctx.send("❌ An error occurred while checking points balance.")

@bot.command(name='addpoints', aliases=['add'])
@commands.has_permissions(administrator=True)
async def add_points(ctx, member: discord.Member, amount: int):
    """Add points to a member (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        if amount > 1000000:  # Reasonable upper limit
            await ctx.send("❌ Point amount is too large. Maximum allowed is 1,000,000 points per transaction.")
            return
            
        # Add points
        await bot.db.update_points(member.id, amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Create success embed
        embed = discord.Embed(
            title="✅ Points Added Successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Added", value=f"{amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} added {amount} points to {member} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in add_points command: {e}")
        await ctx.send("❌ An error occurred while adding points.")

@bot.command(name='silentadd', aliases=['sadd'])
@commands.has_permissions(administrator=True)
async def silent_add_points(ctx, member: discord.Member, amount: int):
    """Silently add points to a member without notifications (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        if amount > 1000000:
            await ctx.send("❌ Point amount is too large. Maximum allowed is 1,000,000 points per transaction.")
            return
            
        # Add points silently
        await bot.db.update_points(member.id, amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Send confirmation only to admin (no mention)
        await ctx.send(f"✅ Silently added {amount:,} points to {member.display_name}. New balance: {new_balance:,}")
        logger.info(f"Admin {ctx.author} silently added {amount} points to {member.display_name} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in silent_add_points command: {e}")
        await ctx.send("❌ An error occurred while adding points.")

@bot.command(name='silentremove', aliases=['sremove'])
@commands.has_permissions(administrator=True)
async def silent_remove_points(ctx, member: discord.Member, amount: int):
    """Silently remove points from a member without notifications (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        current_balance = await bot.db.get_points(member.id)
        
        if current_balance < amount:
            await ctx.send(f"⚠️ {member.display_name} only has {current_balance:,} points. Cannot remove {amount:,} points.")
            return
            
        # Remove points silently
        await bot.db.update_points(member.id, -amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Send confirmation only to admin (no mention)
        await ctx.send(f"✅ Silently removed {amount:,} points from {member.display_name}. New balance: {new_balance:,}")
        logger.info(f"Admin {ctx.author} silently removed {amount} points from {member.display_name} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in silent_remove_points command: {e}")
        await ctx.send("❌ An error occurred while removing points.")

@bot.command(name='removepoints', aliases=['remove', 'subtract'])
@commands.has_permissions(administrator=True)
async def remove_points(ctx, member: discord.Member, amount: int):
    """Remove points from a member (Admin only)"""
    try:
        # Validate amount
        if amount <= 0:
            await ctx.send("❌ Point amount must be a positive number.")
            return
            
        current_balance = await bot.db.get_points(member.id)
        
        # Check if user has enough points
        if current_balance < amount:
            embed = discord.Embed(
                title="⚠️ Insufficient Points",
                description=f"{member.mention} only has **{current_balance:,} points**.\nCannot remove **{amount:,} points**.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
            
        # Remove points
        await bot.db.update_points(member.id, -amount)
        new_balance = await bot.db.get_points(member.id)
        
        # Create success embed
        embed = discord.Embed(
            title="❌ Points Removed Successfully",
            color=discord.Color.red()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Removed", value=f"{amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} removed {amount} points from {member} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in remove_points command: {e}")
        await ctx.send("❌ An error occurred while removing points.")

@bot.command(name='setpoints', aliases=['set'])
@commands.has_permissions(administrator=True)
async def set_points(ctx, member: discord.Member, amount: int):
    """Set a member's points to a specific amount (Admin only)"""
    try:
        # Validate amount
        if amount < 0:
            await ctx.send("❌ Point amount cannot be negative.")
            return
            
        if amount > 10000000:  # Reasonable upper limit
            await ctx.send("❌ Point amount is too large. Maximum allowed is 10,000,000 points.")
            return
            
        # Set points
        await bot.db.set_points(member.id, amount)
        
        # Create success embed
        embed = discord.Embed(
            title="🔧 Points Set Successfully",
            color=discord.Color.purple()
        )
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Points Set To", value=f"{amount:,}", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author} set {member}'s points to {amount} (ID: {member.id})")
        
    except Exception as e:
        logger.error(f"Error in set_points command: {e}")
        await ctx.send("❌ An error occurred while setting points.")

@bot.command(name='pointsboard', aliases=['top', 'lb'])
async def leaderboard(ctx, limit: int = 10):
    """Show the points leaderboard"""
    try:
        # Validate limit
        if limit <= 0:
            limit = 10
        elif limit > 25:
            limit = 25
            
        top_users = await bot.db.get_leaderboard(limit)
        
        if not top_users:
            await ctx.send("📊 No users found in the leaderboard.")
            return
            
        embed = discord.Embed(
            title="🏆 Points Leaderboard",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, (user_id, balance) in enumerate(top_users, 1):
            # Try to get user from the current guild first, then global cache
            user = ctx.guild.get_member(user_id) if ctx.guild else None
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
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in leaderboard command: {e}")
        await ctx.send("❌ An error occurred while fetching the leaderboard.")

@bot.command(name='pipihelp', aliases=['ph'])
async def help_command(ctx):
    """Show help information for all commands"""
    embed = discord.Embed(
        title="🤖 Points Bot Help",
        description="Manage member points with these commands:",
        color=discord.Color.blue()
    )
    
    # User commands
    embed.add_field(
        name="👤 User Commands",
        value=f"`{Config.COMMAND_PREFIX}points [@user]` - Check your points or another user's points\n"
              f"`{Config.COMMAND_PREFIX}pointsboard [limit]` - Show points leaderboard",
        inline=False
    )
    
    # Admin commands
    embed.add_field(
        name="👑 Admin Commands",
        value=f"`{Config.COMMAND_PREFIX}addpoints @user <amount>` - Add points to a user\n"
              f"`{Config.COMMAND_PREFIX}silentadd @user <amount>` - Add points silently\n"
              f"`{Config.COMMAND_PREFIX}removepoints @user <amount>` - Remove points from a user\n"
              f"`{Config.COMMAND_PREFIX}silentremove @user <amount>` - Remove points silently\n"
              f"`{Config.COMMAND_PREFIX}setpoints @user <amount>` - Set user's points to specific amount",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Information",
        value="• Admin commands require Administrator permission\n"
              "• Points cannot go below 0\n"
              "• Use command aliases for faster typing",
        inline=False
    )
    
    embed.set_footer(text=f"Bot made with ❤️ | Prefix: {Config.COMMAND_PREFIX}")
    
    await ctx.send(embed=embed)

@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def bot_status(ctx):
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
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in bot_status command: {e}")
        await ctx.send("❌ An error occurred while fetching bot status.")

@bot.command(name='listusers')
@commands.has_permissions(administrator=True)
async def list_users(ctx):
    """List all server members for debugging (Admin only)"""
    try:
        members_list = []
        for member in ctx.guild.members:
            if not member.bot:  # Skip bots
                members_list.append(f"**{member.display_name}** (username: {member.name})")
        
        if not members_list:
            await ctx.send("No members found in this server.")
            return
            
        # Split into chunks if too many users
        chunk_size = 10
        for i in range(0, len(members_list), chunk_size):
            chunk = members_list[i:i + chunk_size]
            
            embed = discord.Embed(
                title=f"👥 Server Members ({i+1}-{min(i+chunk_size, len(members_list))} of {len(members_list)})",
                description="\n".join(chunk),
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)
            
            if len(members_list) > chunk_size and i + chunk_size < len(members_list):
                await asyncio.sleep(1)  # Small delay between messages
        
    except Exception as e:
        logger.error(f"Error in list_users command: {e}")
        await ctx.send("❌ An error occurred while listing users.")

async def main():
    """Main function to run the bot"""
    try:
        # Validate bot token
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == "your_bot_token_here":
            logger.error("Bot token not configured! Please set BOT_TOKEN in your environment variables.")
            return
            
        # Start Flask web server in a separate thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("Flask web server started on port 5000")
            
        # Start the bot
        async with bot:
            await bot.start(Config.BOT_TOKEN)
            
    except discord.LoginFailure:
        logger.error("Failed to login - Invalid bot token!")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Close database connection
        if bot.db:
            await bot.db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
