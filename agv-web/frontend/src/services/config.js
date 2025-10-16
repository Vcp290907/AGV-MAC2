// Centralized configuration for API and WebSocket URLs
// Priority: explicit env vars -> current window hostname

const getHostname = () => {
  try {
    if (typeof window !== 'undefined' && window.location && window.location.hostname) {
      return window.location.hostname;
    }
  } catch (_) {}
  return 'localhost';
};

// Allow override via environment variables when needed
const ENV_API_URL = process.env.REACT_APP_API_URL;
const ENV_SOCKET_URL = process.env.REACT_APP_SOCKET_URL;

const DEFAULT_HOSTNAME = getHostname();

export const API_BASE_URL = ENV_API_URL || `http://${DEFAULT_HOSTNAME}:5000`;
export const SOCKET_URL = ENV_SOCKET_URL || `http://${DEFAULT_HOSTNAME}:5000`;

export default {
  API_BASE_URL,
  SOCKET_URL,
};
