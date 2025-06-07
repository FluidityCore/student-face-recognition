import React from 'react';
import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
    SafeAreaView,
    ScrollView,
} from 'react-native';

const MenuScreen = ({ navigation }) => {
    const menuOptions = [
        {
            id: 1,
            title: '📷 Reconocimiento Facial',
            subtitle: 'Identificar estudiante por foto',
            screen: 'Recognition',
            color: '#2196F3',
        },
        {
            id: 2,
            title: '👥 Ver Estudiantes',
            subtitle: 'Lista de todos los estudiantes',
            screen: 'StudentsList',
            color: '#4CAF50',
        },
        {
            id: 3,
            title: '➕ Nuevo Estudiante',
            subtitle: 'Registrar nuevo estudiante',
            screen: 'CreateStudent',
            color: '#FF9800',
        },
    ];

    const handleMenuPress = (screen) => {
        navigation.navigate(screen);
    };

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content}>
                <View style={styles.header}>
                    <Text style={styles.title}>🎓 Sistema de Reconocimiento Facial</Text>
                    <Text style={styles.subtitle}>Gestión de Estudiantes</Text>
                </View>

                <View style={styles.menuContainer}>
                    {menuOptions.map((option) => (
                        <TouchableOpacity
                            key={option.id}
                            style={[styles.menuButton, { backgroundColor: option.color }]}
                            onPress={() => handleMenuPress(option.screen)}
                            activeOpacity={0.7}
                        >
                            <Text style={styles.menuTitle}>{option.title}</Text>
                            <Text style={styles.menuSubtitle}>{option.subtitle}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                <View style={styles.footer}>
                    <Text style={styles.footerText}>
                        Desarrollado con React Native & FastAPI
                    </Text>
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
        marginBottom: 40,
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
    },
    menuContainer: {
        flex: 1,
        justifyContent: 'center',
        gap: 20,
    },
    menuButton: {
        padding: 25,
        borderRadius: 15,
        elevation: 5,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        minHeight: 100,
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
    },
});

export default MenuScreen;