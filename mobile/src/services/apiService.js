import axios from 'axios';

// URL de tu backend (ajusta si es necesario)
const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

class ApiService {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000, // 30 segundos
        });
    }

    // Reconocer estudiante por imagen
    async recognizeStudent(imageFile) {
        try {
            const formData = new FormData();
            formData.append('image', {
                uri: imageFile.uri,
                type: imageFile.type || 'image/jpeg',
                name: imageFile.fileName || 'image.jpg',
            });

            console.log('Enviando imagen al backend...');
            const response = await this.client.post('/api/recognize', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log('Respuesta completa del backend:', JSON.stringify(response.data, null, 2));

            // Adaptar la respuesta del backend al formato esperado por la app
            const backendData = response.data;

            // Transformar la respuesta según tu estructura actual del backend
            const transformedResponse = {
                success: backendData.found || false,
                found: backendData.found || false,
                student: backendData.student || null,
                similarity: backendData.similarity || 0,
                confidence: backendData.confidence || 'Baja',
                message: backendData.message || 'Procesado correctamente'
            };

            console.log('Respuesta transformada:', JSON.stringify(transformedResponse, null, 2));
            return transformedResponse;
        } catch (error) {
            console.error('Error en reconocimiento:', error);
            console.error('Detalles del error:', error.response?.data);
            throw error;
        }
    }

    // Verificar que el backend esté funcionando
    async checkHealth() {
        try {
            const response = await this.client.get('/health');
            console.log('Health check:', response.data);
            return response.data;
        } catch (error) {
            console.error('Backend no disponible:', error);
            throw error;
        }
    }
}

export default new ApiService();