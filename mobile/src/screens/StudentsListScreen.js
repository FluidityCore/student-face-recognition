import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    SafeAreaView,
    FlatList,
    TextInput,
    TouchableOpacity,
    Alert,
    ActivityIndicator,
    RefreshControl,
    Image,
} from 'react-native';
import ApiService from '../services/ApiService';

const StudentsListScreen = ({ navigation }) => {
    const [students, setStudents] = useState([]);
    const [filteredStudents, setFilteredStudents] = useState([]);
    const [searchText, setSearchText] = useState('');
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadStudents();
    }, []);

    const filterStudents = useCallback(() => {
        if (!searchText.trim()) {
            setFilteredStudents(students);
            return;
        }
        const filtered = students.filter(student =>
            student.nombre.toLowerCase().includes(searchText.toLowerCase()) ||
            student.apellidos.toLowerCase().includes(searchText.toLowerCase()) ||
            student.codigo.toLowerCase().includes(searchText.toLowerCase()) ||
            student.correo.toLowerCase().includes(searchText.toLowerCase())
        );
        setFilteredStudents(filtered);
    }, [searchText, students]);

    useEffect(() => {
        filterStudents();
    }, [filterStudents]);

    const loadStudents = async () => {
        try {
            setLoading(true);
            const studentsData = await ApiService.getStudents();
            setStudents(studentsData);
        } catch (error) {
            Alert.alert(
                'Error',
                'No se pudieron cargar los estudiantes. Verifica tu conexión.'
            );
            console.error('Error loading students:', error);
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await loadStudents();
        setRefreshing(false);
    };

    const handleDeleteStudent = (student) => {
        Alert.alert(
            'Eliminar Estudiante',
            `¿Estás seguro de que deseas eliminar a ${student.nombre} ${student.apellidos}?`,
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Eliminar',
                    style: 'destructive',
                    onPress: () => deleteStudent(student.id)
                }
            ]
        );
    };

    const deleteStudent = async (studentId) => {
        try {
            await ApiService.deleteStudent(studentId);
            Alert.alert('Éxito', 'Estudiante eliminado correctamente');
            loadStudents(); // Recargar lista
        } catch (error) {
            Alert.alert('Error', 'No se pudo eliminar el estudiante');
            console.error('Error deleting student:', error);
        }
    };

    const handleEditStudent = (student) => {
        navigation.navigate('EditStudent', { student });
    };

    const renderStudentItem = ({ item }) => (
        <View style={styles.studentCard}>
            <View style={styles.studentInfo}>
                <View style={styles.studentImageContainer}>
                    <StudentImage studentId={item.id} />
                </View>

                <View style={styles.studentDetails}>
                    <Text style={styles.studentName}>
                        {item.nombre} {item.apellidos}
                    </Text>
                    <Text style={styles.studentCode}>📋 {item.codigo}</Text>
                    <Text style={styles.studentEmail}>📧 {item.correo}</Text>
                    {item.requisitoriado && (
                        <Text style={styles.alertStatus}>⚠️ REQUISITORIADO</Text>
                    )}
                </View>
            </View>

            <View style={styles.actionButtons}>
                <TouchableOpacity
                    style={[styles.actionButton, styles.editButton]}
                    onPress={() => handleEditStudent(item)}
                >
                    <Text style={styles.actionButtonText}>✏️ Editar</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.actionButton, styles.deleteButton]}
                    onPress={() => handleDeleteStudent(item)}
                >
                    <Text style={styles.actionButtonText}>🗑️ Eliminar</Text>
                </TouchableOpacity>
            </View>
        </View>
    );

    const renderEmptyComponent = () => (
        <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle}>📭 No hay estudiantes</Text>
            <Text style={styles.emptySubtitle}>
                {searchText ? 'No se encontraron resultados para tu búsqueda' : 'Aún no se han registrado estudiantes'}
            </Text>
            {!searchText && (
                <TouchableOpacity
                    style={styles.addButton}
                    onPress={() => navigation.navigate('CreateStudent')}
                >
                    <Text style={styles.addButtonText}>➕ Agregar Primer Estudiante</Text>
                </TouchableOpacity>
            )}
        </View>
    );

    if (loading) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#2196F3" />
                    <Text style={styles.loadingText}>Cargando estudiantes...</Text>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>👥 Lista de Estudiantes</Text>
                <Text style={styles.subtitle}>
                    {students.length} estudiante{students.length !== 1 ? 's' : ''} registrado{students.length !== 1 ? 's' : ''}
                </Text>
            </View>

            <View style={styles.searchContainer}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="🔍 Buscar por nombre, código o email..."
                    value={searchText}
                    onChangeText={setSearchText}
                />
            </View>

            <FlatList
                data={filteredStudents}
                renderItem={renderStudentItem}
                keyExtractor={(item) => item.id.toString()}
                style={styles.list}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                }
                ListEmptyComponent={renderEmptyComponent}
                showsVerticalScrollIndicator={false}
            />

            {students.length > 0 && (
                <TouchableOpacity
                    style={styles.floatingAddButton}
                    onPress={() => navigation.navigate('CreateStudent')}
                >
                    <Text style={styles.floatingAddButtonText}>➕</Text>
                </TouchableOpacity>
            )}
        </SafeAreaView>
    );
};

// Componente separado para manejar la imagen del estudiante
const StudentImage = ({ studentId }) => {
    const [imageError, setImageError] = useState(false);

    const imageUrl = ApiService.getStudentImageUrl(studentId);

    if (imageError) {
        // Mostrar avatar por defecto si hay error cargando la imagen
        return (
            <View style={styles.defaultAvatar}>
                <Text style={styles.defaultAvatarText}>👤</Text>
            </View>
        );
    }

    return (
        <Image
            source={{ uri: imageUrl }}
            style={styles.studentImage}
            onError={() => setImageError(true)}
        />
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    header: {
        padding: 20,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333',
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
        marginTop: 5,
    },
    searchContainer: {
        padding: 15,
        backgroundColor: '#fff',
    },
    searchInput: {
        backgroundColor: '#f8f9fa',
        borderRadius: 10,
        paddingHorizontal: 15,
        paddingVertical: 12,
        fontSize: 16,
        borderWidth: 1,
        borderColor: '#e0e0e0',
    },
    list: {
        flex: 1,
        paddingHorizontal: 15,
    },
    studentCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 15,
        marginVertical: 5,
        elevation: 2,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
    },
    studentInfo: {
        flexDirection: 'row',
        marginBottom: 15,
    },
    studentImageContainer: {
        marginRight: 15,
    },
    studentImage: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#e0e0e0',
    },
    defaultAvatar: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#e0e0e0',
        justifyContent: 'center',
        alignItems: 'center',
    },
    defaultAvatarText: {
        fontSize: 24,
        color: '#999',
    },
    studentDetails: {
        flex: 1,
    },
    studentName: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 4,
    },
    studentCode: {
        fontSize: 14,
        color: '#666',
        marginBottom: 2,
    },
    studentEmail: {
        fontSize: 14,
        color: '#666',
        marginBottom: 2,
    },
    alertStatus: {
        fontSize: 12,
        color: '#f44336',
        fontWeight: 'bold',
        marginTop: 4,
    },
    actionButtons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 10,
    },
    actionButton: {
        flex: 1,
        paddingVertical: 8,
        paddingHorizontal: 15,
        borderRadius: 8,
        alignItems: 'center',
    },
    editButton: {
        backgroundColor: '#2196F3',
    },
    deleteButton: {
        backgroundColor: '#f44336',
    },
    actionButtonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold',
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 10,
        fontSize: 16,
        color: '#666',
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 50,
    },
    emptyTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#666',
        marginBottom: 10,
    },
    emptySubtitle: {
        fontSize: 16,
        color: '#999',
        textAlign: 'center',
        marginBottom: 30,
        paddingHorizontal: 20,
    },
    addButton: {
        backgroundColor: '#4CAF50',
        paddingVertical: 12,
        paddingHorizontal: 25,
        borderRadius: 10,
    },
    addButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: 'bold',
    },
    floatingAddButton: {
        position: 'absolute',
        right: 20,
        bottom: 20,
        backgroundColor: '#4CAF50',
        width: 56,
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 8,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
    },
    floatingAddButtonText: {
        color: '#fff',
        fontSize: 24,
        fontWeight: 'bold',
    },
});

export default StudentsListScreen;