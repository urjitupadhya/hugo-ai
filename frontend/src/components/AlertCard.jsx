/**
 * AlertCard Component
 * Displays individual alert with expandable details
 */

import React, { useState } from 'react';

function AlertCard({ alert, onDismiss }) {
    const [expanded, setExpanded] = useState(false);

    // Format alert type for display
    const formatAlertType = (type) => {
        const types = {
            'supplier_delay': 'Supplier Delay',
            'price_spike': 'Price Spike',
            'financial_distress': 'Financial Risk',
            'quality_issue': 'Quality Issue',
            'stockout_risk': 'Stockout Risk'
        };
        return types[type] || type;
    };

    // Format currency
    const formatCurrency = (value) => {
        if (!value) return '$0';
        if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
        return `$${value.toFixed(0)}`;
    };

    // Format date
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Get severity icon
    const getSeverityIcon = () => {
        switch (alert.severity) {
            case 'critical': return '🔴';
            case 'warning': return '🟡';
            default: return '🟢';
        }
    };

    // Get type icon
    const getTypeIcon = () => {
        switch (alert.alert_type) {
            case 'supplier_delay': return '📦';
            case 'price_spike': return '💰';
            case 'financial_distress': return '🏦';
            case 'quality_issue': return '🔧';
            case 'stockout_risk': return '📉';
            default: return '⚠️';
        }
    };

    return (
        <div className={`alert-card ${alert.severity} ${expanded ? 'expanded' : ''} animate-slide-up`}>
            {/* Alert Header */}
            <div className="alert-header" onClick={() => setExpanded(!expanded)}>
                <div className="alert-info">
                    {/* Badges */}
                    <div className="alert-badges">
                        <span className={`badge ${alert.severity}`}>
                            {getSeverityIcon()} {alert.severity}
                        </span>
                        <span className="badge type">
                            {getTypeIcon()} {formatAlertType(alert.alert_type)}
                        </span>
                    </div>

                    {/* Title */}
                    <h3 className="alert-title">{alert.title}</h3>

                    {/* Description */}
                    <p className="alert-description">{alert.description}</p>

                    {/* Meta */}
                    <div className="alert-meta">
                        <span>🕐 {formatDate(alert.created_at)}</span>
                        {alert.financial_impact?.total > 0 && (
                            <span>💰 {formatCurrency(alert.financial_impact.total)} at risk</span>
                        )}
                        {alert.operational_impact?.affected_orders_count > 0 && (
                            <span>📋 {alert.operational_impact.affected_orders_count} orders affected</span>
                        )}
                    </div>
                </div>

                {/* Actions */}
                <div className="alert-actions">
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDismiss(alert.id);
                        }}
                    >
                        ✓ Dismiss
                    </button>
                    <div className="expand-icon">
                        {expanded ? '▲' : '▼'}
                    </div>
                </div>
            </div>

            {/* Expanded Details */}
            {expanded && (
                <div className="alert-details">
                    {/* Impact Analysis */}
                    {alert.impact_summary && (
                        <div className="alert-section">
                            <h4 className="alert-section-title">📊 Impact Analysis</h4>
                            <div className="alert-section-content">
                                {alert.impact_summary}
                            </div>
                        </div>
                    )}

                    {/* Financial Impact Grid */}
                    {(alert.financial_impact?.revenue_at_risk > 0 || alert.financial_impact?.penalty_risk > 0) && (
                        <div className="alert-section">
                            <h4 className="alert-section-title">💰 Financial Impact</h4>
                            <div className="impact-grid">
                                <div className="impact-item">
                                    <div className="impact-label">Revenue at Risk</div>
                                    <div className="impact-value warning">
                                        {formatCurrency(alert.financial_impact?.revenue_at_risk)}
                                    </div>
                                </div>
                                <div className="impact-item">
                                    <div className="impact-label">Penalty Risk</div>
                                    <div className="impact-value critical">
                                        {formatCurrency(alert.financial_impact?.penalty_risk)}
                                    </div>
                                </div>
                                <div className="impact-item">
                                    <div className="impact-label">Total Exposure</div>
                                    <div className="impact-value critical">
                                        {formatCurrency(alert.financial_impact?.total)}
                                    </div>
                                </div>
                                {alert.operational_impact?.days_until_stockout && (
                                    <div className="impact-item">
                                        <div className="impact-label">Days Until Stockout</div>
                                        <div className={`impact-value ${alert.operational_impact.days_until_stockout < 5 ? 'critical' : 'warning'}`}>
                                            {alert.operational_impact.days_until_stockout < 999
                                                ? `${alert.operational_impact.days_until_stockout} days`
                                                : 'No risk'
                                            }
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Recommended Actions */}
                    {alert.recommended_actions && (
                        <div className="alert-section">
                            <h4 className="alert-section-title">✅ Recommended Actions</h4>
                            <div className="alert-section-content">
                                {alert.recommended_actions}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AlertCard;
