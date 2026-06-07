import React, { useState } from 'react';
import './OptimizationList.css';
import { motion, AnimatePresence } from 'framer-motion';

const OptimizationList = ({ optimizations, overallTip }) => {
    const [expandedIndex, setExpandedIndex] = useState(null);

    if (!optimizations || optimizations.length === 0) return null;

    return (
        <div className="optimization-container glass-panel">
            <div className="opt-header">
                <h3>✨ AI Smart Optimizations</h3>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="overall-tip"
                >
                    {overallTip}
                </motion.p>
            </div>

            <div className="opt-list">
                {optimizations.map((opt, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`opt-card ${expandedIndex === index ? 'expanded' : ''}`}
                        onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                    >
                        <div className="opt-main">
                            <span className="opt-category">{opt.category}</span>
                            <p className="opt-suggestion">{opt.suggestion}</p>
                        </div>

                        <AnimatePresence>
                            {expandedIndex === index && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="opt-details"
                                >
                                    <div className="diff-view">
                                        <div className="diff-item old">
                                            <span className="diff-label">Current</span>
                                            <p>{opt.current}</p>
                                        </div>
                                        <div className="diff-arrow">↘</div>
                                        <div className="diff-item new">
                                            <span className="diff-label">Optimized</span>
                                            <p>{opt.suggestion}</p>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="expand-indicator">
                            {expandedIndex === index ? "Collapse" : "View Comparison"}
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default OptimizationList;
