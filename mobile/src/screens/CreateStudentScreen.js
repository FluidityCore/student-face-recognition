import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    SafeAreaView,
    ScrollView,
    Alert,
    ActivityIndicator,
    Image,
    Switch,
} from 'react-native';
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';
import ApiService from '../services/ApiService';

const CreateStudentScreen = ({ navigation }) => {
    const [formData, setFormData] = useState({
        nombre: '',
        apellidos: '',
        codigo: '',
        correo: '',
        requisitoriado: false,
    });

    const [selectedImage, setSelectedImage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    // Validación del formulario
    const validateForm = () => {
        const newErrors = {};

        if (!formData.nombre.trim()) {
            newErrors.nombre = 'El nombre es obligatorio';
        }

        if (!formData.apellidos.trim()) {
            newErrors.apellidos = 'Los apellidos son obligatorios';
        }

        if (!formData.codigo.trim()) {
            newErrors.codigo = 'El código es obligatorio';
        } else if (formData.codigo.length < 6) {
            newErrors.codigo = 'El código debe tener al menos 6 caracteres';
        }

        if (!formData.correo.trim()) {
            newErrors.correo = 'El correo es obligatorio';
        } else if (!isValidEmail(formData.correo)) {
            newErrors.correo = 'Formato de correo inválido';
        }

        if (!selectedImage) {
            newErrors.image = 'La foto del estudiante es obligatoria';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const isValidEmail = (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    // Manejar cambios en los inputs
    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));

        // Limpiar error del campo cuando el usuario empiece a escribir
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: null
            }));
        }
    };

    // Seleccionar imagen
    const handleSelectImage = () => {
        Alert.alert(
            'Seleccionar Foto',
            'Elige una opción para la foto del estudiante',
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
            setSelectedImage(response.assets[0]);
            // Limpiar error de imagen
            if (errors.image) {
                setErrors(prev => ({
                    ...prev,
                    image: null
                }));
            }
        }
    };

    // Enviar formulario
    const handleSubmit = async () => {
        if (!validateForm()) {
            Alert.alert('Formulario Incompleto', 'Por favor, completa todos los campos obligatorios');
            return;
        }

        setLoading(true);

        try {
            console.log('Enviando datos del estudiante:', formData);

            const response = await ApiService.createStudent(formData, selectedImage);

            console.log('Estudiante creado exitosamente:', response);

            Alert.alert(
                'Éxito',
                `Estudiante ${formData.nombre} ${formData.apellidos} registrado correctamente`,
                [
                    {
                        text: 'Ver Lista',
                        onPress: () => navigation.navigate('StudentsList')
                    },
                    {
                        text: 'Crear Otro',
                        onPress: resetForm
                    }
                ]
            );

        } catch (error) {
            console.error('Error al crear estudiante:', error);

            let errorMessage = 'No se pudo registrar el estudiante';

            if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }

            Alert.alert('Error', errorMessage);
        } finally {
            setLoading(false);
        }
    };

    // Limpiar formulario
    const resetForm = () => {
        setFormData({
            nombre: '',
            apellidos: '',
            codigo: '',
            correo: '',
            requisitoriado: false,
        });
        setSelectedImage(null);
        setErrors({});
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
                <View style={styles.content}>

                    {/* Header */}
                    <View style={styles.header}>
                        <Text style={styles.title}>➕ Registrar Nuevo Estudiante</Text>
                        <Text style={styles.subtitle}>Completa todos los campos</Text>
                    </View>

                    {/* Formulario */}
                    <View style={styles.form}>

                        {/* Foto del estudiante */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>📷 Foto del Estudiante *</Text>

                            <TouchableOpacity
                                style={[
                                    styles.imageSelector,
                                    errors.image && styles.inputError
                                ]}
                                onPress={handleSelectImage}
                            >
                                {selectedImage ? (
                                    <Image
                                        source={{ uri: selectedImage.uri }}
                                        style={styles.selectedImage}
                                    />
                                ) : (
                                    <View style={styles.imagePlaceholder}>
                                        <Text style={styles.imagePlaceholderText}>📷</Text>
                                        <Text style={styles.imagePlaceholderSubtext}>
                                            Toca para seleccionar foto
                                        </Text>
                                    </View>
                                )}
                            </TouchableOpacity>

                            {errors.image && (
                                <Text style={styles.errorText}>{errors.image}</Text>
                            )}
                        </View>

                        {/* Nombre */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>👤 Nombre *</Text>
                            <TextInput
                                style={[
                                    styles.input,
                                    errors.nombre && styles.inputError
                                ]}
                                placeholder="Ingresa el nombre"
                                value={formData.nombre}
                                onChangeText={(value) => handleInputChange('nombre', value)}
                            />
                            {errors.nombre && (
                                <Text style={styles.errorText}>{errors.nombre}</Text>
                            )}
                        </View>

                        {/* Apellidos */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>👥 Apellidos *</Text>
                            <TextInput
                                style={[
                                    styles.input,
                                    errors.apellidos && styles.inputError
                                ]}
                                placeholder="Ingresa los apellidos"
                                value={formData.apellidos}
                                onChangeText={(value) => handleInputChange('apellidos', value)}
                            />
                            {errors.apellidos && (
                                <Text style={styles.errorText}>{errors.apellidos}</Text>
                            )}
                        </View>

                        {/* Código */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>🆔 Código Estudiantil *</Text>
                            <TextInput
                                style={[
                                    styles.input,
                                    errors.codigo && styles.inputError
                                ]}
                                placeholder="Ej: EST001234"
                                value={formData.codigo}
                                onChangeText={(value) => handleInputChange('codigo', value.toUpperCase())}
                                autoCapitalize="characters"
                            />
                            {errors.codigo && (
                                <Text style={styles.errorText}>{errors.codigo}</Text>
                            )}
                        </View>

                        {/* Correo */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>📧 Correo Electrónico *</Text>
                            <TextInput
                                style={[
                                    styles.input,
                                    errors.correo && styles.inputError
                                ]}
                                placeholder="estudiante@universidad.edu"
                                value={formData.correo}
                                onChangeText={(value) => handleInputChange('correo', value.toLowerCase())}
                                keyboardType="email-address"
                                autoCapitalize="none"
                            />
                            {errors.correo && (
                                <Text style={styles.errorText}>{errors.correo}</Text>
                            )}
                        </View>

                        {/* Estado Requisitoriado */}
                        <View style={styles.inputGroup}>
                            <View style={styles.switchContainer}>
                                <View style={styles.switchLabelContainer}>
                                    <Text style={styles.label}>⚠️ Estado Especial</Text>
                                    <Text style={styles.switchSubtext}>
                                        Marcar si el estudiante está requisitoriado
                                    </Text>
                                </View>
                                <Switch
                                    value={formData.requisitoriado}
                                    onValueChange={(value) => handleInputChange('requisitoriado', value)}
                                    trackColor={{ false: '#767577', true: '#f44336' }}
                                    thumbColor={formData.requisitoriado ? '#fff' : '#f4f3f4'}
                                />
                            </View>
                        </View>

                    </View>

                    {/* Botones */}
                    <View style={styles.buttonContainer}>
                        <TouchableOpacity
                            style={[styles.button, styles.submitButton]}
                            onPress={handleSubmit}
                            disabled={loading}
                        >
                            {loading ? (
                                <ActivityIndicator color="#fff" />
                            ) : (
                                <Text style={styles.buttonText}>✅ Registrar Estudiante</Text>
                            )}
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.button, styles.cancelButton]}
                            onPress={() => navigation.goBack()}
                            disabled={loading}
                        >
                            <Text style={[styles.buttonText, styles.cancelButtonText]}>
                                ❌ Cancelar
                            </Text>
                        </TouchableOpacity>
                    </View>

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
    scrollView: {
        flex: 1,
    },
    content: {
        padding: 20,
        paddingBottom: 40,
    },
    header: {
        alignItems: 'center',
        marginBottom: 30,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        textAlign: 'center',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    form: {
        backgroundColor: '#fff',
        borderRadius: 15,
        padding: 20,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        marginBottom: 20,
    },
    inputGroup: {
        marginBottom: 20,
    },
    label: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 8,
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 10,
        paddingHorizontal: 15,
        paddingVertical: 12,
        fontSize: 16,
        backgroundColor: '#f9f9f9',
    },
    inputError: {
        borderColor: '#f44336',
        backgroundColor: '#fff5f5',
    },
    errorText: {
        color: '#f44336',
        fontSize: 14,
        marginTop: 5,
        marginLeft: 5,
    },
    imageSelector: {
        borderWidth: 2,
        borderColor: '#ddd',
        borderStyle: 'dashed',
        borderRadius: 15,
        height: 200,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f9f9f9',
    },
    selectedImage: {
        width: '100%',
        height: '100%',
        borderRadius: 13,
    },
    imagePlaceholder: {
        alignItems: 'center',
    },
    imagePlaceholderText: {
        fontSize: 48,
        marginBottom: 10,
    },
    imagePlaceholderSubtext: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    switchContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 5,
    },
    switchLabelContainer: {
        flex: 1,
        marginRight: 15,
    },
    switchSubtext: {
        fontSize: 14,
        color: '#666',
        marginTop: 2,
    },
    buttonContainer: {
        gap: 15,
    },
    button: {
        paddingVertical: 15,
        paddingHorizontal: 30,
        borderRadius: 10,
        alignItems: 'center',
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
    },
    submitButton: {
        backgroundColor: '#4CAF50',
    },
    cancelButton: {
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: '#ddd',
    },
    buttonText: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#fff',
    },
    cancelButtonText: {
        color: '#666',
    },
});

export default CreateStudentScreen;