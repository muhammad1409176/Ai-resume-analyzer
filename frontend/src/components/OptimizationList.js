import React from 'react';
import './OptimizationList.css';

const OptimizationList = ({ optimizations, overallTip }) => {
    if (!optimizations || optimizations.length === 0) return null;

    return (
        <div className="optimization-container">
            <div className="optimization-header">
                <h3>✨ AI Smart Optimizations</h3>
                <p className="pro-tip"><strong>Pro Tip:</strong> {overallTip}</p>
            </div>

            <div className="optimization-grid">
                {optimizations.map((item, index) => (
                    <div key={index} className="optimization-card">
                        <div className="opt-badge">{item.category}</div>
                        <div className="opt-content">
                            <div className="opt-before">
                                <strong>Current:</strong>
                                <p>{item.current}</p>
                            </div>
                            <div className="opt-arrow">⬇ PRO SUGGESTION ⬇</div>
                            <div className="opt-after">
                                <strong>Optimized Rewrite:</strong>
                                <p>{item.suggestion}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default OptimizationList;
