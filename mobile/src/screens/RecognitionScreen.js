import React, { useState } from 'react';
import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
    SafeAreaView,
    Alert,
    Image,
    ActivityIndicator,
    ScrollView,
} from 'react-native';
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';
import ApiService from '../services/ApiService';

const RecognitionScreen = () => {
    const [selectedImage, setSelectedImage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleStartRecognition = () => {
        Alert.alert(
            'Seleccionar Foto',
            'Elige una opción para capturar o seleccionar la imagen',
            [
                { text: 'Cámara', onPress: openCamera },
                { text: 'Galería', onPress: openGallery },
                { text: 'Cancelar', style: 'cancel' },
            ]
        );
    };

    const openCamera = () => {
        const options = {
            mediaType: 'photo',
            quality: 0.8,
            maxWidth: 1024,
            maxHeight: 1024,
            includeBase64: false,
        };

        launchCamera(options, handleImageResponse);
    };

    const openGallery = () => {
        const options = {
            mediaType: 'photo',
            quality: 0.8,
            maxWidth: 1024,
            maxHeight: 1024,
            includeBase64: false,
        };

        launchImageLibrary(options, handleImageResponse);
    };

    const handleImageResponse = (response) => {
        if (response.didCancel) {
            console.log('Usuario canceló la selección de imagen');
            return;
        }

        if (response.error) {
            console.error('Error al seleccionar imagen:', response.error);
            Alert.alert('Error', 'No se pudo seleccionar la imagen');
            return;
        }

        if (response.assets && response.assets[0]) {
            const imageFile = response.assets[0];
            console.log('Imagen seleccionada:', imageFile);

            setSelectedImage(imageFile);
            setResult(null);

            // ✅ Iniciar reconocimiento automáticamente
            recognizeImage(imageFile);
        }
    };

    const recognizeImage = async (imageFile) => {
        setLoading(true);

        try {
            console.log('🚀 Iniciando proceso de reconocimiento facial...');

            // ✅ Mostrar progreso al usuario
            Alert.alert(
                'Procesando...',
                'Analizando la imagen. Esto puede tomar hasta 2 minutos.',
                [{ text: 'OK' }]
            );

            const response = await ApiService.recognizeStudent(imageFile);

            console.log('✅ Resultado del reconocimiento:', response);
            setResult(response);

            // ✅ Determinar si se encontró un estudiante
            const isFound = response.found || false;

            if (isFound && response.student) {
                const student = response.student;
                const similarity = response.similarity ? (response.similarity * 100).toFixed(1) : 'N/A';

                Alert.alert(
                    '✅ Estudiante Identificado',
                    `👤 ${student.nombre} ${student.apellidos}\n` +
                    `🆔 Código: ${student.codigo}\n` +
                    `📧 ${student.correo}\n` +
                    `🎯 Similitud: ${similarity}%\n` +
                    `${student.requisitoriado ? '\n⚠️ ESTUDIANTE REQUISITORIADO' : ''}`,
                    [{ text: 'OK' }]
                );

                // ✅ Si está requisitoriado, mostrar alerta adicional
                if (student.requisitoriado) {
                    setTimeout(() => {
                        Alert.alert(
                            '🚨 ALERTA DE SEGURIDAD',
                            `El estudiante ${student.nombre} ${student.apellidos} está marcado como REQUISITORIADO.\n\nContactar seguridad inmediatamente.`,
                            [{ text: 'Entendido', style: 'destructive' }]
                        );
                    }, 1000);
                }
            } else {
                Alert.alert(
                    '❌ No Encontrado',
                    response.message || 'No se encontró ningún estudiante que coincida con el rostro en la imagen.',
                    [{ text: 'OK' }]
                );
            }

        } catch (error) {
            console.error('❌ Error completo en reconocimiento:', error);

            Alert.alert(
                'Error de Reconocimiento',
                error.message || 'No se pudo procesar la imagen. Verifica tu conexión e intenta nuevamente.',
                [
                    { text: 'Reintentar', onPress: () => recognizeImage(imageFile) },
                    { text: 'Cancelar', style: 'cancel' }
                ]
            );

        } finally {
            setLoading(false);
        }
    };

    const resetRecognition = () => {
        setSelectedImage(null);
        setResult(null);
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.title}>🔍 Reconocimiento Facial</Text>
                    <Text style={styles.subtitle}>Sistema de Identificación de Estudiantes</Text>
                </View>

                {/* Status del servidor */}
                <View style={styles.statusContainer}>
                    <Text style={styles.statusText}>
                        🌐 Conectado a: {ApiService.getApiBaseUrl().includes('railway') ? 'Railway Cloud' : 'Servidor Local'}
                    </Text>
                </View>

                {/* Botón principal */}
                <TouchableOpacity
                    style={[styles.mainButton, loading && styles.disabledButton]}
                    onPress={handleStartRecognition}
                    disabled={loading}
                >
                    {loading ? (
                        <View style={styles.loadingContainer}>
                            <ActivityIndicator color="#fff" size="large" />
                            <Text style={styles.loadingText}>Procesando...</Text>
                        </View>
                    ) : (
                        <Text style={styles.buttonText}>📷 Iniciar Reconocimiento</Text>
                    )}
                </TouchableOpacity>

                {/* Imagen seleccionada */}
                {selectedImage && (
                    <View style={styles.imageSection}>
                        <Text style={styles.sectionTitle}>📸 Imagen Seleccionada:</Text>
                        <View style={styles.imageContainer}>
                            <Image source={{ uri: selectedImage.uri }} style={styles.selectedImage} />
                            {!loading && (
                                <TouchableOpacity style={styles.resetButton} onPress={resetRecognition}>
                                    <Text style={styles.resetButtonText}>🔄 Cambiar Imagen</Text>
                                </TouchableOpacity>
                            )}
                        </View>
                    </View>
                )}

                {/* Progreso de carga */}
                {loading && (
                    <View style={styles.progressSection}>
                        <Text style={styles.progressTitle}>⏳ Procesando imagen...</Text>
                        <Text style={styles.progressSubtitle}>
                            • Detectando rostro en la imagen{'\n'}
                            • Comparando con base de datos{'\n'}
                            • Calculando similitudes{'\n'}
                            • Esto puede tomar hasta 2 minutos
                        </Text>
                    </View>
                )}

                {/* Resultado del reconocimiento */}
                {result && !loading && (
                    <View style={styles.resultSection}>
                        <Text style={styles.sectionTitle}>
                            {result.found ? '✅ Resultado Exitoso' : '❌ Sin Coincidencias'}
                        </Text>

                        {result.found && result.student ? (
                            <View style={[
                                styles.studentCard,
                                result.student.requisitoriado && styles.alertCard
                            ]}>
                                {result.student.requisitoriado && (
                                    <View style={styles.alertBanner}>
                                        <Text style={styles.alertText}>🚨 REQUISITORIADO</Text>
                                    </View>
                                )}

                                <Text style={styles.studentName}>
                                    {result.student.nombre} {result.student.apellidos}
                                </Text>

                                <View style={styles.studentDetails}>
                                    <Text style={styles.studentDetail}>🆔 Código: {result.student.codigo}</Text>
                                    <Text style={styles.studentDetail}>📧 {result.student.correo}</Text>
                                    <Text style={styles.studentDetail}>
                                        🎯 Similitud: {result.similarity ? (result.similarity * 100).toFixed(1) : 'N/A'}%
                                    </Text>
                                    <Text style={styles.studentDetail}>
                                        💪 Confianza: {result.confidence || 'Media'}
                                    </Text>
                                    {result.processing_time && (
                                        <Text style={styles.studentDetail}>
                                            ⏱️ Tiempo: {result.processing_time.toFixed(2)}s
                                        </Text>
                                    )}
                                </View>
                            </View>
                        ) : (
                            <View style={styles.noResultCard}>
                                <Text style={styles.noResultTitle}>No se encontró coincidencia</Text>
                                <Text style={styles.noResultText}>
                                    {result.message || 'El rostro no coincide con ningún estudiante registrado en la base de datos.'}
                                </Text>
                                {result.similarity && (
                                    <Text style={styles.similarityText}>
                                        Mejor coincidencia: {(result.similarity * 100).toFixed(1)}%
                                    </Text>
                                )}
                            </View>
                        )}
                    </View>
                )}

                {/* Botón para nuevo reconocimiento */}
                {result && !loading && (
                    <TouchableOpacity
                        style={styles.newRecognitionButton}
                        onPress={handleStartRecognition}
                    >
                        <Text style={styles.newRecognitionText}>🔄 Nuevo Reconocimiento</Text>
                    </TouchableOpacity>
                )}

                {/* Instrucciones */}
                <View style={styles.instructionsSection}>
                    <Text style={styles.instructionsTitle}>💡 Instrucciones:</Text>
                    <Text style={styles.instructionsText}>
                        • Asegúrate de tener buena conexión a internet{'\n'}
                        • La imagen debe mostrar claramente el rostro{'\n'}
                        • Evita imágenes borrosas o con poca luz{'\n'}
                        • El procesamiento puede tomar hasta 2 minutos
                    </Text>
                </View>

            </ScrollView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    content: {
        flexGrow: 1,
        padding: 20,
    },
    header: {
        alignItems: 'center',
        marginBottom: 20,
    },
    title: {
        fontSize: 26,
        fontWeight: 'bold',
        color: '#2196F3',
        textAlign: 'center',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    statusContainer: {
        backgroundColor: '#e8f5e8',
        padding: 10,
        borderRadius: 8,
        marginBottom: 20,
        alignItems: 'center',
    },
    statusText: {
        fontSize: 14,
        color: '#2e7d32',
        fontWeight: '600',
    },
    mainButton: {
        backgroundColor: '#2196F3',
        paddingVertical: 18,
        paddingHorizontal: 40,
        borderRadius: 12,
        elevation: 4,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        alignItems: 'center',
        marginBottom: 30,
    },
    disabledButton: {
        backgroundColor: '#90CAF9',
    },
    buttonText: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
    },
    loadingContainer: {
        alignItems: 'center',
    },
    loadingText: {
        color: '#fff',
        fontSize: 16,
        marginTop: 10,
        fontWeight: '600',
    },
    imageSection: {
        marginBottom: 30,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 15,
        textAlign: 'center',
    },
    imageContainer: {
        alignItems: 'center',
    },
    selectedImage: {
        width: 250,
        height: 250,
        borderRadius: 15,
        borderWidth: 3,
        borderColor: '#2196F3',
    },
    resetButton: {
        backgroundColor: '#FF9800',
        paddingVertical: 8,
        paddingHorizontal: 20,
        borderRadius: 8,
        marginTop: 15,
    },
    resetButtonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold',
    },
    progressSection: {
        backgroundColor: '#fff3cd',
        padding: 20,
        borderRadius: 12,
        marginBottom: 20,
        borderLeftWidth: 4,
        borderLeftColor: '#ffc107',
    },
    progressTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#856404',
        marginBottom: 10,
    },
    progressSubtitle: {
        fontSize: 14,
        color: '#856404',
        lineHeight: 20,
    },
    resultSection: {
        marginBottom: 30,
    },
    studentCard: {
        backgroundColor: '#fff',
        borderRadius: 15,
        padding: 20,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        borderLeftWidth: 5,
        borderLeftColor: '#4CAF50',
    },
    alertCard: {
        borderLeftColor: '#f44336',
        backgroundColor: '#fff5f5',
    },
    alertBanner: {
        backgroundColor: '#f44336',
        padding: 8,
        borderRadius: 8,
        marginBottom: 15,
        alignItems: 'center',
    },
    alertText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
    studentName: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#2196F3',
        textAlign: 'center',
        marginBottom: 15,
    },
    studentDetails: {
        gap: 8,
    },
    studentDetail: {
        fontSize: 16,
        color: '#555',
        paddingVertical: 2,
    },
    noResultCard: {
        backgroundColor: '#fff',
        borderRadius: 15,
        padding: 20,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        borderLeftWidth: 5,
        borderLeftColor: '#f44336',
        alignItems: 'center',
    },
    noResultTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#f44336',
        marginBottom: 10,
    },
    noResultText: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
        lineHeight: 22,
    },
    similarityText: {
        fontSize: 14,
        color: '#999',
        marginTop: 10,
        fontStyle: 'italic',
    },
    newRecognitionButton: {
        backgroundColor: '#4CAF50',
        paddingVertical: 12,
        paddingHorizontal: 30,
        borderRadius: 10,
        alignItems: 'center',
        marginBottom: 30,
    },
    newRecognitionText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
    instructionsSection: {
        backgroundColor: '#f8f9fa',
        padding: 15,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: '#e9ecef',
    },
    instructionsTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#495057',
        marginBottom: 8,
    },
    instructionsText: {
        fontSize: 14,
        color: '#6c757d',
        lineHeight: 20,
    },
});

export default RecognitionScreen;