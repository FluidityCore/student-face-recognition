// mobile/screens/StudentsListScreen.tsx - VERSIÓN CORREGIDA PARA APK
import React, { useState } from 'react';
import {
    View,
    StyleSheet,
    FlatList,
    Alert,
    RefreshControl,
} from 'react-native';
import {
    Surface,
    Text,
    Card,
    IconButton,
    Searchbar,
    ActivityIndicator,
    Button,
    Chip,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '../context/ThemeContext';
import {responsive, baseStyles, wp, hp, fp} from '../utils/responsive';

// Tipos de navegación
type RootStackParamList = {
    Menu: undefined;
    Recognize: undefined;
    AddStudent: undefined;
    StudentsList: undefined;
    EditStudent: { student: Student };
};

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const API_BASE = 'https://student-face-recognition-production.up.railway.app';

// Configuración mejorada para requests
const makeRequest = async (endpoint: string, options: any = {}) => {
    const {
        method = 'GET',
        body,
        headers = {},
        timeout = 15000,
        retries = 3
    } = options;

    const url = `${API_BASE}${endpoint}`;

    console.log(`🌐 API Request: ${method} ${url}`);

    const requestHeaders: Record<string, string> = {
        'Accept': 'application/json',
        ...headers
    };

    if (!(body instanceof FormData)) {
        requestHeaders['Content-Type'] = 'application/json';
    }

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            console.log(`📡 Intento ${attempt}/${retries} para ${endpoint}`);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);

            const requestBody = body instanceof FormData ? body :
                (body ? JSON.stringify(body) : undefined);

            const response = await fetch(url, {
                method,
                headers: requestHeaders,
                body: requestBody,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            console.log(`📊 Response Status: ${response.status} for ${endpoint}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ API Error ${response.status}:`, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            console.log(`✅ Success for ${endpoint}`);

            return data;

        } catch (error: any) {
            lastError = error;
            console.error(`❌ Attempt ${attempt} failed for ${endpoint}:`, error.message);

            if (attempt === retries) {
                throw lastError;
            }

            // Esperar antes del siguiente intento
            const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
            console.log(`⏳ Esperando ${delay}ms antes del siguiente intento...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw lastError || new Error('Request failed after all retries');
};

// Servicios API mejorados
const apiService = {
    getStudents: async () => {
        try {
            console.log('📋 Obteniendo lista de estudiantes...');
            const students = await makeRequest('/api/students', {
                timeout: 20000,
                retries: 5
            });

            return Array.isArray(students) ? students : [];
        } catch (error: any) {
            console.error('❌ Error obteniendo estudiantes:', error.message);
            throw new Error(`No se pudieron cargar los estudiantes: ${error.message}`);
        }
    },

    deleteStudent: async (id: number) => {
        try {
            console.log(`🗑️ Eliminando estudiante ${id}...`);
            const result = await makeRequest(`/api/students/${id}`, {
                method: 'DELETE',
                timeout: 15000,
                retries: 3
            });
            return result;
        } catch (error: any) {
            console.error('❌ Error eliminando estudiante:', error.message);
            throw new Error(`Error eliminando estudiante: ${error.message}`);
        }
    },

    healthCheck: async () => {
        try {
            return await makeRequest('/health', {
                timeout: 10000,
                retries: 2
            });
        } catch (error: any) {
            console.error('❌ Health check failed:', error.message);
            throw error;
        }
    }
};

interface Student {
    id: number;
    nombre: string;
    apellidos: string;
    codigo: string;
    correo?: string;
    requisitoriado: boolean;
    imagen_path?: string;
    created_at: string;
}

// Componente de debug de conectividad
const NetworkDebugger: React.FC = () => {
    const { theme } = useTheme();
    const [testResult, setTestResult] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);

    const runTests = async () => {
        setIsLoading(true);
        setTestResult('🔧 Ejecutando pruebas de conectividad...\n');

        try {
            // Test 1: Health check
            try {
                const health = await apiService.healthCheck();
                setTestResult(prev => prev + `✅ Health check: ${health.status || 'OK'}\n`);
            } catch (error: any) {
                setTestResult(prev => prev + `❌ Health check: ${error.message}\n`);
            }

            // Test 2: Obtener estudiantes
            try {
                const students = await apiService.getStudents();
                setTestResult(prev => prev + `✅ Estudiantes: ${students.length} encontrados\n`);
            } catch (error: any) {
                setTestResult(prev => prev + `❌ Estudiantes: ${error.message}\n`);
            }

        } catch (error: any) {
            setTestResult(prev => prev + `❌ Error general: ${error.message}\n`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card style={[styles.debugCard, { backgroundColor: theme.colors.surface }]}>
            <Card.Content>
                <Text style={[styles.debugTitle, { color: theme.colors.text }]}>
                    🔧 Debug de Red
                </Text>
                <Button
                    mode="contained"
                    onPress={runTests}
                    loading={isLoading}
                    disabled={isLoading}
                    style={{ backgroundColor: theme.colors.primary }}
                >
                    🧪 Ejecutar Pruebas
                </Button>
                {testResult ? (
                    <Text style={[styles.debugResult, { color: theme.colors.text }]}>
                        {testResult}
                    </Text>
                ) : null}
            </Card.Content>
        </Card>
    );
};

export default function StudentsListScreen() {
    const navigation = useNavigation<NavigationProp>();
    const queryClient = useQueryClient();
    const { theme, isDark } = useTheme();
    const [searchQuery, setSearchQuery] = useState('');
    const [showDebugger, setShowDebugger] = useState(false);

    // Query para obtener estudiantes con mejor manejo de errores
    const {
        data: students = [],
        isLoading,
        error,
        refetch,
        isRefetching,
    } = useQuery({
        queryKey: ['students'],
        queryFn: apiService.getStudents,
        retry: (failureCount, error: any) => {
            console.log(`🔄 Retry attempt ${failureCount} for students`);
            return failureCount < 3;
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        staleTime: 5 * 60 * 1000, // 5 minutos
        gcTime: 10 * 60 * 1000, // 10 minutos
    });

    // Mutation para eliminar
    const deleteMutation = useMutation({
        mutationFn: apiService.deleteStudent,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            Alert.alert('✅ Éxito', 'Estudiante eliminado correctamente');
        },
        onError: (error: any) => {
            Alert.alert('Error', `No se pudo eliminar: ${error.message}`);
            console.error('Delete error:', error);
        },
        retry: 2,
    });

    // Log para debugging
    React.useEffect(() => {
        console.log('📋 StudentsListScreen mounted');
        console.log('📊 Students data:', students?.length || 0, 'items');
        if (error) {
            console.error('❌ Students error:', error);
        }
    }, [students, error]);

    // Filtrar estudiantes de forma segura
    const filteredStudents = React.useMemo(() => {
        if (!Array.isArray(students)) {
            console.warn('⚠️ Students is not an array:', typeof students);
            return [];
        }

        if (!searchQuery.trim()) {
            return students;
        }

        const searchLower = searchQuery.toLowerCase();
        return students.filter((student: Student) => {
            if (!student) return false;

            const nombre = student.nombre || '';
            const apellidos = student.apellidos || '';
            const codigo = student.codigo || '';
            const correo = student.correo || '';

            return (
                nombre.toLowerCase().includes(searchLower) ||
                apellidos.toLowerCase().includes(searchLower) ||
                codigo.toLowerCase().includes(searchLower) ||
                correo.toLowerCase().includes(searchLower)
            );
        });
    }, [students, searchQuery]);

    const confirmDelete = (student: Student) => {
        Alert.alert(
            'Confirmar Eliminación',
            `¿Eliminar a ${student.nombre} ${student.apellidos}?`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: () => deleteMutation.mutate(student.id),
                },
            ]
        );
    };

    const editStudent = (student: Student) => {
        navigation.navigate('EditStudent', { student });
    };

    const retryLoad = async () => {
        try {
            console.log('🔄 Retry manual triggered');
            await refetch();
        } catch (error) {
            console.error('❌ Manual retry failed:', error);
        }
    };

    const renderStudent = ({ item: student }: { item: Student }) => {
        if (!student) return null;

        return (
            <Card style={[styles.studentCard, { backgroundColor: theme.colors.surface }]}>
                <Card.Content>
                    <View style={styles.studentHeader}>
                        {/* Información del estudiante */}
                        <View style={styles.studentInfo}>
                            <Text style={[styles.studentName, { color: theme.colors.primary }]}>
                                👤 {student.nombre || ''} {student.apellidos || ''}
                            </Text>
                            <Text style={[styles.studentCode, { color: theme.colors.textSecondary }]}>
                                📚 Código: {student.codigo || 'Sin código'}
                            </Text>
                            {student.correo && (
                                <Text style={[styles.studentEmail, { color: theme.colors.textSecondary }]}>
                                    📧 {student.correo}
                                </Text>
                            )}

                            {/* Estados */}
                            <View style={styles.statusContainer}>
                                {student.requisitoriado && (
                                    <Chip
                                        icon="alert"
                                        mode="flat"
                                        style={[styles.alertChip, { backgroundColor: `${theme.colors.error}20` }]}
                                        textStyle={{ color: theme.colors.error, fontSize: responsive.fontSize.xs }}
                                    >
                                        Requisitoriado
                                    </Chip>
                                )}
                                <Chip
                                    icon={student.imagen_path ? "camera" : "camera-off"}
                                    mode="flat"
                                    style={[
                                        styles.imageChip,
                                        {
                                            backgroundColor: student.imagen_path
                                                ? `${theme.colors.success}20`
                                                : `${theme.colors.error}20`
                                        }
                                    ]}
                                    textStyle={{
                                        color: student.imagen_path ? theme.colors.success : theme.colors.error,
                                        fontSize: responsive.fontSize.xs
                                    }}
                                >
                                    {student.imagen_path ? 'Con foto' : 'Sin foto'}
                                </Chip>
                            </View>
                        </View>

                        {/* Acciones */}
                        <View style={styles.actions}>
                            <IconButton
                                icon="pencil"
                                size={responsive.iconSize.md}
                                iconColor={theme.colors.primary}
                                onPress={() => editStudent(student)}
                                style={[styles.actionButton, { backgroundColor: `${theme.colors.primary}15` }]}
                            />
                            <IconButton
                                icon="delete"
                                size={responsive.iconSize.md}
                                iconColor={theme.colors.error}
                                onPress={() => confirmDelete(student)}
                                disabled={deleteMutation.isPending}
                                style={[styles.actionButton, { backgroundColor: `${theme.colors.error}15` }]}
                            />
                        </View>
                    </View>
                </Card.Content>
            </Card>
        );
    };

    const renderHeader = () => (
        <View style={styles.header}>
            <Text style={[styles.title, { color: theme.colors.primary }]}>
                👥 Estudiantes ({Array.isArray(students) ? students.length : 0})
            </Text>

            <Searchbar
                placeholder="Buscar por nombre, código o email..."
                onChangeText={setSearchQuery}
                value={searchQuery}
                style={[styles.searchBar, { backgroundColor: theme.colors.surface }]}
                inputStyle={{ color: theme.colors.text }}
                iconColor={theme.colors.textSecondary}
            />

            {/* Estadísticas */}
            {Array.isArray(students) && students.length > 0 && (
                <Card style={[styles.statsCard, { backgroundColor: theme.colors.surface }]}>
                    <Card.Content>
                        <View style={styles.stats}>
                            <View style={styles.statItem}>
                                <Text style={[styles.statNumber, { color: theme.colors.primary }]}>
                                    {students.length}
                                </Text>
                                <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
                                    Total
                                </Text>
                            </View>
                            <View style={[styles.statDivider, { backgroundColor: theme.colors.border }]} />
                            <View style={styles.statItem}>
                                <Text style={[styles.statNumber, { color: theme.colors.success }]}>
                                    {students.filter((s: Student) => s?.imagen_path).length}
                                </Text>
                                <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
                                    Con Foto
                                </Text>
                            </View>
                            <View style={[styles.statDivider, { backgroundColor: theme.colors.border }]} />
                            <View style={styles.statItem}>
                                <Text style={[styles.statNumber, { color: theme.colors.warning }]}>
                                    {students.filter((s: Student) => s?.requisitoriado).length}
                                </Text>
                                <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
                                    Requisitoriados
                                </Text>
                            </View>
                        </View>
                    </Card.Content>
                </Card>
            )}

            {/* Botones de control */}
            <View style={styles.controlButtons}>
                <Button
                    mode="outlined"
                    onPress={retryLoad}
                    loading={isRefetching}
                    disabled={isLoading || isRefetching}
                    style={[styles.controlButton, { borderColor: theme.colors.primary }]}
                    labelStyle={{ color: theme.colors.primary, fontSize: responsive.fontSize.sm }}
                >
                    🔄 Recargar
                </Button>
                <Button
                    mode="outlined"
                    onPress={() => setShowDebugger(!showDebugger)}
                    style={[styles.controlButton, { borderColor: theme.colors.info }]}
                    labelStyle={{ color: theme.colors.info, fontSize: responsive.fontSize.sm }}
                >
                    🔧 Debug
                </Button>
            </View>

            {/* Debugger de red */}
            {showDebugger && <NetworkDebugger />}
        </View>
    );

    const renderEmpty = () => (
        <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>
                {error ? '❌' : searchQuery ? '🔍' : '👥'}
            </Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.text }]}>
                {error
                    ? 'Error de Conexión'
                    : searchQuery
                        ? 'No se encontraron estudiantes'
                        : 'No hay estudiantes registrados'
                }
            </Text>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
                {error
                    ? `Error: ${error.message}. Verifica tu conexión a internet.`
                    : searchQuery
                        ? 'Intenta con diferentes términos de búsqueda'
                        : 'Agrega el primer estudiante usando el botón "Agregar Estudiante"'
                }
            </Text>
            {!error && !searchQuery && (
                <Button
                    mode="contained"
                    onPress={() => navigation.navigate('AddStudent')}
                    style={[styles.addButton, { backgroundColor: theme.colors.primary }]}
                    labelStyle={{ color: '#FFFFFF' }}
                >
                    ➕ Agregar Estudiante
                </Button>
            )}
            {error && (
                <Button
                    mode="contained"
                    onPress={retryLoad}
                    loading={isRefetching}
                    style={[styles.retryButton, { backgroundColor: theme.colors.primary }]}
                    labelStyle={{ color: '#FFFFFF' }}
                >
                    🔄 Reintentar
                </Button>
            )}
        </View>
    );

    if (isLoading && !isRefetching) {
        return (
            <Surface style={[styles.container, styles.centered, { backgroundColor: theme.colors.background }]}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
                <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
                    Cargando estudiantes...
                </Text>
            </Surface>
        );
    }

    return (
        <Surface style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <FlatList
                data={filteredStudents}
                renderItem={renderStudent}
                keyExtractor={(item) => item?.id?.toString() || Math.random().toString()}
                ListHeaderComponent={renderHeader}
                ListEmptyComponent={renderEmpty}
                refreshControl={
                    <RefreshControl
                        refreshing={isRefetching}
                        onRefresh={refetch}
                        colors={[theme.colors.primary]}
                        tintColor={theme.colors.primary}
                    />
                }
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
            />
        </Surface>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    centered: {
        justifyContent: 'center',
        alignItems: 'center',
    },
    listContent: {
        padding: responsive.layout.paddingHorizontal,
        flexGrow: 1,
    },
    header: {
        marginBottom: responsive.spacing.lg,
    },
    title: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.lg,
        textAlign: 'center',
    },
    searchBar: {
        marginBottom: responsive.spacing.lg,
        elevation: 3,
        borderRadius: responsive.borderRadius.xl,
    },
    statsCard: {
        ...baseStyles.card,
        marginBottom: responsive.spacing.lg,
    },
    stats: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    statItem: {
        flex: 1,
        alignItems: 'center',
    },
    statNumber: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.xs,
    },
    statLabel: {
        fontSize: responsive.fontSize.sm,
        textAlign: 'center',
    },
    statDivider: {
        width: 1,
        height: hp(5),
        marginHorizontal: responsive.spacing.md,
    },
    controlButtons: {
        flexDirection: 'row',
        gap: responsive.spacing.sm,
        marginBottom: responsive.spacing.md,
    },
    controlButton: {
        flex: 1,
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button * 0.8,
    },
    studentCard: {
        ...baseStyles.card,
        marginBottom: responsive.spacing.md,
    },
    studentHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    studentInfo: {
        flex: 1,
    },
    studentName: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.xs,
    },
    studentCode: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.xs,
    },
    studentEmail: {
        fontSize: responsive.fontSize.md,
        marginBottom: responsive.spacing.sm,
    },
    statusContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: responsive.spacing.sm,
    },
    alertChip: {
        height: hp(3),
        borderRadius: responsive.borderRadius.md,
    },
    imageChip: {
        height: hp(3),
        borderRadius: responsive.borderRadius.md,
    },
    actions: {
        flexDirection: 'row',
        gap: responsive.spacing.sm,
    },
    actionButton: {
        borderRadius: responsive.borderRadius.md,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: hp(8),
        paddingHorizontal: responsive.spacing.xl,
    },
    emptyIcon: {
        fontSize: fp(64),
        marginBottom: responsive.spacing.lg,
    },
    emptyTitle: {
        fontSize: responsive.fontSize.xl,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.sm,
        textAlign: 'center',
    },
    emptyText: {
        fontSize: responsive.fontSize.md,
        textAlign: 'center',
        marginBottom: responsive.spacing.xl,
        lineHeight: responsive.fontSize.md * 1.4,
    },
    addButton: {
        minWidth: wp(45),
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button,
    },
    retryButton: {
        minWidth: wp(35),
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button,
    },
    loadingText: {
        marginTop: responsive.spacing.lg,
        fontSize: responsive.fontSize.lg,
    },
    debugCard: {
        ...baseStyles.card,
        marginTop: responsive.spacing.md,
    },
    debugTitle: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.md,
    },
    debugResult: {
        marginTop: responsive.spacing.lg,
        fontFamily: 'monospace',
        fontSize: responsive.fontSize.sm,
        backgroundColor: '#f5f5f5',
        padding: responsive.spacing.sm,
        borderRadius: responsive.borderRadius.sm,
    },
});