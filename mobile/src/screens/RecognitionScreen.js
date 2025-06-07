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
            'Elige una opción',
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
            includeBase64: false,
        };

        launchCamera(options, handleImageResponse);
    };

    const openGallery = () => {
        const options = {
            mediaType: 'photo',
            quality: 0.8,
            includeBase64: false,
        };

        launchImageLibrary(options, handleImageResponse);
    };

    const handleImageResponse = (response) => {
        if (response.didCancel || response.error) {
            return;
        }

        if (response.assets && response.assets[0]) {
            const imageFile = response.assets[0];
            setSelectedImage(imageFile);
            setResult(null);

            // Iniciar reconocimiento automáticamente
            recognizeImage(imageFile);
        }
    };

    const recognizeImage = async (imageFile) => {
        setLoading(true);
        try {
            console.log('Iniciando reconocimiento...');
            const response = await ApiService.recognizeStudent(imageFile);
            console.log('Resultado del reconocimiento:', response);

            setResult(response);

            // Verificar múltiples campos para determinar si fue exitoso
            const isFound = response.found || response.success || (response.student && response.student.nombre);

            if (isFound && response.student) {
                const studentName = response.student.nombre || response.student.name || 'Nombre no disponible';
                const studentEmail = response.student.email || response.student.correo || 'Sin email';
                const similarity = response.similarity ? (response.similarity * 100).toFixed(1) : 'N/A';

                Alert.alert(
                    '✅ Estudiante Encontrado',
                    `👤 ${studentName}\n📧 ${studentEmail}\n🎯 Similitud: ${similarity}%`
                );
            } else {
                const message = response.message || 'No se encontró ningún estudiante con ese rostro';
                Alert.alert(
                    '❌ No Encontrado',
                    message
                );
            }
        } catch (error) {
            console.error('Error completo:', error);
            Alert.alert(
                'Error de Conexión',
                `No se pudo conectar al servidor.\n\nDetalles: ${error.message || 'Error desconocido'}`
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content}>
                <Text style={styles.title}>🎓 Reconocimiento Facial</Text>
                <Text style={styles.subtitle}>Sistema de Estudiantes</Text>

                <TouchableOpacity
                    style={styles.button}
                    onPress={handleStartRecognition}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.buttonText}>📷 Iniciar Reconocimiento</Text>
                    )}
                </TouchableOpacity>

                {selectedImage && (
                    <View style={styles.imageContainer}>
                        <Text style={styles.imageTitle}>Imagen seleccionada:</Text>
                        <Image source={{ uri: selectedImage.uri }} style={styles.image} />
                    </View>
                )}

                {result && (
                    <View style={styles.resultContainer}>
                        <Text style={styles.resultTitle}>
                            {(result.found || result.success || (result.student && result.student.nombre)) ? '✅ Resultado' : '❌ Sin coincidencias'}
                        </Text>

                        {(result.found || result.success || (result.student && result.student.nombre)) ? (
                            <View style={styles.studentInfo}>
                                <Text style={styles.studentName}>
                                    {result.student?.nombre || result.student?.name || 'Nombre no disponible'}
                                </Text>
                                <Text style={styles.studentDetail}>
                                    📧 {result.student?.email || result.student?.correo || 'Sin email'}
                                </Text>
                                {result.student?.id && (
                                    <Text style={styles.studentDetail}>
                                        🆔 ID: {result.student.id}
                                    </Text>
                                )}
                                <Text style={styles.confidence}>
                                    🎯 Similitud: {result.similarity ? (result.similarity * 100).toFixed(1) : 'N/A'}%
                                </Text>
                                <Text style={styles.confidence}>
                                    💪 Confianza: {result.confidence || 'N/A'}
                                </Text>
                            </View>
                        ) : (
                            <Text style={styles.noResult}>
                                {result.message || 'No se encontró coincidencia en la base de datos'}
                            </Text>
                        )}

                        {/* Debug info - puedes comentar esto después */}
                        <View style={styles.debugContainer}>
                            <Text style={styles.debugTitle}>Debug Info:</Text>
                            <Text style={styles.debugText}>
                                {JSON.stringify(result, null, 2)}
                            </Text>
                        </View>
                    </View>
                )}
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
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#2196F3',
        marginBottom: 10,
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 18,
        color: '#666',
        marginBottom: 50,
        textAlign: 'center',
    },
    button: {
        backgroundColor: '#2196F3',
        paddingVertical: 15,
        paddingHorizontal: 30,
        borderRadius: 10,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        minWidth: 200,
        minHeight: 50,
        justifyContent: 'center',
        alignItems: 'center',
    },
    buttonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    imageContainer: {
        marginTop: 30,
        alignItems: 'center',
    },
    imageTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 10,
        color: '#333',
    },
    image: {
        width: 200,
        height: 200,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: '#ddd',
    },
    resultContainer: {
        backgroundColor: '#fff',
        padding: 20,
        borderRadius: 10,
        marginTop: 20,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        width: '100%',
    },
    resultTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 15,
    },
    studentInfo: {
        alignItems: 'center',
    },
    studentName: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#2196F3',
        marginBottom: 8,
    },
    studentDetail: {
        fontSize: 16,
        color: '#666',
        marginBottom: 8,
    },
    confidence: {
        fontSize: 14,
        color: '#4CAF50',
        fontWeight: 'bold',
        marginBottom: 4,
    },
    noResult: {
        fontSize: 16,
        color: '#f44336',
        textAlign: 'center',
        fontStyle: 'italic',
    },
    debugContainer: {
        marginTop: 20,
        padding: 10,
        backgroundColor: '#f0f0f0',
        borderRadius: 5,
    },
    debugTitle: {
        fontSize: 14,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    debugText: {
        fontSize: 10,
        fontFamily: 'monospace',
        color: '#666',
    },
});

export default RecognitionScreen;