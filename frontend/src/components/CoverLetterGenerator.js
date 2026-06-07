import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import CONFIG from '../config';

const CoverLetterGenerator = ({ file, jobDescription }) => {
    const [loading, setLoading] = useState(false);
    const [coverLetter, setCoverLetter] = useState("");

    const generateLetter = async () => {
        if (!file || !jobDescription) {
            toast.error("Upload a resume and provide a JD first!");
            return;
        }
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("job_description", jobDescription);

            const response = await axios.post(`${CONFIG.API_BASE_URL}/resumes/generate-cover-letter`, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            setCoverLetter(response.data.cover_letter);
            toast.success("Cover letter generated!");
        } catch (err) {
            toast.error("Failed to generate cover letter.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="cover-letter-section glass-panel" style={{ marginTop: '24px', padding: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0 }}>✉️ AI Cover Letter Generator</h3>
                <button
                    onClick={generateLetter}
                    disabled={loading}
                    style={{ width: 'auto', padding: '10px 24px', margin: 0, background: 'var(--secondary)' }}
                >
                    {loading ? "Writing..." : "Generate Tailored Letter"}
                </button>
            </div>

            {coverLetter && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="letter-output"
                    style={{
                        background: 'rgba(255,255,255,0.05)',
                        padding: '24px',
                        borderRadius: '16px',
                        whiteSpace: 'pre-wrap',
                        fontSize: '0.95rem',
                        lineHeight: '1.6',
                        border: '1px solid var(--border)'
                    }}
                >
                    {coverLetter}
                </motion.div>
            )}
        </div>
    );
};

export default CoverLetterGenerator;
