// mobile/screens/EditStudentScreen.tsx - VERSIÓN RESPONSIVA Y MODERNA
import React, { useState, useEffect } from 'react';
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
    Chip,
    Divider,
} from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';
import { responsive, baseStyles, wp, hp, fp } from '../utils/responsive';

const API_BASE = 'https://student-face-recognition-production.up.railway.app';

interface Student {
    id: number;
    nombre: string;
    apellidos: string;
    codigo: string;
    correo?: string;
    requisitoriado: boolean;
    imagen_path?: string;
}

export default function EditStudentScreen() {
    const navigation = useNavigation();
    const route = useRoute();
    const queryClient = useQueryClient();
    const { theme, isDark } = useTheme();
    const { student } = route.params as { student: Student };

    const [formData, setFormData] = useState({
        nombre: student.nombre,
        apellidos: student.apellidos,
        codigo: student.codigo,
        correo: student.correo || '',
        requisitoriado: student.requisitoriado,
    });
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
    const [showComparison, setShowComparison] = useState(false);
    const [fadeAnim] = useState(new Animated.Value(1));

    useEffect(() => {
        if (student.imagen_path) {
            const imageUrl = student.imagen_path.startsWith('http')
                ? student.imagen_path
                : `${API_BASE}${student.imagen_path}`;
            setCurrentImageUrl(imageUrl);
        }
    }, [student.imagen_path]);

    // Mutation para actualizar estudiante
    const updateMutation = useMutation({
        mutationFn: async (data: FormData) => {
            const response = await fetch(`${API_BASE}/api/students/${student.id}`, {
                method: 'PUT',
                body: data,
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al actualizar');
            }

            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            Alert.alert(
                '✅ Éxito',
                'Estudiante actualizado correctamente',
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.goBack(),
                    },
                ]
            );
        },
        onError: (error: any) => {
            Alert.alert('Error', error.message || 'No se pudo actualizar el estudiante');
        },
    });

    const selectImage = async () => {
        try {
            Alert.alert(
                'Cambiar Foto',
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
                setShowComparison(true);
                animateTransition();
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
                setShowComparison(true);
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

    const validateForm = () => {
        if (!formData.nombre.trim()) {
            Alert.alert('Error', 'El nombre es obligatorio');
            return false;
        }
        if (!formData.apellidos.trim()) {
            Alert.alert('Error', 'Los apellidos son obligatorios');
            return false;
        }
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
    };

    const submitForm = async () => {
        if (!validateForm()) return;

        const formDataToSend = new FormData();
        formDataToSend.append('nombre', formData.nombre.trim());
        formDataToSend.append('apellidos', formData.apellidos.trim());
        formDataToSend.append('codigo', formData.codigo.trim().toUpperCase());
        formDataToSend.append('correo', formData.correo.trim().toLowerCase());
        formDataToSend.append('requisitoriado', formData.requisitoriado.toString());

        if (selectedImage) {
            formDataToSend.append('image', {
                uri: selectedImage,
                type: 'image/jpeg',
                name: `student_${formData.codigo}_updated.jpg`,
            } as any);
        }

        updateMutation.mutate(formDataToSend);
    };

    const hasChanges = () => {
        return (
            formData.nombre !== student.nombre ||
            formData.apellidos !== student.apellidos ||
            formData.codigo !== student.codigo ||
            formData.correo !== (student.correo || '') ||
            formData.requisitoriado !== student.requisitoriado ||
            selectedImage !== null
        );
    };

    const renderImageComparison = () => {
        if (!showComparison || !selectedImage) return null;

        return (
            <Animated.View style={[styles.comparisonContainer, { opacity: fadeAnim }]}>
                <Card style={[styles.comparisonCard, { backgroundColor: theme.colors.surface }]}>
                    <Card.Content>
                        <Text style={[styles.comparisonTitle, { color: theme.colors.primary }]}>
                            🔄 Comparación de Fotos
                        </Text>

                        <View style={styles.imagesRow}>
                            {/* Foto actual */}
                            <View style={styles.imageComparisonItem}>
                                <Text style={[styles.imageLabel, { color: theme.colors.textSecondary }]}>
                                    Foto Actual
                                </Text>
                                {currentImageUrl ? (
                                    <View style={styles.imageWrapper}>
                                        <Image source={{ uri: currentImageUrl }} style={styles.comparisonImage} />
                                        <LinearGradient
                                            colors={['transparent', 'rgba(0,0,0,0.3)']}
                                            style={styles.imageOverlay}
                                        />
                                    </View>
                                ) : (
                                    <View style={[styles.noImagePlaceholder, { backgroundColor: theme.colors.background }]}>
                                        <Text style={styles.noImageIcon}>📷</Text>
                                        <Text style={[styles.noImageText, { color: theme.colors.textSecondary }]}>
                                            Sin foto
                                        </Text>
                                    </View>
                                )}
                            </View>

                            {/* Flecha */}
                            <View style={styles.arrowContainer}>
                                <Text style={styles.arrow}>→</Text>
                            </View>

                            {/* Foto nueva */}
                            <View style={styles.imageComparisonItem}>
                                <Text style={[styles.imageLabel, { color: theme.colors.success }]}>
                                    Foto Nueva
                                </Text>
                                <View style={styles.imageWrapper}>
                                    <Image source={{ uri: selectedImage }} style={styles.comparisonImage} />
                                    <LinearGradient
                                        colors={['transparent', 'rgba(76, 175, 80, 0.3)']}
                                        style={styles.imageOverlay}
                                    />
                                    <View style={styles.newBadge}>
                                        <Text style={styles.newBadgeText}>NUEVA</Text>
                                    </View>
                                </View>
                            </View>
                        </View>

                        <Button
                            mode="outlined"
                            onPress={() => {
                                setSelectedImage(null);
                                setShowComparison(false);
                            }}
                            style={[styles.cancelImageButton, { borderColor: theme.colors.error }]}
                            labelStyle={{ color: theme.colors.error }}
                        >
                            ❌ Cancelar Cambio
                        </Button>
                    </Card.Content>
                </Card>
            </Animated.View>
        );
    };

    return (
        <Surface style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <KeyboardAvoidingView
                style={{ flex: 1 }}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                <ScrollView
                    style={styles.scrollView}
                    contentContainerStyle={styles.scrollContent}
                    showsVerticalScrollIndicator={false}
                >
                    {/* Header del estudiante */}
                    <Card style={[styles.headerCard, { backgroundColor: theme.colors.surface }]}>
                        <Card.Content>
                            <View style={styles.studentHeader}>
                                <View style={styles.studentInfo}>
                                    <Text style={[styles.studentName, { color: theme.colors.primary }]}>
                                        {student.nombre} {student.apellidos}
                                    </Text>
                                    <Text style={[styles.studentCode, { color: theme.colors.textSecondary }]}>
                                        ID: {student.id} • Código: {student.codigo}
                                    </Text>
                                    <View style={styles.statusChips}>
                                        <Chip
                                            icon="camera"
                                            mode="outlined"
                                            style={[
                                                styles.statusChip,
                                                { borderColor: student.imagen_path ? theme.colors.success : theme.colors.error }
                                            ]}
                                            textStyle={{
                                                color: student.imagen_path ? theme.colors.success : theme.colors.error,
                                                fontSize: responsive.fontSize.xs
                                            }}
                                        >
                                            {student.imagen_path ? 'Con foto' : 'Sin foto'}
                                        </Chip>
                                        {student.requisitoriado && (
                                            <Chip
                                                icon="alert"
                                                mode="outlined"
                                                style={[styles.statusChip, { borderColor: theme.colors.warning }]}
                                                textStyle={{ color: theme.colors.warning, fontSize: responsive.fontSize.xs }}
                                            >
                                                Requisitoriado
                                            </Chip>
                                        )}
                                    </View>
                                </View>
                            </View>
                        </Card.Content>
                    </Card>

                    {/* Foto principal o comparación */}
                    {showComparison ? renderImageComparison() : (
                        <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                            <Card.Content style={styles.cardContent}>
                                <Text style={[styles.sectionTitle, { color: theme.colors.primary }]}>
                                    📷 Foto del Estudiante
                                </Text>

                                <View style={styles.imageContainer}>
                                    {currentImageUrl ? (
                                        <View style={styles.imageWrapper}>
                                            <Image source={{ uri: currentImageUrl }} style={styles.image} />
                                            <LinearGradient
                                                colors={['transparent', 'rgba(0,0,0,0.3)']}
                                                style={styles.imageOverlay}
                                            />
                                        </View>
                                    ) : (
                                        <View style={[styles.noImageContainer, { backgroundColor: theme.colors.background }]}>
                                            <Text style={styles.noImageIcon}>📷</Text>
                                            <Text style={[styles.imageInstructions, { color: theme.colors.textSecondary }]}>
                                                Sin foto actual
                                            </Text>
                                        </View>
                                    )}

                                    <Button
                                        mode="contained"
                                        onPress={selectImage}
                                        style={[styles.changeButton, { backgroundColor: theme.colors.primary }]}
                                        labelStyle={{ color: '#FFFFFF' }}
                                    >
                                        📸 {currentImageUrl ? 'Actualizar Foto' : 'Agregar Foto'}
                                    </Button>
                                </View>
                            </Card.Content>
                        </Card>
                    )}

                    {/* Formulario de datos */}
                    <Card style={[styles.card, { backgroundColor: theme.colors.surface }]}>
                        <Card.Content>
                            <Text style={[styles.sectionTitle, { color: theme.colors.primary }]}>
                                📝 Editar Datos
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

                            <TextInput
                                label="Código de Estudiante *"
                                value={formData.codigo}
                                onChangeText={(text) => setFormData({ ...formData, codigo: text.toUpperCase() })}
                                style={[styles.input, { backgroundColor: theme.colors.background }]}
                                mode="outlined"
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
                                outlineColor={theme.colors.border}
                                activeOutlineColor={theme.colors.primary}
                                textColor={theme.colors.text}
                            />

                            <Divider style={[styles.divider, { backgroundColor: theme.colors.border }]} />

                            {/* Switch para requisitoriado */}
                            <View style={styles.switchContainer}>
                                <View style={styles.switchLeft}>
                                    <Text style={[styles.switchLabel, { color: theme.colors.text }]}>
                                        ⚠️ Estudiante Requisitoriado
                                    </Text>
                                    <Text style={[styles.switchSubtext, { color: theme.colors.textSecondary }]}>
                                        Estado especial del estudiante
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

                    {/* Resumen de cambios */}
                    {hasChanges() && (
                        <Card style={[styles.changesCard, { backgroundColor: theme.colors.card }]}>
                            <Card.Content>
                                <Text style={[styles.changesTitle, { color: theme.colors.warning }]}>
                                    📝 Cambios Pendientes
                                </Text>
                                {selectedImage && (
                                    <Text style={[styles.changeItem, { color: theme.colors.success }]}>
                                        ✅ Nueva foto seleccionada
                                    </Text>
                                )}
                                {formData.nombre !== student.nombre && (
                                    <Text style={[styles.changeItem, { color: theme.colors.text }]}>
                                        👤 Nombre: {student.nombre} → {formData.nombre}
                                    </Text>
                                )}
                                {formData.apellidos !== student.apellidos && (
                                    <Text style={[styles.changeItem, { color: theme.colors.text }]}>
                                        👤 Apellidos: {student.apellidos} → {formData.apellidos}
                                    </Text>
                                )}
                                {formData.codigo !== student.codigo && (
                                    <Text style={[styles.changeItem, { color: theme.colors.text }]}>
                                        🎓 Código: {student.codigo} → {formData.codigo}
                                    </Text>
                                )}
                                {formData.correo !== (student.correo || '') && (
                                    <Text style={[styles.changeItem, { color: theme.colors.text }]}>
                                        📧 Email: {student.correo || 'Sin email'} → {formData.correo}
                                    </Text>
                                )}
                                {formData.requisitoriado !== student.requisitoriado && (
                                    <Text style={[styles.changeItem, { color: theme.colors.warning }]}>
                                        ⚠️ Estado: {student.requisitoriado ? 'Requisitoriado' : 'Normal'} → {formData.requisitoriado ? 'Requisitoriado' : 'Normal'}
                                    </Text>
                                )}
                            </Card.Content>
                        </Card>
                    )}
                </ScrollView>

                {/* Botones de acción */}
                <View style={[styles.actionContainer, { backgroundColor: theme.colors.surface }]}>
                    <View style={styles.buttonRow}>
                        <Button
                            mode="outlined"
                            onPress={() => navigation.goBack()}
                            style={[styles.actionButton, { borderColor: theme.colors.border }]}
                            labelStyle={{ color: theme.colors.text }}
                            disabled={updateMutation.isPending}
                        >
                            ❌ Cancelar
                        </Button>

                        <Button
                            mode="contained"
                            onPress={submitForm}
                            loading={updateMutation.isPending}
                            disabled={updateMutation.isPending || !hasChanges()}
                            style={[
                                styles.actionButton,
                                styles.primaryButton,
                                {
                                    backgroundColor: hasChanges() ? theme.colors.success : theme.colors.border,
                                    opacity: hasChanges() ? 1 : 0.6
                                }
                            ]}
                            labelStyle={{ color: '#FFFFFF' }}
                        >
                            {updateMutation.isPending ? 'Actualizando...' : '✅ Guardar Cambios'}
                        </Button>
                    </View>
                </View>

                {/* Indicador de procesamiento */}
                {updateMutation.isPending && (
                    <Card style={[styles.processingCard, { backgroundColor: theme.colors.surface }]}>
                        <Card.Content style={styles.processingContent}>
                            <ActivityIndicator size="large" color={theme.colors.primary} />
                            <Text style={[styles.processingText, { color: theme.colors.text }]}>
                                Actualizando estudiante...
                            </Text>
                            <Text style={[styles.processingSubtext, { color: theme.colors.textSecondary }]}>
                                {selectedImage ? 'Subiendo nueva foto y actualizando datos' : 'Actualizando datos del estudiante'}
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
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: responsive.layout.paddingHorizontal,
        paddingBottom: hp(10), // Espacio para botones
    },
    headerCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.medium,
        marginBottom: responsive.spacing.lg,
    },
    studentHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    studentInfo: {
        flex: 1,
    },
    studentName: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.xs,
    },
    studentCode: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.sm,
    },
    statusChips: {
        flexDirection: 'row',
        gap: responsive.spacing.sm,
    },
    statusChip: {
        height: hp(3.5),
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
    noImageContainer: {
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
    imageInstructions: {
        fontSize: responsive.fontSize.sm,
        textAlign: 'center',
    },
    changeButton: {
        borderRadius: responsive.borderRadius.xl,
        minWidth: wp(40),
        height: responsive.heights.button,
    },
    comparisonContainer: {
        marginBottom: responsive.spacing.lg,
    },
    comparisonCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.large,
    },
    comparisonTitle: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.lg,
        textAlign: 'center',
    },
    imagesRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: responsive.spacing.lg,
    },
    imageComparisonItem: {
        flex: 1,
        alignItems: 'center',
    },
    imageLabel: {
        fontSize: responsive.fontSize.sm,
        fontWeight: '600',
        marginBottom: responsive.spacing.sm,
        textAlign: 'center',
    },
    comparisonImage: {
        width: wp(28),
        height: wp(28),
        borderRadius: responsive.borderRadius.md,
    },
    noImagePlaceholder: {
        width: wp(28),
        height: wp(28),
        borderRadius: responsive.borderRadius.md,
        justifyContent: 'center',
        alignItems: 'center',
    },
    noImageText: {
        fontSize: responsive.fontSize.xs,
        textAlign: 'center',
    },
    arrowContainer: {
        paddingHorizontal: responsive.spacing.md,
    },
    arrow: {
        fontSize: responsive.fontSize.xxl,
        color: '#666',
    },
    newBadge: {
        position: 'absolute',
        top: -responsive.spacing.xs,
        right: -responsive.spacing.xs,
        backgroundColor: '#4CAF50',
        borderRadius: responsive.borderRadius.sm,
        paddingHorizontal: responsive.spacing.xs,
        paddingVertical: responsive.spacing.xs / 2,
    },
    newBadgeText: {
        color: '#FFFFFF',
        fontSize: responsive.fontSize.xs,
        fontWeight: 'bold',
    },
    cancelImageButton: {
        borderRadius: responsive.borderRadius.xl,
    },
    input: {
        ...baseStyles.input,
        fontSize: responsive.fontSize.md,
    },
    divider: {
        marginVertical: responsive.spacing.lg,
    },
    switchContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: responsive.spacing.md,
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
    changesCard: {
        ...baseStyles.card,
        ...baseStyles.shadow.small,
        marginTop: responsive.spacing.lg,
    },
    changesTitle: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.md,
    },
    changeItem: {
        fontSize: responsive.fontSize.sm,
        marginBottom: responsive.spacing.xs,
        lineHeight: responsive.fontSize.sm * 1.4,
    },
    actionContainer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        paddingHorizontal: responsive.layout.paddingHorizontal,
        paddingVertical: responsive.spacing.md,
        elevation: 8,
    },
    buttonRow: {
        flexDirection: 'row',
        gap: responsive.spacing.md,
    },
    actionButton: {
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