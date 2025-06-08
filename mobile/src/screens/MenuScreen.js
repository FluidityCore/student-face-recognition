import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
    SafeAreaView,
    ScrollView,
    Alert,
    ActivityIndicator,
} from 'react-native';
import ApiService from '../services/ApiService';

const MenuScreen = ({ navigation }) => {
    const [serverStatus, setServerStatus] = useState(null);
    const [studentsCount, setStudentsCount] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            // Verificar estado del servidor
            await ApiService.checkHealth();
            setServerStatus('connected');

            // Obtener cantidad de estudiantes
            const students = await ApiService.getStudents();
            setStudentsCount(students.length);

        } catch (error) {
            setServerStatus('disconnected');
            console.error('Error loading initial data:', error);
        } finally {
            setLoading(false);
        }
    };

    const menuOptions = [
        {
            id: 1,
            title: '📷 Reconocimiento Facial',
            subtitle: 'Identificar estudiante por foto',
            screen: 'Recognition',
            color: '#2196F3',
            requiresConnection: true,
        },
        {
            id: 2,
            title: '👥 Ver Estudiantes',
            subtitle: `${studentsCount} estudiante${studentsCount !== 1 ? 's' : ''} registrado${studentsCount !== 1 ? 's' : ''}`,
            screen: 'StudentsList',
            color: '#4CAF50',
            requiresConnection: true,
        },
        {
            id: 3,
            title: '➕ Nuevo Estudiante',
            subtitle: 'Registrar nuevo estudiante',
            screen: 'CreateStudent',
            color: '#FF9800',
            requiresConnection: true,
        },
        {
            id: 4,
            title: '⚙️ Configuración',
            subtitle: 'Ajustes y preferencias',
            screen: 'Settings',
            color: '#9C27B0',
            requiresConnection: false,
        },
    ];

    const handleMenuPress = (option) => {
        // Verificar si la opción requiere conexión y no hay conexión
        if (option.requiresConnection && serverStatus !== 'connected') {
            Alert.alert(
                'Sin Conexión',
                'Esta función requiere conexión con el servidor. Por favor, verifica tu conexión.',
                [
                    { text: 'Reintentar', onPress: loadInitialData },
                    { text: 'Cancelar', style: 'cancel' }
                ]
            );
            return;
        }

        navigation.navigate(option.screen);
    };

    const handleRefresh = () => {
        loadInitialData();
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content}>

                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.title}>🎓 Sistema de Reconocimiento Facial</Text>
                    <Text style={styles.subtitle}>Gestión de Estudiantes</Text>

                    {/* Estado del servidor */}
                    <View style={styles.statusContainer}>
                        <View style={[
                            styles.statusIndicator,
                            {
                                backgroundColor: loading ? '#FFC107' :
                                    serverStatus === 'connected' ? '#4CAF50' : '#f44336'
                            }
                        ]} />
                        <Text style={styles.statusText}>
                            {loading ? 'Conectando...' :
                                serverStatus === 'connected' ? 'Servidor Conectado' : 'Sin Conexión'}
                        </Text>
                        {!loading && (
                            <TouchableOpacity
                                style={styles.refreshButton}
                                onPress={handleRefresh}
                            >
                                <Text style={styles.refreshButtonText}>🔄</Text>
                            </TouchableOpacity>
                        )}
                    </View>
                </View>

                {/* Loading indicator */}
                {loading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#2196F3" />
                        <Text style={styles.loadingText}>Cargando datos...</Text>
                    </View>
                )}

                {/* Menu Options */}
                <View style={styles.menuContainer}>
                    {menuOptions.map((option) => (
                        <TouchableOpacity
                            key={option.id}
                            style={[
                                styles.menuButton,
                                {
                                    backgroundColor: option.color,
                                    opacity: (option.requiresConnection && serverStatus !== 'connected') ? 0.6 : 1
                                }
                            ]}
                            onPress={() => handleMenuPress(option)}
                            activeOpacity={0.7}
                            disabled={loading}
                        >
                            <Text style={styles.menuTitle}>{option.title}</Text>
                            <Text style={styles.menuSubtitle}>{option.subtitle}</Text>

                            {option.requiresConnection && serverStatus !== 'connected' && (
                                <Text style={styles.offlineIndicator}>⚠️ Requiere conexión</Text>
                            )}
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Quick Stats */}
                {!loading && serverStatus === 'connected' && (
                    <View style={styles.statsContainer}>
                        <Text style={styles.statsTitle}>📊 Resumen</Text>
                        <View style={styles.statsGrid}>
                            <View style={styles.statItem}>
                                <Text style={styles.statValue}>{studentsCount}</Text>
                                <Text style={styles.statLabel}>Estudiantes</Text>
                            </View>
                            <View style={styles.statItem}>
                                <Text style={styles.statValue}>✅</Text>
                                <Text style={styles.statLabel}>Sistema OK</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* Footer */}
                <View style={styles.footer}>
                    <Text style={styles.footerText}>
                        Desarrollado con React Native & FastAPI
                    </Text>
                    <Text style={styles.versionText}>v1.0.0</Text>
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
    content: {
        flexGrow: 1,
        padding: 20,
    },
    header: {
        alignItems: 'center',
        marginBottom: 30,
        marginTop: 20,
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
        marginBottom: 15,
    },
    statusContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#fff',
        paddingHorizontal: 15,
        paddingVertical: 10,
        borderRadius: 20,
        elevation: 2,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
    },
    statusIndicator: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 10,
    },
    statusText: {
        fontSize: 14,
        color: '#333',
        fontWeight: '600',
        flex: 1,
    },
    refreshButton: {
        paddingHorizontal: 10,
        paddingVertical: 5,
    },
    refreshButtonText: {
        fontSize: 16,
    },
    loadingContainer: {
        alignItems: 'center',
        paddingVertical: 20,
    },
    loadingText: {
        marginTop: 10,
        fontSize: 16,
        color: '#666',
    },
    menuContainer: {
        flex: 1,
        justifyContent: 'center',
        gap: 15,
        marginVertical: 20,
    },
    menuButton: {
        padding: 25,
        borderRadius: 15,
        elevation: 5,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        minHeight: 110,
        justifyContent: 'center',
    },
    menuTitle: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 8,
    },
    menuSubtitle: {
        color: '#fff',
        fontSize: 14,
        textAlign: 'center',
        opacity: 0.9,
    },
    offlineIndicator: {
        color: '#fff',
        fontSize: 12,
        textAlign: 'center',
        marginTop: 5,
        opacity: 0.8,
        fontStyle: 'italic',
    },
    statsContainer: {
        backgroundColor: '#fff',
        borderRadius: 15,
        padding: 20,
        marginVertical: 20,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    statsTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        textAlign: 'center',
        marginBottom: 15,
    },
    statsGrid: {
        flexDirection: 'row',
        justifyContent: 'space-around',
    },
    statItem: {
        alignItems: 'center',
    },
    statValue: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#2196F3',
        marginBottom: 5,
    },
    statLabel: {
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
    },
    footer: {
        alignItems: 'center',
        marginTop: 30,
        paddingTop: 20,
        borderTopWidth: 1,
        borderTopColor: '#ddd',
    },
    footerText: {
        fontSize: 12,
        color: '#999',
        textAlign: 'center',
        marginBottom: 5,
    },
    versionText: {
        fontSize: 10,
        color: '#ccc',
        textAlign: 'center',
    },
});

export default MenuScreen;