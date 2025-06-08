import axios from 'axios';

// ✅ URL CORREGIDA - Apunta a Railway
const API_BASE_URL = 'https://student-face-recognition-production.up.railway.app';

class ApiService {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 120000, // ✅ 2 minutos para reconocimiento facial
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'UPAO-Mobile-App/1.0'
            }
        });

        // ✅ Interceptor para logging
        this.client.interceptors.request.use(
            (config) => {
                console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
                return config;
            },
            (error) => {
                console.error('❌ Request Error:', error);
                return Promise.reject(error);
            }
        );

        this.client.interceptors.response.use(
            (response) => {
                console.log(`✅ API Response: ${response.status} ${response.config.url}`);
                return response;
            },
            (error) => {
                console.error('❌ Response Error:', error.response?.status, error.response?.data);
                return Promise.reject(error);
            }
        );
    }

    // ==========================================
    // RECONOCIMIENTO FACIAL
    // ==========================================

    async recognizeStudent(imageFile) {
        try {
            const formData = new FormData();
            formData.append('image', {
                uri: imageFile.uri,
                type: imageFile.type || 'image/jpeg',
                name: imageFile.fileName || 'recognition.jpg',
            });

            console.log('📷 Enviando imagen para reconocimiento...');
            console.log('📝 Archivo:', {
                uri: imageFile.uri,
                type: imageFile.type,
                name: imageFile.fileName
            });

            const response = await this.client.post('/api/recognize', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 120000, // 2 minutos específico para reconocimiento
            });

            console.log('✅ Respuesta del reconocimiento:', JSON.stringify(response.data, null, 2));

            // ✅ Respuesta ya viene en formato correcto del backend Railway
            return response.data;

        } catch (error) {
            console.error('❌ Error en reconocimiento facial:', error);

            if (error.code === 'ECONNABORTED') {
                throw new Error('⏱️ Timeout: El reconocimiento está tomando demasiado tiempo');
            }

            if (error.response?.status === 400) {
                throw new Error(error.response.data?.detail || 'Imagen inválida o sin rostro detectado');
            }

            if (error.response?.status >= 500) {
                throw new Error('🔧 Error del servidor. Intenta nuevamente.');
            }

            if (!error.response) {
                throw new Error('🌐 Sin conexión al servidor. Verifica tu internet.');
            }

            throw error;
        }
    }

    // ==========================================
    // GESTIÓN DE ESTUDIANTES
    // ==========================================

    async getStudents() {
        try {
            console.log('👥 Obteniendo lista de estudiantes...');
            const response = await this.client.get('/api/students');
            console.log(`✅ ${response.data.length} estudiantes obtenidos`);
            return response.data;
        } catch (error) {
            console.error('❌ Error al obtener estudiantes:', error);
            this.handleApiError(error, 'No se pudieron cargar los estudiantes');
        }
    }

    async getStudent(studentId) {
        try {
            console.log(`👤 Obteniendo estudiante ID: ${studentId}`);
            const response = await this.client.get(`/api/students/${studentId}`);
            return response.data;
        } catch (error) {
            console.error('❌ Error al obtener estudiante:', error);
            this.handleApiError(error, 'No se pudo obtener el estudiante');
        }
    }

    async createStudent(studentData, imageFile) {
        try {
            const formData = new FormData();

            // ✅ Agregar datos del estudiante
            formData.append('nombre', studentData.nombre);
            formData.append('apellidos', studentData.apellidos);
            formData.append('codigo', studentData.codigo);
            formData.append('correo', studentData.correo);
            formData.append('requisitoriado', studentData.requisitoriado ? 'true' : 'false');

            // ✅ Agregar imagen
            formData.append('image', {
                uri: imageFile.uri,
                type: imageFile.type || 'image/jpeg',
                name: imageFile.fileName || `student_${studentData.codigo}.jpg`,
            });

            console.log('➕ Creando nuevo estudiante:', studentData.codigo);

            const response = await this.client.post('/api/students', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 60000, // 1 minuto para crear estudiante
            });

            console.log('✅ Estudiante creado exitosamente:', response.data);
            return response.data;

        } catch (error) {
            console.error('❌ Error al crear estudiante:', error);
            this.handleApiError(error, 'No se pudo crear el estudiante');
        }
    }

    async updateStudent(studentId, studentData, imageFile = null) {
        try {
            const formData = new FormData();

            // ✅ Agregar solo datos que han cambiado
            Object.keys(studentData).forEach(key => {
                if (studentData[key] !== undefined) {
                    formData.append(key, studentData[key]);
                }
            });

            // ✅ Agregar nueva imagen si se proporciona
            if (imageFile) {
                formData.append('image', {
                    uri: imageFile.uri,
                    type: imageFile.type || 'image/jpeg',
                    name: imageFile.fileName || `student_${studentId}_updated.jpg`,
                });
            }

            console.log(`✏️ Actualizando estudiante ID: ${studentId}`);

            const response = await this.client.put(`/api/students/${studentId}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            console.log('✅ Estudiante actualizado exitosamente');
            return response.data;

        } catch (error) {
            console.error('❌ Error al actualizar estudiante:', error);
            this.handleApiError(error, 'No se pudo actualizar el estudiante');
        }
    }

    async deleteStudent(studentId) {
        try {
            console.log(`🗑️ Eliminando estudiante ID: ${studentId}`);
            const response = await this.client.delete(`/api/students/${studentId}`);
            console.log('✅ Estudiante eliminado exitosamente');
            return response.data;
        } catch (error) {
            console.error('❌ Error al eliminar estudiante:', error);
            this.handleApiError(error, 'No se pudo eliminar el estudiante');
        }
    }

    // ✅ URL de imagen corregida para Railway
    getStudentImageUrl(studentId) {
        return `${API_BASE_URL}/api/students/${studentId}/image?t=${Date.now()}`;
    }

    // ==========================================
    // ESTADÍSTICAS Y SISTEMA
    // ==========================================

    async checkHealth() {
        try {
            console.log('🏥 Verificando estado del servidor...');
            const response = await this.client.get('/health', {
                timeout: 10000, // 10 segundos para health check
            });
            console.log('✅ Servidor funcionando correctamente');
            return response.data;
        } catch (error) {
            console.error('❌ Servidor no disponible:', error);
            throw new Error('Servidor no disponible');
        }
    }

    async getRecognitionStats() {
        try {
            console.log('📊 Obteniendo estadísticas...');
            const response = await this.client.get('/api/recognition/stats');
            return response.data;
        } catch (error) {
            console.error('❌ Error al obtener estadísticas:', error);
            // No lanzar error aquí, estadísticas no son críticas
            return {
                total_recognitions: 0,
                successful_recognitions: 0,
                success_rate: 0
            };
        }
    }

    async getRecognitionLogs(skip = 0, limit = 50) {
        try {
            const response = await this.client.get(`/api/recognition/logs?skip=${skip}&limit=${limit}`);
            return response.data;
        } catch (error) {
            console.error('❌ Error al obtener logs:', error);
            return [];
        }
    }

    // ==========================================
    // MANEJO DE ERRORES MEJORADO
    // ==========================================

    handleApiError(error, defaultMessage) {
        if (error.response) {
            // Error del servidor (4xx, 5xx)
            const status = error.response.status;
            const data = error.response.data;

            if (status === 400) {
                throw new Error(data?.detail || 'Datos inválidos');
            } else if (status === 404) {
                throw new Error('Recurso no encontrado');
            } else if (status === 422) {
                throw new Error('Error de validación de datos');
            } else if (status >= 500) {
                throw new Error('Error interno del servidor');
            } else {
                throw new Error(data?.detail || defaultMessage);
            }
        } else if (error.request) {
            // Sin respuesta del servidor
            throw new Error('Sin conexión al servidor');
        } else {
            // Error de configuración
            throw new Error(error.message || defaultMessage);
        }
    }

    // ==========================================
    // UTILIDADES
    // ==========================================

    getApiBaseUrl() {
        return API_BASE_URL;
    }

    isConnected() {
        return API_BASE_URL.includes('railway.app');
    }
}

export default new ApiService();