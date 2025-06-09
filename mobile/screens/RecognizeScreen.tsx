// mobile/screens/RecognizeScreen.tsx - VERSIÓN RESPONSIVA Y MODERNA
import React, { useState } from 'react';
import {
    View,
    StyleSheet,
    Image,
    Alert,
    ScrollView,
    Animated,
} from 'react-native';
import {
    Surface,
    Button,
    Text,
    Card,
    ActivityIndicator,
    Chip,
    ProgressBar,
} from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';
import { responsive, baseStyles, wp, hp, fp } from '../utils/responsive';

const API_BASE = 'https://student-face-recognition-production.up.railway.app';

interface RecognitionResult {
    found: boolean;
    student?: {
        id: number;
        nombre: string;
        apellidos: string;
        codigo: string;
        correo?: string;
        requisitoriado: boolean;
    };
    similarity: number;
    confidence: string;
    processing_time: number;
}

export default function RecognizeScreen() {
    const { theme, isDark } = useTheme();
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<RecognitionResult | null>(null);
    const [processingProgress, setProcessingProgress] = useState(0);
    const [fadeAnim] = useState(new Animated.Value(1));

    const selectImage = async () => {
        try {
            const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Error', 'Se necesitan permisos para acceder a la galería');
                return;
            }

            Alert.alert(
                'Seleccionar Imagen',
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
                setResult(null);
                animateTransition();
            }
        } catch (error) {
            Alert.alert('Error', 'No se pudo tomar la foto');
        }
    };

    const pickFromGallery = async () => {
        try {
            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                allowsEditing: true,
                aspect: [1, 1],
                quality: 0.8,
            });

            if (!result.canceled && result.assets[0]) {
                setSelectedImage(result.assets[0].uri);
                setResult(null);
                animateTransition();
            }
        } catch (error) {
            Alert.alert('Error', 'No se pudo seleccionar la imagen');
        }
    };

    const animateTransition = () => {
        Animated.sequence([
            Animated.timing(fadeAnim, {
                toValue: 0.7,
                duration: 200,
                useNativeDriver: true,
            }),
            Animated.timing(fadeAnim, {
                toValue: 1,
                duration: 200,
                useNativeDriver: true,
            }),
        ]).start();
    };

    const simulateProgress = () => {
        const progressInterval = setInterval(() => {
            setProcessingProgress(prev => {
                if (prev >= 0.9) {
                    clearInterval(progressInterval);
                    return 0.9;
                }
                return prev + 0.1;
            });
        }, 200);
        return progressInterval;
    };

    const recognizeStudent = async () => {
        if (!selectedImage) {
            Alert.alert('Error', 'Selecciona una imagen primero');
            return;
        }

        setIsProcessing(true);
        setProcessingProgress(0);

        const progressInterval = simulateProgress();

        try {
            const formData = new FormData();
            formData.append('image', {
                uri: selectedImage,
                type: 'image/jpeg',
                name: 'recognition.jpg',
            } as any);

            const response = await fetch(`${API_BASE}/api/recognize`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            const data = await response.json();

            clearInterval(progressInterval);
            setProcessingProgress(1);

            setTimeout(() => {
                if (response.ok) {
                    setResult(data);
                    animateTransition();

                    if (data.found) {
                        const student = data.student;
                        Alert.alert(
                            data.student.requisitoriado ? '⚠️ ESTUDIANTE REQUISITORIADO' : '✅ Estudiante Encontrado',
                            `${student.nombre} ${student.apellidos}\nCódigo: ${student.codigo}\nConfianza: ${data.confidence}`,
                            [{ text: 'OK' }]
                        );
                    } else {
                        Alert.alert('❌ No Encontrado', 'No se encontró coincidencia con ningún estudiante registrado');
                    }
                } else {
                    Alert.alert('Error', data.detail || 'Error en el reconocimiento');
                }
            }, 500);
        } catch (error) {
            clearInterval(progressInterval);
            Alert.alert('Error', 'No se pudo conectar con el servidor');
        } finally {
            setTimeout(() => {
                setIsProcessing(false);
                setProcessingProgress(0);
            }, 1000);
        }
    };

    const clearAll = () => {
        setSelectedImage(null);
        setResult(null);
        setProcessingProgress(0);
        animateTransition();
    };

    const getConfidenceColor = (confidence: string) => {
        switch (confidence.toLowerCase()) {
            case 'high':
                return theme.colors.success;
            case 'medium':
                return theme.colors.warning;
            case 'low':
                return theme.colors.error;
            default:
                return theme.colors.textSecondary;
        }
    };

    const getConfidenceText = (confidence: string) => {
        switch (confidence.toLowerCase()) {
            case 'high':
                return 'Alta Confianza';
            case 'medium':
                return 'Confianza Media';
            case 'low':
                return 'Baja Confianza';
            default:
                return confidence;
        }
    };

    const renderImageSelector = () => (
        <Animated.View style={[styles.selectorContainer, { opacity: fadeAnim }]}>
            <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                <Card.Content style={styles.cardContent}>
                    {selectedImage ? (
                        <View style={styles.imageContainer}>
                            <Text style={[styles.sectionTitle, { color: theme.colors.primary }]}>
                                📷 Imagen Seleccionada
                            </Text>

                            <View style={styles.imageWrapper}>
                                <Image source={{ uri: selectedImage }} style={styles.image} />
                                <LinearGradient
                                    colors={['transparent', 'rgba(0,0,0,0.4)']}
                                    style={styles.imageOverlay}
                                />
                                <View style={styles.imageBadge}>
                                    <Text style={styles.imageBadgeText}>LISTO</Text>
                                </View>
                            </View>

                            <View style={styles.imageActions}>
                                <Button
                                    mode="outlined"
                                    onPress={selectImage}
                                    style={[styles.actionButton, { borderColor: theme.colors.border }]}
                                    labelStyle={{ color: theme.colors.text }}
                                    disabled={isProcessing}
                                >
                                    🔄 Cambiar
                                </Button>

                                <Button
                                    mode="contained"
                                    onPress={recognizeStudent}
                                    loading={isProcessing}
                                    disabled={isProcessing}
                                    style={[styles.actionButton, styles.recognizeButton, { backgroundColor: theme.colors.primary }]}
                                    labelStyle={{ color: '#FFFFFF' }}
                                >
                                    {isProcessing ? 'Procesando...' : '🔍 Reconocer'}
                                </Button>
                            </View>
                        </View>
                    ) : (
                        <View style={styles.noImageContainer}>
                            <LinearGradient
                                colors={isDark ? ['#2C2C2C', '#1E1E1E'] : ['#F8F9FA', '#E9ECEF']}
                                style={styles.noImageGradient}
                            >
                                <Text style={styles.noImageIcon}>🔍</Text>
                                <Text style={[styles.noImageTitle, { color: theme.colors.text }]}>
                                    Reconocimiento Facial
                                </Text>
                                <Text style={[styles.noImageSubtitle, { color: theme.colors.textSecondary }]}>
                                    Selecciona una imagen para identificar al estudiante
                                </Text>
                            </LinearGradient>

                            <Button
                                mode="contained"
                                onPress={selectImage}
                                style={[styles.selectButton, { backgroundColor: theme.colors.primary }]}
                                labelStyle={{ color: '#FFFFFF' }}
                            >
                                📸 Seleccionar Imagen
                            </Button>
                        </View>
                    )}
                </Card.Content>
            </Card>
        </Animated.View>
    );

    const renderProcessingIndicator = () => {
        if (!isProcessing) return null;

        return (
            <Card style={[styles.processingCard, { backgroundColor: theme.colors.surface }]}>
                <Card.Content style={styles.processingContent}>
                    <ActivityIndicator size="large" color={theme.colors.primary} />
                    <Text style={[styles.processingTitle, { color: theme.colors.text }]}>
                        🧠 Procesando Reconocimiento
                    </Text>
                    <Text style={[styles.processingSubtext, { color: theme.colors.textSecondary }]}>
                        Analizando características faciales...
                    </Text>

                    <View style={styles.progressContainer}>
                        <ProgressBar
                            progress={processingProgress}
                            color={theme.colors.primary}
                            style={[styles.progressBar, { backgroundColor: theme.colors.border }]}
                        />
                        <Text style={[styles.progressText, { color: theme.colors.textSecondary }]}>
                            {Math.round(processingProgress * 100)}%
                        </Text>
                    </View>

                    <View style={styles.processingSteps}>
                        <Text style={[styles.stepText, {
                            color: processingProgress > 0.3 ? theme.colors.success : theme.colors.textSecondary
                        }]}>
                            {processingProgress > 0.3 ? '✅' : '⏳'} Detectando rostro
                        </Text>
                        <Text style={[styles.stepText, {
                            color: processingProgress > 0.6 ? theme.colors.success : theme.colors.textSecondary
                        }]}>
                            {processingProgress > 0.6 ? '✅' : '⏳'} Extrayendo características
                        </Text>
                        <Text style={[styles.stepText, {
                            color: processingProgress > 0.9 ? theme.colors.success : theme.colors.textSecondary
                        }]}>
                            {processingProgress > 0.9 ? '✅' : '⏳'} Comparando con base de datos
                        </Text>
                    </View>
                </Card.Content>
            </Card>
        );
    };

    const renderResult = () => {
        if (!result) return null;

        return (
            <Animated.View style={[styles.resultContainer, { opacity: fadeAnim }]}>
                <Card style={[
                    styles.resultCard,
                    { backgroundColor: theme.colors.surface },
                    result.found ? styles.successCard : styles.failureCard
                ]}>
                    <Card.Content>
                        <View style={styles.resultHeader}>
                            <Text style={[styles.resultIcon, {
                                color: result.found ? theme.colors.success : theme.colors.error
                            }]}>
                                {result.found ? '✅' : '❌'}
                            </Text>
                            <Text style={[styles.resultTitle, { color: theme.colors.text }]}>
                                {result.found ? 'Estudiante Encontrado' : 'Sin Coincidencia'}
                            </Text>
                        </View>

                        {result.found && result.student ? (
                            <View style={styles.studentResult}>
                                <Text style={[styles.studentName, { color: theme.colors.primary }]}>
                                    👤 {result.student.nombre} {result.student.apellidos}
                                </Text>

                                <View style={styles.studentDetails}>
                                    <Text style={[styles.studentDetail, { color: theme.colors.text }]}>
                                        🎓 Código: {result.student.codigo}
                                    </Text>
                                    {result.student.correo && (
                                        <Text style={[styles.studentDetail, { color: theme.colors.text }]}>
                                            📧 {result.student.correo}
                                        </Text>
                                    )}
                                </View>

                                {/* Estado del estudiante */}
                                <View style={styles.statusContainer}>
                                    {result.student.requisitoriado && (
                                        <Chip
                                            icon="alert"
                                            mode="flat"
                                            style={[styles.alertChip, { backgroundColor: `${theme.colors.error}20` }]}
                                            textStyle={{ color: theme.colors.error, fontWeight: 'bold' }}
                                        >
                                            ⚠️ REQUISITORIADO
                                        </Chip>
                                    )}

                                    <Chip
                                        icon="check-circle"
                                        mode="flat"
                                        style={[styles.statusChip, { backgroundColor: `${getConfidenceColor(result.confidence)}20` }]}
                                        textStyle={{ color: getConfidenceColor(result.confidence), fontWeight: '600' }}
                                    >
                                        {getConfidenceText(result.confidence)}
                                    </Chip>
                                </View>

                                {/* Métricas de reconocimiento */}
                                <Card style={[styles.metricsCard, { backgroundColor: theme.colors.background }]}>
                                    <Card.Content style={styles.metricsContent}>
                                        <View style={styles.metricItem}>
                                            <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                                                Similitud
                                            </Text>
                                            <Text style={[styles.metricValue, { color: theme.colors.success }]}>
                                                {(result.similarity * 100).toFixed(1)}%
                                            </Text>
                                        </View>

                                        <View style={styles.metricDivider} />

                                        <View style={styles.metricItem}>
                                            <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                                                Tiempo
                                            </Text>
                                            <Text style={[styles.metricValue, { color: theme.colors.info }]}>
                                                {result.processing_time.toFixed(1)}s
                                            </Text>
                                        </View>
                                    </Card.Content>
                                </Card>
                            </View>
                        ) : (
                            <View style={styles.noMatchContainer}>
                                <Text style={[styles.noMatchText, { color: theme.colors.textSecondary }]}>
                                    No se encontró coincidencia con estudiantes registrados
                                </Text>
                                <Text style={[styles.noMatchSubtext, { color: theme.colors.textSecondary }]}>
                                    • Verifica que la imagen sea clara
                                </Text>
                                <Text style={[styles.noMatchSubtext, { color: theme.colors.textSecondary }]}>
                                    • Asegúrate de que el rostro sea visible
                                </Text>
                                <Text style={[styles.noMatchSubtext, { color: theme.colors.textSecondary }]}>
                                    • El estudiante debe estar registrado
                                </Text>
                            </View>
                        )}
                    </Card.Content>
                </Card>
            </Animated.View>
        );
    };

    return (
        <Surface style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                {renderImageSelector()}
                {renderProcessingIndicator()}
                {renderResult()}

                {/* Botón limpiar */}
                {(selectedImage || result) && !isProcessing && (
                    <View style={styles.clearContainer}>
                        <Button
                            mode="outlined"
                            onPress={clearAll}
                            style={[styles.clearButton, { borderColor: theme.colors.border }]}
                            labelStyle={{ color: theme.colors.text }}
                        >
                            🗑️ Limpiar Todo
                        </Button>
                    </View>
                )}

                {/* Información útil */}
                <Card style={[styles.infoCard, { backgroundColor: theme.colors.card }]}>
                    <Card.Content>
                        <Text style={[styles.infoTitle, { color: theme.colors.primary }]}>
                            ℹ️ Consejos para mejor reconocimiento
                        </Text>
                        <View style={styles.tipsList}>
                            <Text style={[styles.tipItem, { color: theme.colors.textSecondary }]}>
                                • Usa imágenes con buena iluminación
                            </Text>
                            <Text style={[styles.tipItem, { color: theme.colors.textSecondary }]}>
                                • Asegúrate de que el rostro sea visible
                            </Text>
                            <Text style={[styles.tipItem, { color: theme.colors.textSecondary }]}>
                                • Evita sombras excesivas en la cara
                            </Text>
                            <Text style={[styles.tipItem, { color: theme.colors.textSecondary }]}>
                                • El estudiante debe estar registrado en el sistema
                            </Text>
                        </View>
                    </Card.Content>
                </Card>
            </ScrollView>
        </Surface>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: responsive.layout.paddingHorizontal,
        paddingBottom: responsive.spacing.xxl,
    },
    selectorContainer: {
        marginBottom: responsive.spacing.lg,
    },
    card: {
        ...baseStyles.card,
        ...baseStyles.shadow.medium,
    },
    cardContent: {
        alignItems: 'center',
    },
    sectionTitle: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.lg,
        textAlign: 'center',
    },
    imageContainer: {
        alignItems: 'center',
        width: '100%',
    },
    imageWrapper: {
        position: 'relative',
        marginBottom: responsive.spacing.lg,
    },
    image: {
        width: responsive.screen.isSmall ? wp(50) : wp(55),
        height: responsive.screen.isSmall ? wp(50) : wp(55),
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
    imageBadge: {
        position: 'absolute',
        top: -responsive.spacing.sm,
        right: -responsive.spacing.sm,
        backgroundColor: '#4CAF50',
        borderRadius: responsive.borderRadius.sm,
        paddingHorizontal: responsive.spacing.sm,
        paddingVertical: responsive.spacing.xs,
    },
    imageBadgeText: {
        color: '#FFFFFF',
        fontSize: responsive.fontSize.xs,
        fontWeight: 'bold',
    },
    imageActions: {
        flexDirection: 'row',
        gap: responsive.spacing.md,
        width: '100%',
        justifyContent: 'center',
    },
    actionButton: {
        flex: 1,
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button,
        maxWidth: wp(35),
    },
    recognizeButton: {
        elevation: 2,
    },
    noImageContainer: {
        alignItems: 'center',
        width: '100%',
    },
    noImageGradient: {
        width: '100%',
        paddingVertical: responsive.spacing.xxl,
        borderRadius: responsive.borderRadius.lg,
        alignItems: 'center',
        marginBottom: responsive.spacing.lg,
    },
    noImageIcon: {
        fontSize: responsive.screen.isSmall ? fp(60) : fp(72),
        marginBottom: responsive.spacing.md,
    },
    noImageTitle: {
        fontSize: responsive.fontSize.xxl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.sm,
        textAlign: 'center',
    },
    noImageSubtitle: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
        paddingHorizontal: responsive.spacing.lg,
        lineHeight: responsive.fontSize.md * 1.4,
    },
    selectButton: {
        borderRadius: responsive.borderRadius.xl,
        minWidth: wp(50),
        height: responsive.heights.button,
    },
    processingCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.large,
        marginBottom: responsive.spacing.lg,
    },
    processingContent: {
        alignItems: 'center',
        paddingVertical: responsive.spacing.xl,
    },
    processingTitle: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginTop: responsive.spacing.md,
        marginBottom: responsive.spacing.sm,
        textAlign: 'center',
    },
    processingSubtext: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
        marginBottom: responsive.spacing.lg,
    },
    progressContainer: {
        width: '100%',
        marginBottom: responsive.spacing.lg,
    },
    progressBar: {
        height: wp(1.5),
        borderRadius: responsive.borderRadius.xs,
        marginBottom: responsive.spacing.sm,
    },
    progressText: {
        fontSize: responsive.fontSize.sm,
        textAlign: 'center',
        fontWeight: '600',
    },
    processingSteps: {
        alignItems: 'flex-start',
        width: '100%',
    },
    stepText: {
        fontSize: responsive.fontSize.sm,
        marginBottom: responsive.spacing.xs,
        textAlign: 'left',
    },
    resultContainer: {
        marginBottom: responsive.spacing.lg,
    },
    resultCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.large,
    },
    successCard: {
        borderLeftWidth: wp(1),
        borderLeftColor: '#4CAF50',
    },
    failureCard: {
        borderLeftWidth: wp(1),
        borderLeftColor: '#F44336',
    },
    resultHeader: {
        alignItems: 'center',
        marginBottom: responsive.spacing.lg,
    },
    resultIcon: {
        fontSize: responsive.fontSize.header,
        marginBottom: responsive.spacing.sm,
    },
    resultTitle: {
        fontSize: responsive.fontSize.xxl,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    studentResult: {
        width: '100%',
    },
    studentName: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: responsive.spacing.md,
    },
    studentDetails: {
        alignItems: 'center',
        marginBottom: responsive.spacing.lg,
    },
    studentDetail: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.xs,
        textAlign: 'center',
    },
    statusContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: responsive.spacing.sm,
        marginBottom: responsive.spacing.lg,
    },
    alertChip: {
        borderRadius: responsive.borderRadius.xl,
    },
    statusChip: {
        borderRadius: responsive.borderRadius.xl,
    },
    metricsCard: {
        ...baseStyles.card,
        marginTop: responsive.spacing.md,
    },
    metricsContent: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-around',
    },
    metricItem: {
        alignItems: 'center',
        flex: 1,
    },
    metricLabel: {
        fontSize: responsive.fontSize.sm,
        marginBottom: responsive.spacing.xs,
    },
    metricValue: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
    },
    metricDivider: {
        width: 1,
        height: hp(4),
        backgroundColor: '#E0E0E0',
        marginHorizontal: responsive.spacing.md,
    },
    noMatchContainer: {
        alignItems: 'center',
        paddingVertical: responsive.spacing.lg,
    },
    noMatchText: {
        fontSize: responsive.fontSize.lg,
        textAlign: 'center',
        marginBottom: responsive.spacing.lg,
        fontWeight: '600',
    },
    noMatchSubtext: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
        marginBottom: responsive.spacing.xs,
        lineHeight: responsive.fontSize.md * 1.3,
    },
    clearContainer: {
        alignItems: 'center',
        marginBottom: responsive.spacing.lg,
    },
    clearButton: {
        borderRadius: responsive.borderRadius.xl,
        minWidth: wp(40),
        height: responsive.heights.button,
    },
    infoCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.small,
    },
    infoTitle: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.md,
        textAlign: 'center',
    },
    tipsList: {
        paddingLeft: responsive.spacing.md,
    },
    tipItem: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.sm,
        lineHeight: responsive.fontSize.md * 1.4,
    },
});