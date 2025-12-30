/**
 * Hugo AI Procurement Agent
 * Main Application Component with Feature Navigation
 */

import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AlertList from './components/AlertList';
import Toast from './components/Toast';
import InventoryAlerts from './components/InventoryAlerts';
import ChatInterface from './components/ChatInterface';

// API Base URL - normalized to remove trailing slash
const API_BASE = (import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`).replace(/\/$/, '');

function App() {
  // Feature state
  const [activeFeature, setActiveFeature] = useState('supplier');

  // Chat context for context-aware chat
  const [chatContext, setChatContext] = useState(null);

  // Supplier alerts state
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState(null);

  // Fetch supplier alerts on mount
  useEffect(() => {
    if (activeFeature === 'supplier') {
      fetchSupplierData();
    }
  }, [activeFeature]);

  const fetchSupplierData = async () => {
    try {
      const [alertsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/alerts`),
        fetch(`${API_BASE}/stats`)
      ]);

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(alertsData.alerts || []);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      showToast('Unable to connect to Hugo API', 'error');
      setLoading(false);
    }
  };

  const refreshSupplierAlerts = async () => {
    setRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/alerts/refresh`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        showToast(`✅ Detection complete: ${result.new_alerts_count} new alerts`, 'success');
        await fetchSupplierData();
      } else {
        showToast('Failed to refresh alerts', 'error');
      }
    } catch (error) {
      console.error('Error refreshing:', error);
      showToast('Unable to connect to Hugo API', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const dismissAlert = async (alertId) => {
    try {
      const response = await fetch(`${API_BASE}/alerts/${alertId}/dismiss`, {
        method: 'POST'
      });

      if (response.ok) {
        setAlerts(alerts.filter(a => a.id !== alertId));
        showToast('Alert dismissed', 'success');
      }
    } catch (error) {
      console.error('Error dismissing alert:', error);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Handle "Chat about this" from alerts
  const handleChatAbout = (alert) => {
    // Create context message with alert details
    const contextMessage = `I need help with this issue: ${alert.title}. ` +
      `Details: ${alert.description}. ` +
      (alert.severity === 'critical' ? 'This is CRITICAL. ' : '') +
      (alert.financial_impact?.total ? `Financial impact: $${alert.financial_impact.total.toLocaleString()}. ` : '') +
      'What should I do?';

    setChatContext(contextMessage);
    setActiveFeature('chat');
  };

  // Render content based on active feature
  const renderContent = () => {
    switch (activeFeature) {
      case 'supplier':
        return (
          <div className="supplier-alerts">
            {/* Header */}
            <div className="page-header">
              <div className="header-content">
                <h1 className="page-title">🚚 Supplier Alerts</h1>
                <p className="page-subtitle">Delays, price changes, quality issues, financial risks</p>
              </div>
              <button
                className={`btn btn-primary ${refreshing ? 'loading' : ''}`}
                onClick={refreshSupplierAlerts}
                disabled={refreshing}
              >
                {refreshing ? '🔄 Analyzing...' : '🔍 Run Detection'}
              </button>
            </div>

            {/* Stats */}
            <Dashboard stats={stats} alerts={alerts} />

            {/* Alerts */}
            <AlertList
              alerts={alerts.filter(a => !a.dismissed)}
              onDismiss={dismissAlert}
              onRefresh={refreshSupplierAlerts}
              onChatAbout={handleChatAbout}
            />
          </div>
        );

      case 'inventory':
        return <InventoryAlerts onChatAbout={handleChatAbout} />;

      case 'chat':
        return <ChatInterface initialMessage={chatContext} onContextUsed={() => setChatContext(null)} />;

      default:
        return (
          <div className="coming-soon">
            <div className="empty-icon">🚀</div>
            <h2>Coming Soon</h2>
            <p>This feature is under development.</p>
          </div>
        );
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <Sidebar
        activeFeature={activeFeature}
        onSelectFeature={setActiveFeature}
      />

      {/* Main Content */}
      <main className="main-content">
        {loading && activeFeature === 'supplier' ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p className="loading-text">Loading Hugo AI...</p>
          </div>
        ) : (
          renderContent()
        )}
      </main>

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default App;
