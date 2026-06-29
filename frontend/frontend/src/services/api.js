import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})

export async function sendMessage(payload) {
  const response = await apiClient.post('/chat', payload)
  return response.data
}

export async function uploadPDF(file, onUploadProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/upload_pdf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
  return response.data
}

export async function getChatHistory() {
  const response = await apiClient.get('/history')
  return response.data
}

export async function clearChat() {
  const response = await apiClient.delete('/history')
  return response.data
}

export default apiClient
