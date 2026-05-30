const getApiBaseUrl = () => {
    let url = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

    // Fix Render internal hostnames for the browser
    if (url && !url.includes('.') && !url.includes('localhost')) {
        url = `https://${url}.onrender.com`;
    }

    return url.endsWith('/api') ? url : `${url}/api`;
};


const CONFIG = {
    API_BASE_URL: getApiBaseUrl(),
    AI_SERVICE_URL: process.env.REACT_APP_AI_SERVICE_URL || 'https://resume-analyzer-ai-service.onrender.com',
};

export default CONFIG;
