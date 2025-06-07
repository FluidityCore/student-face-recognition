import axios from 'axios';

const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

class ApiService {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
        });
    }

    async recognizeStudent(imageFile) {
        try {
            const formData = new FormData();
            formData.append('image', {
                uri: imageFile.uri,
                type: imageFile.type || 'image/jpeg',
                name: imageFile.fileName || 'image.jpg',
            });

            const response = await this.client.post('/api/recognize', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            return response.data;
        } catch (error) {
            console.error('Error recognizing student:', error);
            throw error;
        }
    }

    async getStudents() {
        try {
            const response = await this.client.get('/api/students');
            return response.data;
        } catch (error) {
            console.error('Error getting students:', error);
            throw error;
        }
    }

    async getSystemStats() {
        try {
            const response = await this.client.get('/api/admin/stats');
            return response.data;
        } catch (error) {
            console.error('Error getting stats:', error);
            throw error;
        }
    }
}

export default new ApiService();