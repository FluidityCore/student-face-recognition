// mobile/screens/StudentsListScreen.tsx - VERSIÓN CORREGIDA CON NAVEGACIÓN TIPADA
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
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '../context/ThemeContext';

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

// Servicios API
const apiService = {
    getStudents: async () => {
        try {
            const response = await fetch(`${API_BASE}/api/students`);
            if (!response.ok) throw new Error('Error al cargar estudiantes');
            return response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    },

    deleteStudent: async (id: number) => {
        try {
            const response = await fetch(`${API_BASE}/api/students/${id}`, {
                method: 'DELETE',
            });
            if (!response.ok) throw new Error('Error al eliminar estudiante');
            return response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    },
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

export default function StudentsListScreen() {
    const navigation = useNavigation<NavigationProp>();
    const queryClient = useQueryClient();
    const { theme, isDark } = useTheme();
    const [searchQuery, setSearchQuery] = useState('');

    // Query para obtener estudiantes
    const {
        data: students = [],
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['students'],
        queryFn: apiService.getStudents,
        retry: 1,
    });

    // Mutation para eliminar
    const deleteMutation = useMutation({
        mutationFn: apiService.deleteStudent,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            Alert.alert('✅ Éxito', 'Estudiante eliminado correctamente');
        },
        onError: (error: any) => {
            Alert.alert('Error', 'No se pudo eliminar el estudiante');
            console.error('Delete error:', error);
        },
    });

    // Filtrar estudiantes de forma segura
    const filteredStudents = students.filter((student: Student) => {
        if (!student || !searchQuery) return true;

        const searchLower = searchQuery.toLowerCase();
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
        // ✅ CORRECCIÓN: Navegación tipada correctamente
        navigation.navigate('EditStudent', { student });
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
                                    <Text style={[styles.alertStatus, { color: theme.colors.error }]}>
                                        ⚠️ Requisitoriado
                                    </Text>
                                )}
                                <Text style={[
                                    styles.imageStatus,
                                    { color: student.imagen_path ? theme.colors.success : theme.colors.error }
                                ]}>
                                    {student.imagen_path ? '📷 Con foto' : '📷 Sin foto'}
                                </Text>
                            </View>
                        </View>

                        {/* Acciones */}
                        <View style={styles.actions}>
                            <IconButton
                                icon="pencil"
                                size={24}
                                iconColor={theme.colors.primary}
                                onPress={() => editStudent(student)}
                                style={[styles.actionButton, { backgroundColor: `${theme.colors.primary}15` }]}
                            />
                            <IconButton
                                icon="delete"
                                size={24}
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
                👥 Estudiantes ({students.length})
            </Text>

            <Searchbar
                placeholder="Buscar por nombre, código o email..."
                onChangeText={setSearchQuery}
                value={searchQuery}
                style={[styles.searchBar, { backgroundColor: theme.colors.surface }]}
                inputStyle={{ color: theme.colors.text }}
                iconColor={theme.colors.textSecondary}
            />

            {/* Estadísticas mejoradas */}
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
        </View>
    );

    const renderEmpty = () => (
        <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>👥</Text>
            <Text style={[styles.emptyTitle, { color: theme.colors.text }]}>
                {students.length === 0 ? 'No hay estudiantes' : 'No se encontraron estudiantes'}
            </Text>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
                {students.length === 0
                    ? 'Agrega el primer estudiante usando el botón "Agregar Estudiante"'
                    : 'Intenta con diferentes términos de búsqueda'
                }
            </Text>
            {students.length === 0 && (
                <Button
                    mode="contained"
                    onPress={() => navigation.navigate('AddStudent')}
                    style={[styles.addButton, { backgroundColor: theme.colors.primary }]}
                    labelStyle={{ color: '#FFFFFF' }}
                >
                    ➕ Agregar Estudiante
                </Button>
            )}
        </View>
    );

    if (isLoading) {
        return (
            <Surface style={[styles.container, styles.centered, { backgroundColor: theme.colors.background }]}>
                <ActivityIndicator size="large" color={theme.colors.primary} />
                <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
                    Cargando estudiantes...
                </Text>
            </Surface>
        );
    }

    if (error) {
        return (
            <Surface style={[styles.container, styles.centered, { backgroundColor: theme.colors.background }]}>
                <Text style={styles.errorIcon}>❌</Text>
                <Text style={[styles.errorTitle, { color: theme.colors.error }]}>Error al cargar</Text>
                <Text style={[styles.errorText, { color: theme.colors.textSecondary }]}>
                    No se pudieron cargar los estudiantes
                </Text>
                <Button
                    mode="contained"
                    onPress={() => refetch()}
                    style={[styles.retryButton, { backgroundColor: theme.colors.primary }]}
                    labelStyle={{ color: '#FFFFFF' }}
                >
                    🔄 Reintentar
                </Button>
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
                        refreshing={isLoading}
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
        padding: 16,
        flexGrow: 1,
    },
    header: {
        marginBottom: 16,
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 16,
        textAlign: 'center',
    },
    searchBar: {
        marginBottom: 16,
        elevation: 3,
        borderRadius: 16,
    },
    statsCard: {
        borderRadius: 16,
        elevation: 3,
        marginBottom: 16,
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
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    statLabel: {
        fontSize: 12,
        textAlign: 'center',
    },
    statDivider: {
        width: 1,
        height: 40,
        marginHorizontal: 16,
    },
    studentCard: {
        marginBottom: 12,
        elevation: 3,
        borderRadius: 16,
    },
    studentHeader: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    studentInfo: {
        flex: 1,
    },
    studentName: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    studentCode: {
        fontSize: 14,
        marginBottom: 2,
    },
    studentEmail: {
        fontSize: 14,
        marginBottom: 4,
    },
    statusContainer: {
        flexDirection: 'row',
        gap: 12,
    },
    alertStatus: {
        fontSize: 12,
        fontWeight: 'bold',
    },
    imageStatus: {
        fontSize: 12,
        fontWeight: '500',
    },
    actions: {
        flexDirection: 'row',
        gap: 8,
    },
    actionButton: {
        borderRadius: 12,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyIcon: {
        fontSize: 64,
        marginBottom: 16,
    },
    emptyTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 8,
        textAlign: 'center',
    },
    emptyText: {
        fontSize: 16,
        textAlign: 'center',
        marginBottom: 24,
        paddingHorizontal: 32,
    },
    addButton: {
        minWidth: 180,
        borderRadius: 24,
    },
    loadingText: {
        marginTop: 16,
        fontSize: 16,
    },
    errorIcon: {
        fontSize: 64,
        marginBottom: 16,
    },
    errorTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 8,
    },
    errorText: {
        fontSize: 16,
        textAlign: 'center',
        marginBottom: 24,
    },
    retryButton: {
        minWidth: 140,
        borderRadius: 24,
    },
});