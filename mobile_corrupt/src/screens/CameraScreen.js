import React, {useState, useRef} from 'react';
import {
    View,
    StyleSheet,
    Alert,
    Dimensions,
} from 'react-native';
import {Button, ActivityIndicator, Text} from 'react-native-paper';
import {launchImageLibrary, launchCamera} from 'react-native-image-picker';
import apiService from '../services/apiService';

const {width, height} = Dimensions.get('window');

const CameraScreen = ({navigation}) => {
    const [loading, setLoading] = useState(false);
    const [imageUri, setImageUri] = useState(null);

    const selectImage = () => {
        Alert.alert(
            'Seleccionar Imagen',
            'Elige una opción',
            [
                {text: 'Cámara', onPress: openCamera},
                {text: 'Galería', onPress: openGallery},
                {text: 'Cancelar', style: 'cancel'},
            ],
        );
    };

    const openCamera = () => {
        const options = {
            mediaType: 'photo',
            quality: 0.7,
        };

        launchCamera(options, response => {
            if (response.assets && response.assets[0]) {
                processImage(response.assets[0]);
            }
        });
    };

    const openGallery = () => {
        const options = {
            mediaType: 'photo',
            quality: 0.7,
        };

        launchImageLibrary(options, response => {
            if (response.assets && response.assets[0]) {
                processImage(response.assets[0]);
            }
        });
    };

    const processImage = async (image) => {
        setLoading(true);
        setImageUri(image.uri);

        try {
            const result = await apiService.recognizeStudent(image);
            navigation.navigate('Result', {
                result,
                imageUri: image.uri,
            });
        } catch (error) {
            Alert.alert('Error', 'No se pudo procesar la imagen');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.content}>
                <Text style={styles.instruction}>
                    Toma una foto o selecciona una imagen para reconocer al estudiante
                </Text>

                {loading ? (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#2196F3" />
                        <Text style={styles.loadingText}>Procesando imagen...</Text>
                    </View>
                ) : (
                    <View style={styles.buttonContainer}>
                        <Button
                            mode="contained"
                            onPress={selectImage}
                            style={styles.button}
                            icon="camera"
                            contentStyle={styles.buttonContent}>
                            Seleccionar Imagen
                        </Button>
                    </View>
                )}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    content: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    instruction: {
        fontSize: 18,
        textAlign: 'center',
        marginBottom: 40,
        color: '#666',
    },
    loadingContainer: {
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 20,
        fontSize: 16,
        color: '#666',
    },
    buttonContainer: {
        width: '100%',
    },
    button: {
        paddingVertical: 8,
    },
    buttonContent: {
        height: 60,
    },
});

export default CameraScreen;