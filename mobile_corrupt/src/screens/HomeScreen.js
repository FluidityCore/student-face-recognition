import React from 'react';
import {
    View,
    StyleSheet,
    StatusBar,
} from 'react-native';
import {Button, Title, Paragraph, Card, FAB} from 'react-native-paper';

const HomeScreen = ({navigation}) => {
    return (
        <View style={styles.container}>
            <StatusBar backgroundColor="#1976D2" barStyle="light-content" />

            <Card style={styles.card}>
                <Card.Content>
                    <Title style={styles.title}>Sistema de Reconocimiento Facial</Title>
                    <Paragraph style={styles.subtitle}>
                        Identifica estudiantes usando inteligencia artificial
                    </Paragraph>
                </Card.Content>
            </Card>

            <View style={styles.buttonContainer}>
                <Button
                    mode="contained"
                    onPress={() => navigation.navigate('Camera')}
                    style={styles.primaryButton}
                    icon="camera"
                    contentStyle={styles.buttonContent}>
                    Iniciar Reconocimiento
                </Button>

                <Button
                    mode="outlined"
                    onPress={() => navigation.navigate('Settings')}
                    style={styles.secondaryButton}
                    icon="cog"
                    contentStyle={styles.buttonContent}>
                    Configuración
                </Button>
            </View>

            <FAB
                style={styles.fab}
                icon="information"
                onPress={() => {
                    // Mostrar información de la app
                }}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        padding: 20,
    },
    card: {
        marginTop: 40,
        marginBottom: 40,
        elevation: 4,
    },
    title: {
        textAlign: 'center',
        color: '#1976D2',
        fontSize: 24,
        fontWeight: 'bold',
    },
    subtitle: {
        textAlign: 'center',
        marginTop: 10,
        fontSize: 16,
        color: '#666',
    },
    buttonContainer: {
        flex: 1,
        justifyContent: 'center',
        gap: 20,
    },
    primaryButton: {
        paddingVertical: 8,
    },
    secondaryButton: {
        paddingVertical: 8,
    },
    buttonContent: {
        height: 60,
    },
    fab: {
        position: 'absolute',
        margin: 16,
        right: 0,
        bottom: 0,
        backgroundColor: '#2196F3',
    },
});

export default HomeScreen;