const getApiBaseUrl = () => {
    const url = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';
    return url.endsWith('/api') ? url : `${url}/api`;
};

const CONFIG = {
    API_BASE_URL: getApiBaseUrl(),
};

export default CONFIG;
