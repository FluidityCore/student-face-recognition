import React, {useState} from 'react';
import {
    View,
    StyleSheet,
    ScrollView,
} from 'react-native';
import {
    List,
    Switch,
    Divider,
    Button,
    TextInput,
    Card,
    Title,
} from 'react-native-paper';

const SettingsScreen = () => {
    const [apiUrl, setApiUrl] = useState('http://localhost:8000');
    const [autoSave, setAutoSave] = useState(true);
    const [highQuality, setHighQuality] = useState(false);

    return (
        <ScrollView style={styles.container}>
            <Card style={styles.card}>
                <Card.Content>
                    <Title>Configuración de la API</Title>

                    <TextInput
                        label="URL del Servidor"
                        value={apiUrl}
                        onChangeText={setApiUrl}
                        style={styles.input}
                        mode="outlined"
                    />

                    <Button
                        mode="contained"
                        onPress={() => {
                            // Probar conexión
                        }}
                        style={styles.testButton}>
                        Probar Conexión
                    </Button>
                </Card.Content>
            </Card>

            <Card style={styles.card}>
                <Card.Content>
                    <Title>Configuración de Cámara</Title>

                    <List.Item
                        title="Guardar automáticamente"
                        description="Guardar imágenes procesadas"
                        right={() => (
                            <Switch
                                value={autoSave}
                                onValueChange={setAutoSave}
                            />
                        )}
                    />

                    <Divider />

                    <List.Item
                        title="Alta calidad"
                        description="Usar máxima resolución (más lento)"
                        right={() => (
                            <Switch
                                value={highQuality}
                                onValueChange={setHighQuality}
                            />
                        )}
                    />
                </Card.Content>
            </Card>

            <Card style={styles.card}>
                <Card.Content>
                    <Title>Información</Title>

                    <List.Item
                        title="Versión de la App"
                        description="1.0.0"
                        left={(props) => <List.Icon {...props} icon="information" />}
                    />

                    <List.Item
                        title="Acerca de"
                        description="Sistema de reconocimiento facial"
                        left={(props) => <List.Icon {...props} icon="help" />}
                    />
                </Card.Content>
            </Card>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    card: {
        margin: 20,
        elevation: 4,
    },
    input: {
        marginBottom: 15,
    },
    testButton: {
        marginTop: 10,
    },
});

export default SettingsScreen;