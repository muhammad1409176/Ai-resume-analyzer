import React, { useState } from 'react';
import './InterviewCoach.css';

const InterviewCoach = ({ questions, overallAdvice }) => {
    const [activeIndex, setActiveIndex] = useState(null);

    if (!questions || questions.length === 0) return null;

    return (
        <div className="coach-container">
            <div className="coach-header">
                <h3>🎓 AI Interview Coach</h3>
                <p className="advice-banner">
                    <strong>Preparation Tip:</strong> {overallAdvice}
                </p>
            </div>

            <div className="questions-stack">
                {questions.map((q, index) => (
                    <div
                        key={q.id}
                        className={`question-card ${activeIndex === index ? 'active' : ''}`}
                        onClick={() => setActiveIndex(activeIndex === index ? null : index)}
                    >
                        <div className="q-type-badge">{q.type}</div>
                        <div className="q-main">
                            <h4>Question {index + 1}</h4>
                            <p className="q-text">{q.question}</p>
                        </div>

                        {activeIndex === index && (
                            <div className="q-tip">
                                <strong>💡 Coach's Advice:</strong>
                                <p>{q.tip}</p>
                            </div>
                        )}

                        <div className="q-expand-hint">
                            {activeIndex === index ? 'Click to collapse' : 'Click to see answer strategy'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default InterviewCoach;
