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

    // ==========================================
    // RECONOCIMIENTO FACIAL
    // ==========================================

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

    // ==========================================
    // GESTIÓN DE ESTUDIANTES
    // ==========================================

    // Obtener lista de todos los estudiantes
    async getStudents() {
        try {
            console.log('Obteniendo lista de estudiantes...');
            const response = await this.client.get('/api/students');
            console.log('Estudiantes obtenidos:', response.data.length);
            return response.data;
        } catch (error) {
            console.error('Error al obtener estudiantes:', error);
            throw error;
        }
    }

    // Obtener un estudiante por ID
    async getStudent(studentId) {
        try {
            console.log(`Obteniendo estudiante ID: ${studentId}`);
            const response = await this.client.get(`/api/students/${studentId}`);
            return response.data;
        } catch (error) {
            console.error('Error al obtener estudiante:', error);
            throw error;
        }
    }

    // Crear nuevo estudiante
    async createStudent(studentData, imageFile) {
        try {
            const formData = new FormData();

            // Agregar datos del estudiante
            formData.append('nombre', studentData.nombre);
            formData.append('apellidos', studentData.apellidos);
            formData.append('codigo', studentData.codigo);
            formData.append('correo', studentData.correo);
            formData.append('requisitoriado', studentData.requisitoriado || false);

            // Agregar imagen
            formData.append('image', {
                uri: imageFile.uri,
                type: imageFile.type || 'image/jpeg',
                name: imageFile.fileName || 'student_photo.jpg',
            });

            console.log('Creando nuevo estudiante...');
            const response = await this.client.post('/api/students/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log('Estudiante creado exitosamente:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error al crear estudiante:', error);
            console.error('Detalles del error:', error.response?.data);
            throw error;
        }
    }

    // Actualizar estudiante existente
    async updateStudent(studentId, studentData, imageFile = null) {
        try {
            const formData = new FormData();

            // Agregar datos del estudiante (solo los que han cambiado)
            if (studentData.nombre !== undefined) {
                formData.append('nombre', studentData.nombre);
            }
            if (studentData.apellidos !== undefined) {
                formData.append('apellidos', studentData.apellidos);
            }
            if (studentData.codigo !== undefined) {
                formData.append('codigo', studentData.codigo);
            }
            if (studentData.correo !== undefined) {
                formData.append('correo', studentData.correo);
            }
            if (studentData.requisitoriado !== undefined) {
                formData.append('requisitoriado', studentData.requisitoriado);
            }

            // Agregar nueva imagen si se proporciona
            if (imageFile) {
                formData.append('image', {
                    uri: imageFile.uri,
                    type: imageFile.type || 'image/jpeg',
                    name: imageFile.fileName || 'student_photo_updated.jpg',
                });
            }

            console.log(`Actualizando estudiante ID: ${studentId}`);
            const response = await this.client.put(`/api/students/${studentId}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log('Estudiante actualizado exitosamente:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error al actualizar estudiante:', error);
            console.error('Detalles del error:', error.response?.data);
            throw error;
        }
    }

    // Eliminar estudiante
    async deleteStudent(studentId) {
        try {
            console.log(`Eliminando estudiante ID: ${studentId}`);
            const response = await this.client.delete(`/api/students/${studentId}`);
            console.log('Estudiante eliminado exitosamente');
            return response.data;
        } catch (error) {
            console.error('Error al eliminar estudiante:', error);
            console.error('Detalles del error:', error.response?.data);
            throw error;
        }
    }

    // Obtener imagen de un estudiante
    getStudentImageUrl(studentId) {
        return `${API_BASE_URL}/api/students/${studentId}/image`;
    }

    // ==========================================
    // ESTADÍSTICAS Y SISTEMA
    // ==========================================

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

    // Obtener estadísticas de reconocimiento
    async getRecognitionStats() {
        try {
            const response = await this.client.get('/api/recognition/stats');
            return response.data;
        } catch (error) {
            console.error('Error al obtener estadísticas:', error);
            throw error;
        }
    }

    // Obtener logs de reconocimiento
    async getRecognitionLogs(skip = 0, limit = 50) {
        try {
            const response = await this.client.get(`/api/recognition/logs?skip=${skip}&limit=${limit}`);
            return response.data;
        } catch (error) {
            console.error('Error al obtener logs:', error);
            throw error;
        }
    }
}

export default new ApiService();