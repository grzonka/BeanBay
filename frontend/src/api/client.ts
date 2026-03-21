import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
});

export const API_ERROR_EVENT = 'beanbay:api-error';

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ??
      (typeof error.response?.data === 'string' ? error.response.data : null) ??
      error.message ??
      'Something went wrong';

    window.dispatchEvent(
      new CustomEvent(API_ERROR_EVENT, {
        detail: { message, status: error.response?.status },
      }),
    );

    return Promise.reject(error);
  },
);

export default apiClient;
