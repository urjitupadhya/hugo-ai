import React from 'react';

function InventoryAlerts({ onChatAbout }) {
    return (
        <div className="inventory-alerts">
            <div className="page-header">
                <h1 className="page-title">📦 Inventory Health</h1>
                <p className="page-subtitle">Stockouts, excess inventory, and reorder points</p>
            </div>

            <div className="empty-state">
                <div className="empty-icon">📊</div>
                <h3>Inventory Module Loading...</h3>
                <p>This feature is currently being connected to the new Firebase backend.</p>
                <button className="btn btn-secondary" onClick={() => onChatAbout({ title: "Inventory status", description: "Checking inventory status" })}>
                    Ask Chat about Inventory
                </button>
            </div>
        </div>
    );
}

export default InventoryAlerts;
