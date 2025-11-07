// Central place to configure backend API base URL
// Use NEXT_PUBLIC_API_URL for client-side code so it's exposed at build time
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
