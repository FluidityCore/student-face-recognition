import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    SafeAreaView,
    ScrollView,
    TouchableOpacity,
    Switch,
    Alert,
    TextInput,
    ActivityIndicator,
} from 'react-native';
import ApiService from '../services/ApiService';

const SettingsScreen = ({ navigation }) => {
    const [settings, setSettings] = useState({
        recognitionThreshold: 0.5,
        autoSave: true,
        showDebugInfo: false,
        cacheImages: true,
        soundEnabled: true,
        vibrationEnabled: true,
    });

    const [serverStatus, setServerStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        checkServerHealth();
        loadStats();
    }, []);

    const checkServerHealth = async () => {
        try {
            const health = await ApiService.checkHealth();
            setServerStatus('connected');
            console.log('Server health:', health);
        } catch (error) {
            setServerStatus('disconnected');
            console.error('Server health check failed:', error);
        }
    };

    const loadStats = async () => {
        try {
            const statsData = await ApiService.getRecognitionStats();
            setStats(statsData);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    };

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSaveSettings = () => {
        // Aquí podrías guardar las configuraciones en AsyncStorage
        Alert.alert('Configuración', 'Configuraciones guardadas correctamente');
    };

    const handleClearCache = () => {
        Alert.alert(
            'Limpiar Caché',
            '¿Estás seguro de que deseas limpiar el caché de imágenes?',
            [
                { text: 'Cancelar', style: 'cancel' },
                {
                    text: 'Limpiar',
                    onPress: () => {
                        Alert.alert('Caché', 'Caché limpiado correctamente');
                    }
                }
            ]
        );
    };

    const handleTestConnection = async () => {
        setLoading(true);
        try {
            await checkServerHealth();
            Alert.alert(
                'Conexión',
                serverStatus === 'connected'
                    ? '✅ Conexión exitosa con el servidor'
                    : '❌ No se pudo conectar al servidor'
            );
        } catch (error) {
            Alert.alert('Error', 'No se pudo probar la conexión');
        } finally {
            setLoading(false);
        }
    };

    const handleViewLogs = () => {
        navigation.navigate('LogsScreen');
    };

    const renderSettingItem = (title, description, value, onValueChange, type = 'switch') => (
        <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
                <Text style={styles.settingTitle}>{title}</Text>
                <Text style={styles.settingDescription}>{description}</Text>
            </View>
            {type === 'switch' ? (
                <Switch
                    value={value}
                    onValueChange={onValueChange}
                    trackColor={{ false: '#767577', true: '#2196F3' }}
                    thumbColor={value ? '#fff' : '#f4f3f4'}
                />
            ) : (
                <TextInput
                    style={styles.settingInput}
                    value={value.toString()}
                    onChangeText={(text) => onValueChange(parseFloat(text) || 0)}
                    keyboardType="numeric"
                />
            )}
        </View>
    );

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>

                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.title}>⚙️ Configuración</Text>
                    <Text style={styles.subtitle}>Ajustes de la aplicación</Text>
                </View>

                {/* Estado del Servidor */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>🌐 Estado del Servidor</Text>
                    <View style={styles.serverStatus}>
                        <View style={styles.statusInfo}>
                            <View style={[
                                styles.statusIndicator,
                                { backgroundColor: serverStatus === 'connected' ? '#4CAF50' : '#f44336' }
                            ]} />
                            <Text style={styles.statusText}>
                                {serverStatus === 'connected' ? 'Conectado' : 'Desconectado'}
                            </Text>
                        </View>
                        <TouchableOpacity
                            style={styles.testButton}
                            onPress={handleTestConnection}
                            disabled={loading}
                        >
                            {loading ? (
                                <ActivityIndicator color="#fff" size="small" />
                            ) : (
                                <Text style={styles.testButtonText}>Probar</Text>
                            )}
                        </TouchableOpacity>
                    </View>
                </View>

                {/* Estadísticas */}
                {stats && (
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}>📊 Estadísticas</Text>
                        <View style={styles.statsContainer}>
                            <View style={styles.statItem}>
                                <Text style={styles.statValue}>{stats.total_recognitions || 0}</Text>
                                <Text style={styles.statLabel}>Reconocimientos</Text>
                            </View>
                            <View style={styles.statItem}>
                                <Text style={styles.statValue}>{stats.successful_recognitions || 0}</Text>
                                <Text style={styles.statLabel}>Exitosos</Text>
                            </View>
                            <View style={styles.statItem}>
                                <Text style={styles.statValue}>
                                    {stats.success_rate ? (stats.success_rate * 100).toFixed(1) : 0}%
                                </Text>
                                <Text style={styles.statLabel}>Precisión</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* Configuración de Reconocimiento */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>🎯 Reconocimiento Facial</Text>

                    {renderSettingItem(
                        'Umbral de Similitud',
                        'Nivel de similitud requerido (0.1 - 1.0)',
                        settings.recognitionThreshold,
                        (value) => handleSettingChange('recognitionThreshold', Math.min(1.0, Math.max(0.1, value))),
                        'input'
                    )}

                    {renderSettingItem(
                        'Mostrar Información de Debug',
                        'Mostrar detalles técnicos en reconocimiento',
                        settings.showDebugInfo,
                        (value) => handleSettingChange('showDebugInfo', value)
                    )}
                </View>

                {/* Configuración General */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>🔧 General</Text>

                    {renderSettingItem(
                        'Guardado Automático',
                        'Guardar automáticamente los cambios',
                        settings.autoSave,
                        (value) => handleSettingChange('autoSave', value)
                    )}

                    {renderSettingItem(
                        'Caché de Imágenes',
                        'Guardar imágenes en caché local',
                        settings.cacheImages,
                        (value) => handleSettingChange('cacheImages', value)
                    )}

                    {renderSettingItem(
                        'Sonidos',
                        'Reproducir sonidos de notificación',
                        settings.soundEnabled,
                        (value) => handleSettingChange('soundEnabled', value)
                    )}

                    {renderSettingItem(
                        'Vibración',
                        'Vibrar en notificaciones',
                        settings.vibrationEnabled,
                        (value) => handleSettingChange('vibrationEnabled', value)
                    )}
                </View>

                {/* Acciones */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>🛠️ Acciones</Text>

                    <TouchableOpacity style={styles.actionButton} onPress={handleSaveSettings}>
                        <Text style={styles.actionButtonText}>💾 Guardar Configuración</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.actionButton} onPress={handleClearCache}>
                        <Text style={styles.actionButtonText}>🗑️ Limpiar Caché</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.actionButton} onPress={handleViewLogs}>
                        <Text style={styles.actionButtonText}>📋 Ver Logs</Text>
                    </TouchableOpacity>
                </View>

                {/* Información de la App */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>ℹ️ Información</Text>
                    <View style={styles.infoContainer}>
                        <Text style={styles.infoText}>Versión: 1.0.0</Text>
                        <Text style={styles.infoText}>Build: 001</Text>
                        <Text style={styles.infoText}>React Native: 0.79.3</Text>
                        <Text style={styles.infoText}>API: FastAPI + face_recognition</Text>
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
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
        marginTop: 5,
    },
    section: {
        backgroundColor: '#fff',
        marginVertical: 10,
        marginHorizontal: 15,
        borderRadius: 10,
        padding: 20,
        elevation: 2,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
        marginBottom: 15,
    },
    settingItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0',
    },
    settingInfo: {
        flex: 1,
        marginRight: 15,
    },
    settingTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        marginBottom: 2,
    },
    settingDescription: {
        fontSize: 14,
        color: '#666',
    },
    settingInput: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        paddingHorizontal: 12,
        paddingVertical: 8,
        fontSize: 16,
        backgroundColor: '#f9f9f9',
        width: 80,
        textAlign: 'center',
    },
    serverStatus: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 15,
        backgroundColor: '#f8f9fa',
        borderRadius: 10,
    },
    statusInfo: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    statusIndicator: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 10,
    },
    statusText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    testButton: {
        backgroundColor: '#2196F3',
        paddingHorizontal: 20,
        paddingVertical: 8,
        borderRadius: 8,
        minWidth: 80,
        alignItems: 'center',
    },
    testButtonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold',
    },
    statsContainer: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        paddingVertical: 15,
    },
    statItem: {
        alignItems: 'center',
    },
    statValue: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#2196F3',
        marginBottom: 5,
    },
    statLabel: {
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
    },
    actionButton: {
        backgroundColor: '#f8f9fa',
        paddingVertical: 15,
        paddingHorizontal: 20,
        borderRadius: 10,
        marginVertical: 5,
        borderWidth: 1,
        borderColor: '#e0e0e0',
    },
    actionButtonText: {
        fontSize: 16,
        color: '#333',
        textAlign: 'center',
        fontWeight: '600',
    },
    infoContainer: {
        backgroundColor: '#f8f9fa',
        padding: 15,
        borderRadius: 10,
    },
    infoText: {
        fontSize: 14,
        color: '#666',
        marginBottom: 8,
        textAlign: 'center',
    },
});

export default SettingsScreen;