import React from 'react';

function Sidebar({ activeFeature, onSelectFeature }) {
    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="logo-icon">H</div>
                <span className="logo-text">Hugo AI</span>
            </div>

            <nav className="sidebar-nav">
                <button
                    className={`nav-item ${activeFeature === 'supplier' ? 'active' : ''}`}
                    onClick={() => onSelectFeature('supplier')}
                >
                    <span className="icon">🚚</span>
                    <span className="label">Supplier Alerts</span>
                </button>

                <button
                    className={`nav-item ${activeFeature === 'inventory' ? 'active' : ''}`}
                    onClick={() => onSelectFeature('inventory')}
                >
                    <span className="icon">📦</span>
                    <span className="label">Inventory</span>
                </button>

                <button
                    className={`nav-item ${activeFeature === 'chat' ? 'active' : ''}`}
                    onClick={() => onSelectFeature('chat')}
                >
                    <span className="icon">💬</span>
                    <span className="label">Chat Agent</span>
                </button>
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="avatar">U</div>
                    <div className="details">
                        <span className="name">Procurement Mgr</span>
                        <span className="role">Voltway</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
