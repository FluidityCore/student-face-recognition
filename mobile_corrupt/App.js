import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  StyleSheet,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';
import axios from 'axios';

const API_BASE_URL = 'http://10.0.2.2:8000'; // Para emulador Android

const App = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [recognitionResult, setRecognitionResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const selectImage = () => {
    const options = {
      mediaType: 'photo',
      quality: 0.8,
      includeBase64: true,
    };

    Alert.alert(
      'Seleccionar Foto',
      'Elige una opción',
      [
        { text: 'Cámara', onPress: () => launchCamera(options, handleImageResponse) },
        { text: 'Galería', onPress: () => launchImageLibrary(options, handleImageResponse) },
        { text: 'Cancelar', style: 'cancel' },
      ]
    );
  };

  const handleImageResponse = (response) => {
    if (response.didCancel || response.error) {
      return;
    }

    if (response.assets && response.assets[0]) {
      setSelectedImage(response.assets[0]);
      setRecognitionResult(null);
    }
  };

  const recognizeFace = async () => {
    if (!selectedImage) {
      Alert.alert('Error', 'Por favor selecciona una imagen primero');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: selectedImage.uri,
        type: selectedImage.type,
        name: selectedImage.fileName || 'image.jpg',
      });

      const response = await axios.post(`${API_BASE_URL}/api/recognize`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 10000,
      });

      setRecognitionResult(response.data);
    } catch (error) {
      console.error('Error:', error);
      Alert.alert(
        'Error de Reconocimiento',
        error.response?.data?.detail || 'No se pudo conectar al servidor'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🎓 Reconocimiento Facial</Text>
        <Text style={styles.subtitle}>Sistema de Estudiantes</Text>
      </View>

      <View style={styles.section}>
        <TouchableOpacity style={styles.button} onPress={selectImage}>
          <Text style={styles.buttonText}>📷 Seleccionar Foto</Text>
        </TouchableOpacity>

        {selectedImage && (
          <View style={styles.imageContainer}>
            <Image source={{ uri: selectedImage.uri }} style={styles.image} />
            <TouchableOpacity 
              style={[styles.button, styles.recognizeButton]} 
              onPress={recognizeFace}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>🔍 Reconocer Rostro</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {recognitionResult && (
          <View style={styles.resultContainer}>
            <Text style={styles.resultTitle}>✅ Resultado del Reconocimiento</Text>
            
            {recognitionResult.success ? (
              <View style={styles.successResult}>
                <Text style={styles.studentName}>
                  👤 {recognitionResult.student.nombre}
                </Text>
                <Text style={styles.studentInfo}>
                  📧 {recognitionResult.student.email}
                </Text>
                <Text style={styles.confidence}>
                  🎯 Confianza: {(recognitionResult.confidence * 100).toFixed(1)}%
                </Text>
              </View>
            ) : (
              <View style={styles.errorResult}>
                <Text style={styles.errorText}>
                  ❌ {recognitionResult.message}
                </Text>
              </View>
            )}
          </View>
        )}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Sistema desarrollado con React Native & FastAPI
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 30,
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
  },
  section: {
    padding: 20,
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 15,
    elevation: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  recognizeButton: {
    backgroundColor: '#4CAF50',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  imageContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  image: {
    width: 250,
    height: 250,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ddd',
  },
  resultContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginTop: 20,
    elevation: 2,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  successResult: {
    alignItems: 'center',
  },
  studentName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 5,
  },
  studentInfo: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
  },
  confidence: {
    fontSize: 14,
    color: '#2196F3',
    fontWeight: 'bold',
  },
  errorResult: {
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#f44336',
    textAlign: 'center',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
});

export default App;