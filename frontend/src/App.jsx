/**
 * Hugo AI - Procurement Agent
 * Main Application Component
 */

import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import AlertList from './components/AlertList';
import Toast from './components/Toast';

// API Base URL - change this for production
const API_URL = 'http://localhost:8000';

function App() {
  // State
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState(null);

  // Fetch alerts and stats on mount
  useEffect(() => {
    fetchData();
  }, []);

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [alertsRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/alerts`),
        fetch(`${API_URL}/stats`)
      ]);

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(alertsData.alerts || []);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      showToast('Unable to connect to Hugo API. Is the backend running?', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Refresh alerts (run detection engine)
  const refreshAlerts = async () => {
    setRefreshing(true);
    try {
      const response = await fetch(`${API_URL}/alerts/refresh`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        showToast(`Detection complete! ${data.new_alerts_count} new alerts generated.`, 'success');
        // Refresh data
        await fetchData();
      } else {
        showToast('Error refreshing alerts', 'error');
      }
    } catch (error) {
      console.error('Error refreshing alerts:', error);
      showToast('Unable to connect to Hugo API', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  // Dismiss an alert
  const dismissAlert = async (alertId) => {
    try {
      const response = await fetch(`${API_URL}/alerts/${alertId}/dismiss`, {
        method: 'POST'
      });

      if (response.ok) {
        setAlerts(alerts.filter(a => a.id !== alertId));
        showToast('Alert dismissed', 'success');
        // Update stats
        if (stats) {
          setStats({
            ...stats,
            active_alerts: stats.active_alerts - 1,
            dismissed_alerts: stats.dismissed_alerts + 1
          });
        }
      }
    } catch (error) {
      console.error('Error dismissing alert:', error);
      showToast('Error dismissing alert', 'error');
    }
  };

  // Show toast notification
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">H</div>
          <div>
            <h1 className="header-title">Hugo AI</h1>
            <p className="header-subtitle">Procurement Operations Agent • Voltway</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className={`btn btn-primary btn-lg ${refreshing ? 'loading' : ''}`}
            onClick={refreshAlerts}
            disabled={refreshing}
          >
            {refreshing ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              <>
                🔍 Run Detection
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Connecting to Hugo AI...</p>
        </div>
      ) : (
        <>
          {/* Dashboard Stats */}
          <Dashboard stats={stats} alerts={alerts} />

          {/* Alert List */}
          <AlertList
            alerts={alerts}
            onDismiss={dismissAlert}
            onRefresh={refreshAlerts}
          />
        </>
      )}

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
