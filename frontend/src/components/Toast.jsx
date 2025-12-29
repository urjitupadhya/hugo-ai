/**
 * Toast Notification Component
 */

import React from 'react';

function Toast({ message, type = 'success', onClose }) {
    return (
        <div className="toast-container">
            <div className={`toast ${type}`}>
                <span>{type === 'success' ? '✅' : '❌'}</span>
                <span>{message}</span>
                <button
                    className="btn btn-ghost btn-sm"
                    onClick={onClose}
                    style={{ marginLeft: 'auto' }}
                >
                    ✕
                </button>
            </div>
        </div>
    );
}

export default Toast;
