/**
 * AlertList Component
 * Container for displaying all alerts
 */

import React from 'react';
import AlertCard from './AlertCard';

function AlertList({ alerts, onDismiss, onRefresh }) {
    // Separate alerts by severity
    const criticalAlerts = alerts.filter(a => a.severity === 'critical');
    const warningAlerts = alerts.filter(a => a.severity === 'warning');
    const infoAlerts = alerts.filter(a => a.severity === 'info');

    // Empty state
    if (alerts.length === 0) {
        return (
            <div className="alerts-section animate-slide-up">
                <div className="section-header">
                    <h2 className="section-title">🔔 Alerts</h2>
                </div>
                <div className="empty-state">
                    <div className="empty-icon">✨</div>
                    <h3 className="empty-title">No Active Alerts</h3>
                    <p className="empty-description">
                        All clear! Hugo is monitoring your procurement operations.
                        <br />
                        Click "Run Detection" to check for new issues.
                    </p>
                    <button className="btn btn-primary" onClick={onRefresh}>
                        🔍 Run Detection
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="alerts-section animate-slide-up">
            {/* Critical Alerts */}
            {criticalAlerts.length > 0 && (
                <>
                    <div className="section-header">
                        <h2 className="section-title">🔴 Critical Alerts ({criticalAlerts.length})</h2>
                    </div>
                    <div className="alert-list">
                        {criticalAlerts.map(alert => (
                            <AlertCard
                                key={alert.id}
                                alert={alert}
                                onDismiss={onDismiss}
                            />
                        ))}
                    </div>
                </>
            )}

            {/* Warning Alerts */}
            {warningAlerts.length > 0 && (
                <>
                    <div className="section-header" style={{ marginTop: criticalAlerts.length > 0 ? '2rem' : 0 }}>
                        <h2 className="section-title">⚠️ Warnings ({warningAlerts.length})</h2>
                    </div>
                    <div className="alert-list">
                        {warningAlerts.map(alert => (
                            <AlertCard
                                key={alert.id}
                                alert={alert}
                                onDismiss={onDismiss}
                            />
                        ))}
                    </div>
                </>
            )}

            {/* Info Alerts */}
            {infoAlerts.length > 0 && (
                <>
                    <div className="section-header" style={{ marginTop: '2rem' }}>
                        <h2 className="section-title">ℹ️ Information ({infoAlerts.length})</h2>
                    </div>
                    <div className="alert-list">
                        {infoAlerts.map(alert => (
                            <AlertCard
                                key={alert.id}
                                alert={alert}
                                onDismiss={onDismiss}
                            />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

export default AlertList;
