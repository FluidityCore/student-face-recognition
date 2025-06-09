// mobile/screens/AddStudentScreen.tsx - VERSIÓN RESPONSIVA Y MODERNA
import React, { useState } from 'react';
import {
    View,
    StyleSheet,
    Image,
    Alert,
    ScrollView,
    KeyboardAvoidingView,
    Platform,
    Animated,
} from 'react-native';
import {
    Surface,
    Button,
    Text,
    Card,
    TextInput,
    Switch,
    ActivityIndicator,
    ProgressBar,
} from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';
import { responsive, baseStyles, wp, hp, fp } from '../utils/responsive';

const API_BASE = 'https://student-face-recognition-production.up.railway.app';

export default function AddStudentScreen() {
    const navigation = useNavigation();
    const { theme, isDark } = useTheme();
    const [currentStep, setCurrentStep] = useState(1);
    const [formData, setFormData] = useState({
        nombre: '',
        apellidos: '',
        codigo: '',
        correo: '',
        requisitoriado: false,
    });
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [fadeAnim] = useState(new Animated.Value(1));

    const totalSteps = 3;
    const progress = currentStep / totalSteps;

    const selectImage = async () => {
        try {
            Alert.alert(
                'Seleccionar Foto',
                'Elige una opción',
                [
                    { text: 'Cámara', onPress: takePhoto },
                    { text: 'Galería', onPress: pickFromGallery },
                    { text: 'Cancelar', style: 'cancel' },
                ]
            );
        } catch (error) {
            Alert.alert('Error', 'No se pudo acceder a las opciones de imagen');
        }
    };

    const takePhoto = async () => {
        try {
            const { status } = await ImagePicker.requestCameraPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Error', 'Se necesitan permisos para usar la cámara');
                return;
            }

            const result = await ImagePicker.launchCameraAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                allowsEditing: true,
                aspect: [1, 1],
                quality: 0.8,
            });

            if (!result.canceled && result.assets[0]) {
                setSelectedImage(result.assets[0].uri);
            }
        } catch (error) {
            Alert.alert('Error', 'No se pudo tomar la foto');
        }
    };

    const pickFromGallery = async () => {
        try {
            const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Error', 'Se necesitan permisos para acceder a la galería');
                return;
            }

            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                allowsEditing: true,
                aspect: [1, 1],
                quality: 0.8,
            });

            if (!result.canceled && result.assets[0]) {
                setSelectedImage(result.assets[0].uri);
            }
        } catch (error) {
            Alert.alert('Error', 'No se pudo seleccionar la imagen');
        }
    };

    const validateStep = (step: number) => {
        switch (step) {
            case 1:
                if (!selectedImage) {
                    Alert.alert('Error', 'La foto es obligatoria para el reconocimiento facial');
                    return false;
                }
                return true;
            case 2:
                if (!formData.nombre.trim()) {
                    Alert.alert('Error', 'El nombre es obligatorio');
                    return false;
                }
                if (!formData.apellidos.trim()) {
                    Alert.alert('Error', 'Los apellidos son obligatorios');
                    return false;
                }
                return true;
            case 3:
                if (!formData.codigo.trim()) {
                    Alert.alert('Error', 'El código es obligatorio');
                    return false;
                }
                if (!formData.correo.trim()) {
                    Alert.alert('Error', 'El correo es obligatorio');
                    return false;
                }
                if (!formData.correo.includes('@')) {
                    Alert.alert('Error', 'El correo debe tener un formato válido');
                    return false;
                }
                return true;
            default:
                return true;
        }
    };

    const nextStep = () => {
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                setCurrentStep(currentStep + 1);
                animateTransition();
            } else {
                submitForm();
            }
        }
    };

    const prevStep = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
            animateTransition();
        }
    };

    const animateTransition = () => {
        Animated.sequence([
            Animated.timing(fadeAnim, {
                toValue: 0.7,
                duration: 150,
                useNativeDriver: true,
            }),
            Animated.timing(fadeAnim, {
                toValue: 1,
                duration: 150,
                useNativeDriver: true,
            }),
        ]).start();
    };

    const submitForm = async () => {
        setIsSubmitting(true);
        try {
            const formDataToSend = new FormData();
            formDataToSend.append('nombre', formData.nombre.trim());
            formDataToSend.append('apellidos', formData.apellidos.trim());
            formDataToSend.append('codigo', formData.codigo.trim().toUpperCase());
            formDataToSend.append('correo', formData.correo.trim().toLowerCase());
            formDataToSend.append('requisitoriado', formData.requisitoriado.toString());

            formDataToSend.append('image', {
                uri: selectedImage,
                type: 'image/jpeg',
                name: `student_${formData.codigo}.jpg`,
            } as any);

            const response = await fetch(`${API_BASE}/api/students/`, {
                method: 'POST',
                body: formDataToSend,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            const data = await response.json();

            if (response.ok) {
                Alert.alert(
                    '✅ Éxito',
                    `Estudiante ${data.nombre} ${data.apellidos} registrado correctamente`,
                    [
                        {
                            text: 'OK',
                            onPress: () => {
                                setFormData({
                                    nombre: '',
                                    apellidos: '',
                                    codigo: '',
                                    correo: '',
                                    requisitoriado: false,
                                });
                                setSelectedImage(null);
                                setCurrentStep(1);
                                navigation.goBack();
                            },
                        },
                    ]
                );
            } else {
                Alert.alert('Error', data.detail || 'No se pudo registrar el estudiante');
            }
        } catch (error) {
            Alert.alert('Error', 'No se pudo conectar con el servidor');
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return renderPhotoStep();
            case 2:
                return renderPersonalDataStep();
            case 3:
                return renderContactDataStep();
            default:
                return null;
        }
    };

    const renderPhotoStep = () => (
        <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
            <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                <Card.Content style={styles.cardContent}>
                    <Text style={[styles.stepTitle, { color: theme.colors.primary }]}>
                        📷 Paso 1: Foto del Estudiante
                    </Text>
                    <Text style={[styles.stepDescription, { color: theme.colors.textSecondary }]}>
                        La foto es obligatoria para el reconocimiento facial
                    </Text>

                    {selectedImage ? (
                        <View style={styles.imageContainer}>
                            <View style={styles.imageWrapper}>
                                <Image source={{ uri: selectedImage }} style={styles.image} />
                                <LinearGradient
                                    colors={['transparent', 'rgba(0,0,0,0.3)']}
                                    style={styles.imageOverlay}
                                />
                            </View>
                            <Button
                                mode="outlined"
                                onPress={selectImage}
                                style={[styles.changeButton, { borderColor: theme.colors.primary }]}
                                labelStyle={{ color: theme.colors.primary }}
                            >
                                Cambiar Foto
                            </Button>
                        </View>
                    ) : (
                        <View style={styles.noImageContainer}>
                            <LinearGradient
                                colors={isDark ? ['#333', '#555'] : ['#F0F0F0', '#E0E0E0']}
                                style={styles.noImageGradient}
                            >
                                <Text style={styles.noImageIcon}>📷</Text>
                                <Text style={[styles.noImageText, { color: theme.colors.textSecondary }]}>
                                    Selecciona una foto
                                </Text>
                            </LinearGradient>
                            <Button
                                mode="contained"
                                onPress={selectImage}
                                style={[styles.selectButton, { backgroundColor: theme.colors.primary }]}
                                labelStyle={{ color: '#FFFFFF' }}
                            >
                                📸 Seleccionar Foto
                            </Button>
                        </View>
                    )}
                </Card.Content>
            </Card>
        </Animated.View>
    );

    const renderPersonalDataStep = () => (
        <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
            <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                <Card.Content>
                    <Text style={[styles.stepTitle, { color: theme.colors.primary }]}>
                        👤 Paso 2: Datos Personales
                    </Text>
                    <Text style={[styles.stepDescription, { color: theme.colors.textSecondary }]}>
                        Información básica del estudiante
                    </Text>

                    <TextInput
                        label="Nombre *"
                        value={formData.nombre}
                        onChangeText={(text) => setFormData({ ...formData, nombre: text })}
                        style={[styles.input, { backgroundColor: theme.colors.background }]}
                        mode="outlined"
                        outlineColor={theme.colors.border}
                        activeOutlineColor={theme.colors.primary}
                        textColor={theme.colors.text}
                    />

                    <TextInput
                        label="Apellidos *"
                        value={formData.apellidos}
                        onChangeText={(text) => setFormData({ ...formData, apellidos: text })}
                        style={[styles.input, { backgroundColor: theme.colors.background }]}
                        mode="outlined"
                        outlineColor={theme.colors.border}
                        activeOutlineColor={theme.colors.primary}
                        textColor={theme.colors.text}
                    />
                </Card.Content>
            </Card>
        </Animated.View>
    );

    const renderContactDataStep = () => (
        <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
            <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                <Card.Content>
                    <Text style={[styles.stepTitle, { color: theme.colors.primary }]}>
                        📝 Paso 3: Datos de Contacto
                    </Text>
                    <Text style={[styles.stepDescription, { color: theme.colors.textSecondary }]}>
                        Información de contacto y estado
                    </Text>

                    <TextInput
                        label="Código de Estudiante *"
                        value={formData.codigo}
                        onChangeText={(text) => setFormData({ ...formData, codigo: text.toUpperCase() })}
                        style={[styles.input, { backgroundColor: theme.colors.background }]}
                        mode="outlined"
                        placeholder="Ej: EST001, 2024001"
                        outlineColor={theme.colors.border}
                        activeOutlineColor={theme.colors.primary}
                        textColor={theme.colors.text}
                    />

                    <TextInput
                        label="Correo Electrónico *"
                        value={formData.correo}
                        onChangeText={(text) => setFormData({ ...formData, correo: text })}
                        style={[styles.input, { backgroundColor: theme.colors.background }]}
                        mode="outlined"
                        keyboardType="email-address"
                        autoCapitalize="none"
                        placeholder="estudiante@upao.edu.pe"
                        outlineColor={theme.colors.border}
                        activeOutlineColor={theme.colors.primary}
                        textColor={theme.colors.text}
                    />

                    {/* Switch responsivo */}
                    <Card style={[styles.switchCard, { backgroundColor: theme.colors.card }]}>
                        <Card.Content>
                            <View style={styles.switchContainer}>
                                <View style={styles.switchLeft}>
                                    <Text style={[styles.switchLabel, { color: theme.colors.text }]}>
                                        ⚠️ Estudiante Requisitoriado
                                    </Text>
                                    <Text style={[styles.switchSubtext, { color: theme.colors.textSecondary }]}>
                                        Marcar si tiene estado especial
                                    </Text>
                                </View>
                                <Switch
                                    value={formData.requisitoriado}
                                    onValueChange={(value) => setFormData({ ...formData, requisitoriado: value })}
                                    thumbColor={formData.requisitoriado ? theme.colors.error : theme.colors.textSecondary}
                                    trackColor={{ false: theme.colors.border, true: `${theme.colors.error}40` }}
                                />
                            </View>
                        </Card.Content>
                    </Card>
                </Card.Content>
            </Card>
        </Animated.View>
    );

    return (
        <Surface style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <KeyboardAvoidingView
                style={{ flex: 1 }}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                {/* Header con progreso */}
                <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
                    <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
                        Agregar Estudiante
                    </Text>
                    <ProgressBar
                        progress={progress}
                        color={theme.colors.primary}
                        style={[styles.progressBar, { backgroundColor: theme.colors.border }]}
                    />
                    <Text style={[styles.progressText, { color: theme.colors.textSecondary }]}>
                        Paso {currentStep} de {totalSteps}
                    </Text>
                </View>

                <ScrollView
                    style={styles.scrollView}
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                >
                    {renderStep()}

                    {/* Resumen de datos */}
                    {currentStep > 1 && (
                        <Card style={[styles.summaryCard, { backgroundColor: theme.colors.card }]}>
                            <Card.Content>
                                <Text style={[styles.summaryTitle, { color: theme.colors.primary }]}>
                                    📋 Resumen
                                </Text>
                                {selectedImage && (
                                    <Text style={[styles.summaryItem, { color: theme.colors.success }]}>
                                        ✅ Foto seleccionada
                                    </Text>
                                )}
                                {formData.nombre && (
                                    <Text style={[styles.summaryItem, { color: theme.colors.text }]}>
                                        👤 {formData.nombre} {formData.apellidos}
                                    </Text>
                                )}
                                {formData.codigo && (
                                    <Text style={[styles.summaryItem, { color: theme.colors.text }]}>
                                        🎓 {formData.codigo}
                                    </Text>
                                )}
                                {formData.correo && (
                                    <Text style={[styles.summaryItem, { color: theme.colors.text }]}>
                                        📧 {formData.correo}
                                    </Text>
                                )}
                            </Card.Content>
                        </Card>
                    )}
                </ScrollView>

                {/* Botones de navegación */}
                <View style={[styles.navigationContainer, { backgroundColor: theme.colors.surface }]}>
                    <View style={styles.buttonRow}>
                        {currentStep > 1 && (
                            <Button
                                mode="outlined"
                                onPress={prevStep}
                                style={[styles.navButton, { borderColor: theme.colors.border }]}
                                labelStyle={{ color: theme.colors.text }}
                                disabled={isSubmitting}
                            >
                                ← Anterior
                            </Button>
                        )}

                        <Button
                            mode="contained"
                            onPress={nextStep}
                            loading={isSubmitting}
                            disabled={isSubmitting}
                            style={[
                                styles.navButton,
                                styles.primaryButton,
                                { backgroundColor: theme.colors.primary },
                                currentStep === 1 && { flex: 1 }
                            ]}
                            labelStyle={{ color: '#FFFFFF' }}
                        >
                            {isSubmitting
                                ? 'Registrando...'
                                : currentStep === totalSteps
                                    ? '✅ Registrar'
                                    : 'Siguiente →'
                            }
                        </Button>
                    </View>
                </View>

                {/* Indicador de procesamiento */}
                {isSubmitting && (
                    <Card style={[styles.processingCard, { backgroundColor: theme.colors.surface }]}>
                        <Card.Content style={styles.processingContent}>
                            <ActivityIndicator size="large" color={theme.colors.primary} />
                            <Text style={[styles.processingText, { color: theme.colors.text }]}>
                                Registrando estudiante...
                            </Text>
                            <Text style={[styles.processingSubtext, { color: theme.colors.textSecondary }]}>
                                Subiendo foto y procesando datos faciales
                            </Text>
                        </Card.Content>
                    </Card>
                )}
            </KeyboardAvoidingView>
        </Surface>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    header: {
        paddingTop: hp(2),
        paddingHorizontal: responsive.layout.paddingHorizontal,
        paddingBottom: responsive.spacing.md,
        elevation: 2,
    },
    headerTitle: {
        ...baseStyles.text.subtitle,
        textAlign: 'center',
        marginBottom: responsive.spacing.sm,
    },
    progressBar: {
        height: wp(1),
        borderRadius: responsive.borderRadius.xs,
        marginBottom: responsive.spacing.xs,
    },
    progressText: {
        fontSize: responsive.fontSize.sm,
        textAlign: 'center',
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: responsive.layout.paddingHorizontal,
        paddingBottom: responsive.spacing.xxl,
    },
    stepContainer: {
        marginBottom: responsive.spacing.lg,
    },
    card: {
        ...baseStyles.card,
        ...baseStyles.shadow.medium,
    },
    cardContent: {
        alignItems: 'center',
    },
    stepTitle: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.sm,
        textAlign: 'center',
    },
    stepDescription: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
        marginBottom: responsive.spacing.lg,
    },
    imageContainer: {
        alignItems: 'center',
        width: '100%',
    },
    imageWrapper: {
        position: 'relative',
        marginBottom: responsive.spacing.md,
    },
    image: {
        width: responsive.screen.isSmall ? wp(35) : wp(40),
        height: responsive.screen.isSmall ? wp(35) : wp(40),
        borderRadius: responsive.borderRadius.lg,
    },
    imageOverlay: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: '30%',
        borderBottomLeftRadius: responsive.borderRadius.lg,
        borderBottomRightRadius: responsive.borderRadius.lg,
    },
    changeButton: {
        borderRadius: responsive.borderRadius.xl,
        minWidth: wp(30),
    },
    noImageContainer: {
        alignItems: 'center',
        width: '100%',
    },
    noImageGradient: {
        width: responsive.screen.isSmall ? wp(35) : wp(40),
        height: responsive.screen.isSmall ? wp(35) : wp(40),
        borderRadius: responsive.borderRadius.lg,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: responsive.spacing.md,
    },
    noImageIcon: {
        fontSize: responsive.screen.isSmall ? fp(40) : fp(48),
        marginBottom: responsive.spacing.sm,
    },
    noImageText: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
    },
    selectButton: {
        borderRadius: responsive.borderRadius.xl,
        minWidth: wp(40),
        height: responsive.heights.button,
    },
    input: {
        ...baseStyles.input,
        fontSize: responsive.fontSize.md,
    },
    switchCard: {
        ...baseStyles.card,
        marginTop: responsive.spacing.md,
    },
    switchContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    switchLeft: {
        flex: 1,
        marginRight: responsive.spacing.md,
    },
    switchLabel: {
        fontSize: responsive.fontSize.md,
        fontWeight: '600',
        marginBottom: responsive.spacing.xs,
    },
    switchSubtext: {
        fontSize: responsive.fontSize.sm,
        lineHeight: responsive.fontSize.sm * 1.3,
    },
    summaryCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.small,
        marginTop: responsive.spacing.lg,
    },
    summaryTitle: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.md,
    },
    summaryItem: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.xs,
    },
    navigationContainer: {
        paddingHorizontal: responsive.layout.paddingHorizontal,
        paddingVertical: responsive.spacing.md,
        elevation: 4,
    },
    buttonRow: {
        flexDirection: 'row',
        gap: responsive.spacing.md,
    },
    navButton: {
        flex: 1,
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button,
        justifyContent: 'center',
    },
    primaryButton: {
        elevation: 2,
    },
    processingCard: {
        position: 'absolute',
        top: '50%',
        left: responsive.layout.paddingHorizontal,
        right: responsive.layout.paddingHorizontal,
        transform: [{ translateY: -hp(10) }],
        ...baseStyles.shadow.large,
        borderRadius: responsive.borderRadius.xl,
    },
    processingContent: {
        alignItems: 'center',
        paddingVertical: responsive.spacing.xl,
    },
    processingText: {
        fontSize: responsive.fontSize.lg,
        fontWeight: '600',
        marginTop: responsive.spacing.md,
        textAlign: 'center',
    },
    processingSubtext: {
        fontSize: responsive.fontSize.md,
        marginTop: responsive.spacing.sm,
        textAlign: 'center',
        paddingHorizontal: responsive.spacing.lg,
    },
});