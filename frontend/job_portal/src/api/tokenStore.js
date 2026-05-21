// In-memory token store — survives component re-renders but NOT page refresh.
// Page refresh triggers a silent /auth/refresh call using the HttpOnly cookie.

let accessToken = null;
let userRole    = null;

export const setAccessToken = (token) => { accessToken = token; };
export const getAccessToken = () => accessToken;
export const clearAccessToken = () => { accessToken = null; };

export const setUserRole = (role) => { userRole = role; };
export const getUserRole = () => userRole;
export const clearUserRole = () => { userRole = null; };

export const clearAll = () => {
    accessToken = null;
    userRole    = null;
};