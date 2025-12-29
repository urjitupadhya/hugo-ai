/**
 * Dashboard Component
 * Displays key stats and metrics
 */

import React from 'react';

function Dashboard({ stats, alerts }) {
    // Calculate stats from alerts if backend stats not available
    const calculateStats = () => {
        if (stats) return stats;

        const active = alerts.filter(a => !a.dismissed);
        const critical = active.filter(a => a.severity === 'critical').length;
        const warning = active.filter(a => a.severity === 'warning').length;
        const totalRisk = active.reduce((sum, a) => sum + (a.financial_impact?.total || 0), 0);

        return {
            active_alerts: active.length,
            by_severity: { critical, warning },
            total_financial_risk: totalRisk
        };
    };

    const data = calculateStats();

    // Format currency
    const formatCurrency = (value) => {
        if (!value) return '$0';
        if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
        return `$${value.toFixed(0)}`;
    };

    return (
        <div className="stats-grid animate-fade-in">
            {/* Active Alerts */}
            <div className={`stat-card ${data.by_severity?.critical > 0 ? 'critical' : ''}`}>
                <div className="stat-icon alerts">🚨</div>
                <div className="stat-value">{data.active_alerts || 0}</div>
                <div className="stat-label">Active Alerts</div>
            </div>

            {/* Critical Issues */}
            <div className={`stat-card ${data.by_severity?.critical > 0 ? 'critical' : ''}`}>
                <div className="stat-icon alerts">🔴</div>
                <div className="stat-value">{data.by_severity?.critical || 0}</div>
                <div className="stat-label">Critical Issues</div>
            </div>

            {/* Warnings */}
            <div className={`stat-card ${data.by_severity?.warning > 2 ? 'warning' : ''}`}>
                <div className="stat-icon warning">⚠️</div>
                <div className="stat-value">{data.by_severity?.warning || 0}</div>
                <div className="stat-label">Warnings</div>
            </div>

            {/* Financial Risk */}
            <div className="stat-card">
                <div className="stat-icon info">💰</div>
                <div className="stat-value">
                    {formatCurrency(data.total_financial_risk)}
                </div>
                <div className="stat-label">Total Risk Exposure</div>
            </div>

            {/* Alert Types Breakdown */}
            {data.by_type && Object.keys(data.by_type).length > 0 && (
                <div className="stat-card">
                    <div className="stat-icon info">📊</div>
                    <div className="stat-value">{Object.keys(data.by_type).length}</div>
                    <div className="stat-label">Alert Categories</div>
                </div>
            )}
        </div>
    );
}

export default Dashboard;
