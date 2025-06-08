import React, { useState, useEffect } from 'react';
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

const EditStudentScreen = ({ navigation, route }) => {
    const { student } = route.params || {};

    const [formData, setFormData] = useState({
        nombre: '',
        apellidos: '',
        codigo: '',
        correo: '',
        requisitoriado: false,
    });

    const [selectedImage, setSelectedImage] = useState(null);
    const [currentImageUrl, setCurrentImageUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});
    const [hasChanges, setHasChanges] = useState(false);

    // Cargar datos del estudiante al inicializar
    useEffect(() => {
        if (student) {
            setFormData({
                nombre: student.nombre || '',
                apellidos: student.apellidos || '',
                codigo: student.codigo || '',
                correo: student.correo || '',
                requisitoriado: student.requisitoriado || false,
            });

            // URL de la imagen actual del estudiante
            setCurrentImageUrl(ApiService.getStudentImageUrl(student.id));
        }
    }, [student]);

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

        setHasChanges(true);

        // Limpiar error del campo cuando el usuario empiece a escribir
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: null
            }));
        }
    };

    // Seleccionar nueva imagen
    const handleSelectImage = () => {
        Alert.alert(
            'Cambiar Foto',
            'Elige una opción para actualizar la foto del estudiante',
            [
                { text: 'Cámara', onPress: openCamera },
                { text: 'Galería', onPress: openGallery },
                { text: 'Mantener Actual', style: 'cancel' },
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
            setHasChanges(true);
        }
    };

    // Enviar actualización
    const handleSubmit = async () => {
        if (!validateForm()) {
            Alert.alert('Formulario Incompleto', 'Por favor, completa todos los campos obligatorios');
            return;
        }

        if (!hasChanges && !selectedImage) {
            Alert.alert('Sin Cambios', 'No has realizado ningún cambio');
            return;
        }

        setLoading(true);

        try {
            console.log('Actualizando estudiante:', student.id, formData);

            const response = await ApiService.updateStudent(student.id, formData, selectedImage);

            console.log('Estudiante actualizado exitosamente:', response);

            Alert.alert(
                'Éxito',
                `Estudiante ${formData.nombre} ${formData.apellidos} actualizado correctamente`,
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.goBack()
                    }
                ]
            );

        } catch (error) {
            console.error('Error al actualizar estudiante:', error);

            let errorMessage = 'No se pudo actualizar el estudiante';

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

    // Confirmar eliminación
    const handleDelete = () => {
        Alert.alert(
            'Eliminar Estudiante',
            `¿Estás seguro de que deseas eliminar a ${formData.nombre} ${formData.apellidos}?\n\nEsta acción no se puede deshacer.`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: confirmDelete
                }
            ]
        );
    };

    const confirmDelete = async () => {
        setLoading(true);

        try {
            await ApiService.deleteStudent(student.id);

            Alert.alert(
                'Eliminado',
                'Estudiante eliminado correctamente',
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.navigate('StudentsList')
                    }
                ]
            );

        } catch (error) {
            console.error('Error al eliminar estudiante:', error);
            Alert.alert('Error', 'No se pudo eliminar el estudiante');
        } finally {
            setLoading(false);
        }
    };

    if (!student) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>❌ No se encontró el estudiante</Text>
                    <TouchableOpacity
                        style={styles.button}
                        onPress={() => navigation.goBack()}
                    >
                        <Text style={styles.buttonText}>Volver</Text>
                    </TouchableOpacity>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
                <View style={styles.content}>

                    {/* Header */}
                    <View style={styles.header}>
                        <Text style={styles.title}>✏️ Editar Estudiante</Text>
                        <Text style={styles.subtitle}>ID: {student.id}</Text>
                    </View>

                    {/* Formulario */}
                    <View style={styles.form}>

                        {/* Foto del estudiante */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>📷 Foto del Estudiante</Text>

                            <TouchableOpacity
                                style={styles.imageSelector}
                                onPress={handleSelectImage}
                            >
                                {selectedImage ? (
                                    // Nueva imagen seleccionada
                                    <View style={styles.imageContainer}>
                                        <Image
                                            source={{ uri: selectedImage.uri }}
                                            style={styles.selectedImage}
                                        />
                                        <View style={styles.imageOverlay}>
                                            <Text style={styles.imageOverlayText}>Nueva imagen</Text>
                                        </View>
                                    </View>
                                ) : currentImageUrl ? (
                                    // Imagen actual del estudiante
                                    <View style={styles.imageContainer}>
                                        <Image
                                            source={{ uri: currentImageUrl }}
                                            style={styles.selectedImage}
                                        />
                                        <View style={styles.imageOverlay}>
                                            <Text style={styles.imageOverlayText}>Toca para cambiar</Text>
                                        </View>
                                    </View>
                                ) : (
                                    // Sin imagen
                                    <View style={styles.imagePlaceholder}>
                                        <Text style={styles.imagePlaceholderText}>📷</Text>
                                        <Text style={styles.imagePlaceholderSubtext}>
                                            Toca para seleccionar foto
                                        </Text>
                                    </View>
                                )}
                            </TouchableOpacity>
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
                                <Text style={styles.buttonText}>💾 Guardar Cambios</Text>
                            )}
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.button, styles.deleteButton]}
                            onPress={handleDelete}
                            disabled={loading}
                        >
                            <Text style={styles.buttonText}>🗑️ Eliminar Estudiante</Text>
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
        borderRadius: 15,
        height: 200,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f9f9f9',
        overflow: 'hidden',
    },
    imageContainer: {
        width: '100%',
        height: '100%',
        position: 'relative',
    },
    selectedImage: {
        width: '100%',
        height: '100%',
    },
    imageOverlay: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(0,0,0,0.7)',
        paddingVertical: 8,
        alignItems: 'center',
    },
    imageOverlayText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold',
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
        backgroundColor: '#2196F3',
    },
    deleteButton: {
        backgroundColor: '#f44336',
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
    errorContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
});

export default EditStudentScreen;