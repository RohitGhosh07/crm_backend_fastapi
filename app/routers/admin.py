from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, MetaData
from typing import List, Dict, Any
import json

from .. import models, schemas
from ..db import get_db, engine
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """Ensure only admin users can access admin endpoints"""
    # For demo purposes, all authenticated users are admin
    # In production, add proper role checking
    return current_user


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(admin_user: models.User = Depends(get_admin_user)):
    """Serve the admin dashboard HTML"""
    return get_admin_html()


@router.get("/api/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Get dashboard statistics"""
    
    # Get counts
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    total_clients = db.query(models.Client).count()
    total_commissions = db.query(models.Commission).count()
    
    # Get total commission amount
    total_commission_amount = db.query(models.Commission).with_entities(
        text("SUM(amount)")
    ).scalar() or 0
    
    # Get recent activity
    recent_users = db.query(models.User).order_by(models.User.created_at.desc()).limit(5).all()
    recent_clients = db.query(models.Client).order_by(models.Client.created_at.desc()).limit(5).all()
    recent_commissions = db.query(models.Commission).order_by(models.Commission.created_at.desc()).limit(5).all()
    
    return {
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "total_clients": total_clients,
            "total_commissions": total_commissions,
            "total_commission_amount": float(total_commission_amount)
        },
        "recent_activity": {
            "recent_users": [{"id": u.id, "name": u.name, "email": u.email, "created_at": u.created_at} for u in recent_users],
            "recent_clients": [{"id": c.id, "name": c.name, "email": c.email, "created_at": c.created_at} for c in recent_clients],
            "recent_commissions": [{"id": co.id, "client_id": co.client_id, "amount": float(co.amount), "created_at": co.created_at} for co in recent_commissions]
        }
    }


@router.get("/api/database/structure")
async def get_database_structure(admin_user: models.User = Depends(get_admin_user)):
    """Get complete database structure"""
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    structure = {}
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        structure[table_name] = {
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "primary_key": col.get("primary_key", False),
                    "autoincrement": col.get("autoincrement", False),
                    "default": str(col.get("default")) if col.get("default") else None
                }
                for col in columns
            ],
            "foreign_keys": [
                {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                }
                for fk in foreign_keys
            ],
            "indexes": [
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"]
                }
                for idx in indexes
            ]
        }
    
    return {"tables": structure}


@router.get("/api/tables/{table_name}")
async def get_table_data(
    table_name: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Get data from any table"""
    
    # Validate table exists
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Get table data
    query = text(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {skip}")
    result = db.execute(query)
    
    # Get column names
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    
    # Convert to list of dictionaries
    rows = []
    for row in result:
        row_dict = {}
        for i, value in enumerate(row):
            row_dict[columns[i]] = str(value) if value is not None else None
        rows.append(row_dict)
    
    # Get total count
    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
    total_count = db.execute(count_query).scalar()
    
    return {
        "table_name": table_name,
        "columns": columns,
        "data": rows,
        "total_count": total_count,
        "showing": len(rows)
    }


@router.post("/api/sql/execute")
async def execute_sql(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Execute custom SQL queries (READ ONLY)"""
    
    sql_query = request_data.get("query", "").strip()
    
    if not sql_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Basic safety check - only allow SELECT statements
    if not sql_query.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    try:
        result = db.execute(text(sql_query))
        
        # Get column names
        columns = list(result.keys()) if result.keys() else []
        
        # Convert to list of dictionaries
        rows = []
        for row in result:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(columns):
                    row_dict[columns[i]] = str(value) if value is not None else None
            rows.append(row_dict)
        
        return {
            "success": True,
            "columns": columns,
            "data": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution error: {str(e)}")


@router.get("/api/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Get all users with pagination"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    total_count = db.query(models.User).count()
    
    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "is_active": u.is_active,
                "created_at": u.created_at
            }
            for u in users
        ],
        "total_count": total_count
    }


@router.get("/api/commissions")
async def get_all_commissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    """Get all commissions with client details"""
    commissions = db.query(models.Commission).join(models.Client).offset(skip).limit(limit).all()
    total_count = db.query(models.Commission).count()
    
    result = []
    for commission in commissions:
        client = db.query(models.Client).filter(models.Client.id == commission.client_id).first()
        result.append({
            "id": commission.id,
            "client_id": commission.client_id,
            "client_name": client.name if client else "Unknown",
            "amount": float(commission.amount),
            "source": commission.source,
            "created_at": commission.created_at
        })
    
    return {
        "commissions": result,
        "total_count": total_count
    }


def get_admin_html():
    """Return the complete admin dashboard HTML"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRM Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card { backdrop-filter: blur(10px); }
        .glass { background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.18); }
        .sidebar-item:hover { background: rgba(255, 255, 255, 0.1); transform: translateX(5px); }
        .sidebar-item { transition: all 0.3s ease; }
        .stat-card { background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%); }
    </style>
</head>
<body class="bg-gray-100 gradient-bg min-h-screen" x-data="adminDashboard()">
    
    <!-- Navigation -->
    <nav class="bg-white shadow-lg border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <i class="fas fa-shield-alt text-indigo-600 text-2xl mr-3"></i>
                    <h1 class="text-xl font-bold text-gray-900">CRM Admin Dashboard</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-sm text-gray-700">Welcome, Admin</span>
                    <div class="h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-white text-xs"></i>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <div class="flex h-screen bg-gray-100">
        <!-- Sidebar -->
        <div class="w-64 glass shadow-xl border-r border-white border-opacity-20">
            <div class="p-6">
                <nav class="space-y-2">
                    <a href="#" @click="activeTab = 'dashboard'" 
                       :class="activeTab === 'dashboard' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-chart-line mr-3"></i>
                        Dashboard
                    </a>
                    
                    <a href="#" @click="activeTab = 'database'" 
                       :class="activeTab === 'database' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-database mr-3"></i>
                        Database Structure
                    </a>
                    
                    <a href="#" @click="activeTab = 'users'" 
                       :class="activeTab === 'users' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-users mr-3"></i>
                        Users
                    </a>
                    
                    <a href="#" @click="activeTab = 'clients'" 
                       :class="activeTab === 'clients' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-address-book mr-3"></i>
                        Clients
                    </a>
                    
                    <a href="#" @click="activeTab = 'commissions'" 
                       :class="activeTab === 'commissions' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-money-bill-wave mr-3"></i>
                        Commissions
                    </a>
                    
                    <a href="#" @click="activeTab = 'sql'" 
                       :class="activeTab === 'sql' ? 'bg-white bg-opacity-20' : ''"
                       class="sidebar-item flex items-center px-4 py-3 text-white rounded-lg">
                        <i class="fas fa-terminal mr-3"></i>
                        SQL Terminal
                    </a>
                </nav>
            </div>
        </div>

        <!-- Main Content -->
        <div class="flex-1 overflow-auto">
            <div class="p-8">
                
                <!-- Dashboard Tab -->
                <div x-show="activeTab === 'dashboard'" x-transition>
                    <div class="mb-8">
                        <h2 class="text-3xl font-bold text-white mb-2">Dashboard Overview</h2>
                        <p class="text-white text-opacity-80">Monitor your CRM system performance</p>
                    </div>

                    <!-- Stats Cards -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <div class="stat-card rounded-xl p-6 text-white">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-white text-opacity-80 text-sm">Total Users</p>
                                    <p class="text-2xl font-bold" x-text="stats.total_users || 0"></p>
                                </div>
                                <i class="fas fa-users text-white text-opacity-50 text-3xl"></i>
                            </div>
                        </div>
                        
                        <div class="stat-card rounded-xl p-6 text-white">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-white text-opacity-80 text-sm">Active Users</p>
                                    <p class="text-2xl font-bold" x-text="stats.active_users || 0"></p>
                                </div>
                                <i class="fas fa-user-check text-white text-opacity-50 text-3xl"></i>
                            </div>
                        </div>
                        
                        <div class="stat-card rounded-xl p-6 text-white">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-white text-opacity-80 text-sm">Total Clients</p>
                                    <p class="text-2xl font-bold" x-text="stats.total_clients || 0"></p>
                                </div>
                                <i class="fas fa-address-book text-white text-opacity-50 text-3xl"></i>
                            </div>
                        </div>
                        
                        <div class="stat-card rounded-xl p-6 text-white">
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-white text-opacity-80 text-sm">Commission Revenue</p>
                                    <p class="text-2xl font-bold">$<span x-text="(stats.total_commission_amount || 0).toFixed(2)"></span></p>
                                </div>
                                <i class="fas fa-dollar-sign text-white text-opacity-50 text-3xl"></i>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="glass rounded-xl p-6">
                            <h3 class="text-lg font-semibold text-white mb-4">Recent Users</h3>
                            <div class="space-y-3">
                                <template x-for="user in recentActivity.recent_users" :key="user.id">
                                    <div class="flex items-center space-x-3 p-3 bg-white bg-opacity-10 rounded-lg">
                                        <div class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center">
                                            <i class="fas fa-user text-white text-xs"></i>
                                        </div>
                                        <div class="flex-1">
                                            <p class="text-white text-sm font-medium" x-text="user.name"></p>
                                            <p class="text-white text-opacity-70 text-xs" x-text="user.email"></p>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                        
                        <div class="glass rounded-xl p-6">
                            <h3 class="text-lg font-semibold text-white mb-4">Recent Clients</h3>
                            <div class="space-y-3">
                                <template x-for="client in recentActivity.recent_clients" :key="client.id">
                                    <div class="flex items-center space-x-3 p-3 bg-white bg-opacity-10 rounded-lg">
                                        <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                            <i class="fas fa-address-book text-white text-xs"></i>
                                        </div>
                                        <div class="flex-1">
                                            <p class="text-white text-sm font-medium" x-text="client.name"></p>
                                            <p class="text-white text-opacity-70 text-xs" x-text="client.email"></p>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                        
                        <div class="glass rounded-xl p-6">
                            <h3 class="text-lg font-semibold text-white mb-4">Recent Commissions</h3>
                            <div class="space-y-3">
                                <template x-for="commission in recentActivity.recent_commissions" :key="commission.id">
                                    <div class="flex items-center space-x-3 p-3 bg-white bg-opacity-10 rounded-lg">
                                        <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                                            <i class="fas fa-dollar-sign text-white text-xs"></i>
                                        </div>
                                        <div class="flex-1">
                                            <p class="text-white text-sm font-medium">$<span x-text="commission.amount.toFixed(2)"></span></p>
                                            <p class="text-white text-opacity-70 text-xs">Client ID: <span x-text="commission.client_id"></span></p>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Database Structure Tab -->
                <div x-show="activeTab === 'database'" x-transition>
                    <div class="mb-8">
                        <h2 class="text-3xl font-bold text-white mb-2">Database Structure</h2>
                        <p class="text-white text-opacity-80">Explore your database tables and relationships</p>
                    </div>

                    <div class="space-y-6">
                        <template x-for="(table, tableName) in dbStructure" :key="tableName">
                            <div class="glass rounded-xl p-6">
                                <h3 class="text-xl font-semibold text-white mb-4 flex items-center">
                                    <i class="fas fa-table mr-3"></i>
                                    <span x-text="tableName"></span>
                                    <button @click="loadTableData(tableName)" 
                                            class="ml-auto bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                                        <i class="fas fa-eye mr-2"></i>View Data
                                    </button>
                                </h3>
                                
                                <!-- Columns -->
                                <div class="mb-4">
                                    <h4 class="text-white text-lg mb-3">Columns</h4>
                                    <div class="overflow-x-auto">
                                        <table class="min-w-full bg-white bg-opacity-10 rounded-lg">
                                            <thead>
                                                <tr class="border-b border-white border-opacity-20">
                                                    <th class="px-4 py-3 text-left text-white text-sm font-semibold">Name</th>
                                                    <th class="px-4 py-3 text-left text-white text-sm font-semibold">Type</th>
                                                    <th class="px-4 py-3 text-left text-white text-sm font-semibold">Nullable</th>
                                                    <th class="px-4 py-3 text-left text-white text-sm font-semibold">Primary Key</th>
                                                    <th class="px-4 py-3 text-left text-white text-sm font-semibold">Default</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <template x-for="column in table.columns" :key="column.name">
                                                    <tr class="border-b border-white border-opacity-10">
                                                        <td class="px-4 py-3 text-white text-sm" x-text="column.name"></td>
                                                        <td class="px-4 py-3 text-white text-sm" x-text="column.type"></td>
                                                        <td class="px-4 py-3 text-white text-sm">
                                                            <span x-text="column.nullable ? 'Yes' : 'No'" 
                                                                  :class="column.nullable ? 'text-yellow-300' : 'text-red-300'"></span>
                                                        </td>
                                                        <td class="px-4 py-3 text-white text-sm">
                                                            <span x-text="column.primary_key ? 'Yes' : 'No'"
                                                                  :class="column.primary_key ? 'text-green-300' : 'text-gray-300'"></span>
                                                        </td>
                                                        <td class="px-4 py-3 text-white text-sm" x-text="column.default || 'None'"></td>
                                                    </tr>
                                                </template>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                <!-- Foreign Keys -->
                                <div x-show="table.foreign_keys.length > 0" class="mb-4">
                                    <h4 class="text-white text-lg mb-3">Foreign Keys</h4>
                                    <div class="space-y-2">
                                        <template x-for="fk in table.foreign_keys" :key="fk">
                                            <div class="bg-white bg-opacity-10 p-3 rounded-lg text-white text-sm">
                                                <span x-text="fk.constrained_columns.join(', ')"></span> → 
                                                <span class="text-blue-300" x-text="fk.referred_table"></span>
                                                (<span x-text="fk.referred_columns.join(', ')"></span>)
                                            </div>
                                        </template>
                                    </div>
                                </div>

                                <!-- Indexes -->
                                <div x-show="table.indexes.length > 0" class="mb-4">
                                    <h4 class="text-white text-lg mb-3">Indexes</h4>
                                    <div class="space-y-2">
                                        <template x-for="index in table.indexes" :key="index.name">
                                            <div class="bg-white bg-opacity-10 p-3 rounded-lg text-white text-sm flex justify-between items-center">
                                                <span>
                                                    <strong x-text="index.name"></strong>: 
                                                    <span x-text="index.columns.join(', ')"></span>
                                                </span>
                                                <span x-show="index.unique" class="bg-green-500 text-white px-2 py-1 rounded text-xs">UNIQUE</span>
                                            </div>
                                        </template>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>

                <!-- Users Tab -->
                <div x-show="activeTab === 'users'" x-transition>
                    <div class="mb-8 flex justify-between items-center">
                        <div>
                            <h2 class="text-3xl font-bold text-white mb-2">Users Management</h2>
                            <p class="text-white text-opacity-80">Manage system users</p>
                        </div>
                        <button @click="loadUsers()" 
                                class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg transition-colors">
                            <i class="fas fa-refresh mr-2"></i>Refresh
                        </button>
                    </div>

                    <div class="glass rounded-xl p-6">
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="border-b border-white border-opacity-20">
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">ID</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Name</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Email</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Status</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Created At</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="user in users" :key="user.id">
                                        <tr class="border-b border-white border-opacity-10">
                                            <td class="px-6 py-4 text-white text-sm" x-text="user.id"></td>
                                            <td class="px-6 py-4 text-white text-sm font-medium" x-text="user.name"></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="user.email"></td>
                                            <td class="px-6 py-4 text-sm">
                                                <span :class="user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                                                      class="px-2 py-1 rounded-full text-xs font-semibold"
                                                      x-text="user.is_active ? 'Active' : 'Inactive'"></span>
                                            </td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="new Date(user.created_at).toLocaleDateString()"></td>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Clients Tab -->
                <div x-show="activeTab === 'clients'" x-transition>
                    <div class="mb-8 flex justify-between items-center">
                        <div>
                            <h2 class="text-3xl font-bold text-white mb-2">Clients Management</h2>
                            <p class="text-white text-opacity-80">Manage your clients</p>
                        </div>
                        <button @click="loadClients()" 
                                class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg transition-colors">
                            <i class="fas fa-refresh mr-2"></i>Refresh
                        </button>
                    </div>

                    <div class="glass rounded-xl p-6">
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="border-b border-white border-opacity-20">
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">ID</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Name</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Email</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Phone</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Created At</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="client in clients" :key="client.id">
                                        <tr class="border-b border-white border-opacity-10">
                                            <td class="px-6 py-4 text-white text-sm" x-text="client.id"></td>
                                            <td class="px-6 py-4 text-white text-sm font-medium" x-text="client.name"></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="client.email"></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="client.phone || 'N/A'"></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="new Date(client.created_at).toLocaleDateString()"></td>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Commissions Tab -->
                <div x-show="activeTab === 'commissions'" x-transition>
                    <div class="mb-8 flex justify-between items-center">
                        <div>
                            <h2 class="text-3xl font-bold text-white mb-2">Commissions Management</h2>
                            <p class="text-white text-opacity-80">Track commission payments</p>
                        </div>
                        <button @click="loadCommissions()" 
                                class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg transition-colors">
                            <i class="fas fa-refresh mr-2"></i>Refresh
                        </button>
                    </div>

                    <div class="glass rounded-xl p-6">
                        <div class="overflow-x-auto">
                            <table class="min-w-full">
                                <thead>
                                    <tr class="border-b border-white border-opacity-20">
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">ID</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Client</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Amount</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Source</th>
                                        <th class="px-6 py-4 text-left text-white text-sm font-semibold">Created At</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="commission in commissions" :key="commission.id">
                                        <tr class="border-b border-white border-opacity-10">
                                            <td class="px-6 py-4 text-white text-sm" x-text="commission.id"></td>
                                            <td class="px-6 py-4 text-white text-sm font-medium" x-text="commission.client_name"></td>
                                            <td class="px-6 py-4 text-white text-sm font-bold text-green-300">$<span x-text="commission.amount.toFixed(2)"></span></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="commission.source || 'N/A'"></td>
                                            <td class="px-6 py-4 text-white text-sm" x-text="new Date(commission.created_at).toLocaleDateString()"></td>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- SQL Terminal Tab -->
                <div x-show="activeTab === 'sql'" x-transition>
                    <div class="mb-8">
                        <h2 class="text-3xl font-bold text-white mb-2">SQL Terminal</h2>
                        <p class="text-white text-opacity-80">Execute SQL queries (SELECT only)</p>
                    </div>

                    <div class="glass rounded-xl p-6 mb-6">
                        <div class="mb-4">
                            <label class="block text-white text-sm font-medium mb-2">SQL Query</label>
                            <textarea x-model="sqlQuery" 
                                      class="w-full h-32 p-4 bg-gray-900 text-green-400 rounded-lg border border-gray-600 font-mono text-sm"
                                      placeholder="SELECT * FROM users LIMIT 10;"></textarea>
                        </div>
                        <button @click="executeSql()" 
                                class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors">
                            <i class="fas fa-play mr-2"></i>Execute Query
                        </button>
                    </div>

                    <div x-show="sqlResult" class="glass rounded-xl p-6">
                        <h3 class="text-lg font-semibold text-white mb-4">Query Result</h3>
                        <div x-show="sqlResult.success" class="overflow-x-auto">
                            <table class="min-w-full bg-white bg-opacity-10 rounded-lg">
                                <thead>
                                    <tr class="border-b border-white border-opacity-20">
                                        <template x-for="column in sqlResult.columns" :key="column">
                                            <th class="px-4 py-3 text-left text-white text-sm font-semibold" x-text="column"></th>
                                        </template>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="row in sqlResult.data" :key="row">
                                        <tr class="border-b border-white border-opacity-10">
                                            <template x-for="column in sqlResult.columns" :key="column">
                                                <td class="px-4 py-3 text-white text-sm" x-text="row[column] || 'NULL'"></td>
                                            </template>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                            <p class="text-white text-sm mt-4">
                                <i class="fas fa-info-circle mr-2"></i>
                                Returned <span x-text="sqlResult.row_count"></span> rows
                            </p>
                        </div>
                        <div x-show="!sqlResult.success" class="text-red-300">
                            <i class="fas fa-exclamation-triangle mr-2"></i>
                            <span x-text="sqlResult.error"></span>
                        </div>
                    </div>
                </div>

                <!-- Table Data Modal -->
                <div x-show="showTableData" x-transition 
                     class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div class="glass rounded-xl p-6 max-w-6xl max-h-5xl overflow-auto m-4">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-xl font-semibold text-white">
                                Table Data: <span x-text="currentTableData.table_name"></span>
                            </h3>
                            <button @click="showTableData = false" 
                                    class="text-white hover:text-gray-300">
                                <i class="fas fa-times text-xl"></i>
                            </button>
                        </div>
                        
                        <div class="mb-4 text-white text-sm">
                            Showing <span x-text="currentTableData.showing"></span> of 
                            <span x-text="currentTableData.total_count"></span> records
                        </div>

                        <div class="overflow-x-auto">
                            <table class="min-w-full bg-white bg-opacity-10 rounded-lg">
                                <thead>
                                    <tr class="border-b border-white border-opacity-20">
                                        <template x-for="column in currentTableData.columns" :key="column">
                                            <th class="px-4 py-3 text-left text-white text-sm font-semibold" x-text="column"></th>
                                        </template>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="row in currentTableData.data" :key="row">
                                        <tr class="border-b border-white border-opacity-10">
                                            <template x-for="column in currentTableData.columns" :key="column">
                                                <td class="px-4 py-3 text-white text-sm" x-text="row[column] || 'NULL'"></td>
                                            </template>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <script>
        function adminDashboard() {
            return {
                activeTab: 'dashboard',
                stats: {},
                recentActivity: {
                    recent_users: [],
                    recent_clients: [],
                    recent_commissions: []
                },
                dbStructure: {},
                users: [],
                clients: [],
                commissions: [],
                sqlQuery: 'SELECT * FROM users LIMIT 10;',
                sqlResult: null,
                showTableData: false,
                currentTableData: {},
                
                init() {
                    this.loadDashboardStats();
                    this.loadDatabaseStructure();
                },
                
                async loadDashboardStats() {
                    try {
                        const response = await fetch('/admin/api/stats');
                        const data = await response.json();
                        this.stats = data.stats;
                        this.recentActivity = data.recent_activity;
                    } catch (error) {
                        console.error('Error loading stats:', error);
                    }
                },
                
                async loadDatabaseStructure() {
                    try {
                        const response = await fetch('/admin/api/database/structure');
                        const data = await response.json();
                        this.dbStructure = data.tables;
                    } catch (error) {
                        console.error('Error loading database structure:', error);
                    }
                },
                
                async loadTableData(tableName) {
                    try {
                        const response = await fetch(`/admin/api/tables/${tableName}`);
                        const data = await response.json();
                        this.currentTableData = data;
                        this.showTableData = true;
                    } catch (error) {
                        console.error('Error loading table data:', error);
                    }
                },
                
                async loadUsers() {
                    try {
                        const response = await fetch('/admin/api/users');
                        const data = await response.json();
                        this.users = data.users;
                    } catch (error) {
                        console.error('Error loading users:', error);
                    }
                },
                
                async loadClients() {
                    try {
                        const response = await fetch('/clients/');
                        const data = await response.json();
                        this.clients = data;
                    } catch (error) {
                        console.error('Error loading clients:', error);
                    }
                },
                
                async loadCommissions() {
                    try {
                        const response = await fetch('/admin/api/commissions');
                        const data = await response.json();
                        this.commissions = data.commissions;
                    } catch (error) {
                        console.error('Error loading commissions:', error);
                    }
                },
                
                async executeSql() {
                    try {
                        const response = await fetch('/admin/api/sql/execute', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ query: this.sqlQuery })
                        });
                        
                        if (response.ok) {
                            this.sqlResult = await response.json();
                        } else {
                            const error = await response.json();
                            this.sqlResult = { success: false, error: error.detail };
                        }
                    } catch (error) {
                        this.sqlResult = { success: false, error: error.message };
                    }
                }
            }
        }
    </script>
</body>
</html>
    """