// Helper — extracts readable message from any axios error
export function getErrorMessage(error) {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;   // your FastAPI detail string
  }
  if (error?.response?.status === 429) {
    return "AI service is busy. Please wait a moment and try again.";
  }
  if (error?.response?.status >= 500) {
    return "Something went wrong on our end. Please try again shortly.";
  }
  if (error?.code === "ECONNABORTED") {
    return "Request timed out. Please check your connection.";
  }
  return "An unexpected error occurred. Please try again.";
}