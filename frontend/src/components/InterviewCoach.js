import React, { useState } from 'react';
import './InterviewCoach.css';
import { motion, AnimatePresence } from 'framer-motion';

const InterviewCoach = ({ questions, overallAdvice }) => {
    const [activeIndex, setActiveIndex] = useState(null);

    if (!questions || questions.length === 0) return null;

    return (
        <div className="coach-container glass-panel">
            <div className="coach-header">
                <motion.h3
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                >
                    🎓 AI Interview Coach
                </motion.h3>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="advice-banner"
                >
                    <strong>Preparation Tip:</strong> {overallAdvice}
                </motion.p>
            </div>

            <div className="questions-stack">
                {questions.map((q, index) => (
                    <motion.div
                        key={q.id || index}
                        layout
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`question-card ${activeIndex === index ? 'active' : ''}`}
                        onClick={() => setActiveIndex(activeIndex === index ? null : index)}
                    >
                        <div className="q-type-badge">{q.type}</div>
                        <div className="q-main">
                            <h4>Question {index + 1}</h4>
                            <p className="q-text">{q.question}</p>
                        </div>

                        <AnimatePresence>
                            {activeIndex === index && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="q-tip"
                                >
                                    <div className="tip-divider" />
                                    <strong>💡 Coach's Advice:</strong>
                                    <p>{q.tip}</p>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="q-expand-hint">
                            {activeIndex === index ? 'Click to collapse' : 'Click to see answer strategy'}
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default InterviewCoach;
