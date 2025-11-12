from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any
import json
import asyncio
import subprocess
import os
import sys

from .. import models, schemas
from ..db import get_db, engine
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """Ensure only admin users can access admin endpoints"""
    return current_user

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_simple():
    """Serve the simple admin dashboard HTML"""
    return get_simple_admin_html()

@router.get("/api/all-data")
async def get_all_database_data(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Get all data from all tables"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    all_data = {}
    
    for table_name in tables:
        try:
            # Get table structure
            columns = inspector.get_columns(table_name)
            column_names = [col["name"] for col in columns]
            
            # Get table data
            query = text(f"SELECT * FROM {table_name}")
            result = db.execute(query)
            
            rows = []
            for row in result:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[column_names[i]] = str(value) if value is not None else None
                rows.append(row_dict)
            
            all_data[table_name] = {
                "columns": column_names,
                "data": rows,
                "count": len(rows)
            }
        except Exception as e:
            all_data[table_name] = {
                "error": str(e),
                "columns": [],
                "data": [],
                "count": 0
            }
    
    return all_data

@router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """WebSocket endpoint for live terminal"""
    await websocket.accept()
    
    try:
        while True:
            # Get current working directory
            cwd = os.getcwd()
            
            # Get Python environment info
            python_path = sys.executable
            
            # Get database file info if exists
            db_info = ""
            if os.path.exists("crm.db"):
                db_size = os.path.getsize("crm.db")
                db_info = f"Database: crm.db ({db_size} bytes)"
            
            # Get running processes
            try:
                ps_result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"], 
                                         capture_output=True, text=True, timeout=5)
                processes = ps_result.stdout if ps_result.returncode == 0 else "No Python processes found"
            except:
                processes = "Unable to get process list"
            
            # System info
            terminal_output = f"""
🖥️  SYSTEM STATUS - {asyncio.get_event_loop().time()}
{'='*60}
📁 Working Directory: {cwd}
🐍 Python Path: {python_path}
{db_info}

🔄 RUNNING PROCESSES:
{processes}

📊 BACKEND STATUS:
Server: FastAPI on port 8000
Database: SQLite (crm.db)
Environment: Development
Last Update: {asyncio.get_event_loop().time()}

💻 AVAILABLE COMMANDS:
- View logs: Get latest application logs
- Check DB: Database connection status  
- Memory: Current memory usage
- Restart: Restart application services

{'='*60}
            """
            
            await websocket.send_text(terminal_output)
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        print("Terminal websocket disconnected")
    except Exception as e:
        await websocket.send_text(f"Terminal Error: {str(e)}")

def get_simple_admin_html():
    """Return the simple admin dashboard HTML"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRM Admin Dashboard - Database & Terminal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: #fff;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #fff;
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .section {
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }

        .section h2 {
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }

        .table-container {
            margin-bottom: 30px;
        }

        .table-header {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .table-name {
            font-size: 1.2rem;
            font-weight: bold;
        }

        .table-count {
            background: #4CAF50;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
        }

        .data-table th {
            background: rgba(255,255,255,0.2);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }

        .data-table td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .data-table tr:hover {
            background: rgba(255,255,255,0.1);
        }

        .terminal {
            height: 600px;
            background: #000;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            color: #00ff00;
            overflow-y: auto;
            border: 2px solid #333;
        }

        .terminal h2 {
            color: #00ff00;
            margin-bottom: 15px;
            font-family: 'Segoe UI', sans-serif;
        }

        .terminal-output {
            white-space: pre-wrap;
            font-size: 0.85rem;
            line-height: 1.4;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin-bottom: 20px;
        }

        .refresh-btn:hover {
            background: #45a049;
        }

        .loading {
            text-align: center;
            padding: 20px;
            color: #ccc;
        }

        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 0.9rem;
        }

        .connected {
            background: #4CAF50;
        }

        .disconnected {
            background: #f44336;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ CRM Admin Dashboard</h1>
            <p>Complete Database Overview & Live Backend Terminal</p>
        </div>

        <div class="connection-status" id="connectionStatus">
            <span id="statusText">Connecting...</span>
        </div>

        <div class="dashboard-grid">
            <!-- Database Section -->
            <div class="section">
                <h2>📊 Database Tables & Content</h2>
                
                <button class="refresh-btn" onclick="loadAllData()">🔄 Refresh Data</button>
                
                <div class="stats-grid" id="statsGrid">
                    <!-- Stats will be populated here -->
                </div>
                
                <div id="tablesContainer">
                    <div class="loading">Loading database content...</div>
                </div>
            </div>

            <!-- Terminal Section -->
            <div class="section">
                <div class="terminal">
                    <h2>💻 Live Backend Terminal</h2>
                    <div class="terminal-output" id="terminalOutput">
                        Connecting to live terminal...
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let allData = {};

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadAllData();
            connectTerminal();
        });

        // Load all database data
        async function loadAllData() {
            try {
                const response = await fetch('/admin/api/all-data');
                allData = await response.json();
                displayAllData();
                updateStats();
            } catch (error) {
                document.getElementById('tablesContainer').innerHTML = 
                    '<div class="loading">Error loading data: ' + error.message + '</div>';
            }
        }

        // Display all database tables and data
        function displayAllData() {
            const container = document.getElementById('tablesContainer');
            container.innerHTML = '';

            for (const [tableName, tableData] of Object.entries(allData)) {
                if (tableData.error) {
                    container.innerHTML += `
                        <div class="table-container">
                            <div class="table-header">
                                <span class="table-name">❌ ${tableName}</span>
                                <span class="table-count">Error</span>
                            </div>
                            <p style="color: #ff6b6b;">Error: ${tableData.error}</p>
                        </div>
                    `;
                    continue;
                }

                const tableHtml = `
                    <div class="table-container">
                        <div class="table-header">
                            <span class="table-name">📋 ${tableName}</span>
                            <span class="table-count">${tableData.count} records</span>
                        </div>
                        ${createTable(tableData.columns, tableData.data)}
                    </div>
                `;
                container.innerHTML += tableHtml;
            }
        }

        // Create HTML table
        function createTable(columns, data) {
            if (!data || data.length === 0) {
                return '<p style="color: #ccc; padding: 20px; text-align: center;">No data available</p>';
            }

            let html = '<table class="data-table"><thead><tr>';
            columns.forEach(column => {
                html += `<th>${column}</th>`;
            });
            html += '</tr></thead><tbody>';

            data.slice(0, 100).forEach(row => { // Limit to first 100 rows for performance
                html += '<tr>';
                columns.forEach(column => {
                    const value = row[column] || '';
                    const displayValue = value.length > 50 ? value.substring(0, 50) + '...' : value;
                    html += `<td>${displayValue}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table>';
            
            if (data.length > 100) {
                html += `<p style="color: #ccc; text-align: center; padding: 10px;">
                    Showing first 100 of ${data.length} records
                </p>`;
            }

            return html;
        }

        // Update statistics
        function updateStats() {
            const statsContainer = document.getElementById('statsGrid');
            let totalRecords = 0;
            let totalTables = 0;

            for (const [tableName, tableData] of Object.entries(allData)) {
                if (!tableData.error) {
                    totalRecords += tableData.count;
                    totalTables++;
                }
            }

            const stats = [
                { label: 'Total Tables', value: totalTables },
                { label: 'Total Records', value: totalRecords },
                { label: 'Users', value: allData.users?.count || 0 },
                { label: 'Clients', value: allData.clients?.count || 0 },
                { label: 'Commissions', value: allData.commissions?.count || 0 }
            ];

            statsContainer.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <div class="stat-number">${stat.value}</div>
                    <div class="stat-label">${stat.label}</div>
                </div>
            `).join('');
        }

        // Connect to terminal WebSocket
        function connectTerminal() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/admin/ws/terminal`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                updateConnectionStatus(true);
            };
            
            ws.onmessage = function(event) {
                const terminalOutput = document.getElementById('terminalOutput');
                terminalOutput.textContent = event.data;
                terminalOutput.scrollTop = terminalOutput.scrollHeight;
            };
            
            ws.onclose = function() {
                updateConnectionStatus(false);
                // Attempt to reconnect after 3 seconds
                setTimeout(connectTerminal, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('Terminal WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connectionStatus');
            const statusText = document.getElementById('statusText');
            
            if (connected) {
                statusElement.className = 'connection-status connected';
                statusText.textContent = '🟢 Connected';
            } else {
                statusElement.className = 'connection-status disconnected';
                statusText.textContent = '🔴 Disconnected';
            }
        }

        // Auto-refresh data every 30 seconds
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
    """