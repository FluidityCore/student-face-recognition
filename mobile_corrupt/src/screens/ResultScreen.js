import React from 'react';
import {
    View,
    StyleSheet,
    Image,
    ScrollView,
} from 'react-native';
import {
    Card,
    Title,
    Paragraph,
    Button,
    Chip,
    Divider,
} from 'react-native-paper';

const ResultScreen = ({navigation, route}) => {
    const {result, imageUri} = route.params;

    const getConfidenceColor = (confidence) => {
        switch (confidence) {
            case 'Alta':
                return '#4CAF50';
            case 'Media':
                return '#FF9800';
            default:
                return '#F44336';
        }
    };

    return (
        <ScrollView style={styles.container}>
            <Card style={styles.imageCard}>
                <Image source={{uri: imageUri}} style={styles.image} />
            </Card>

            <Card style={styles.resultCard}>
                <Card.Content>
                    {result.found ? (
                        <>
                            <View style={styles.statusContainer}>
                                <Chip
                                    mode="flat"
                                    style={[
                                        styles.statusChip,
                                        {backgroundColor: '#E8F5E8'},
                                    ]}
                                    textStyle={{color: '#2E7D32'}}>
                                    ✓ Estudiante Encontrado
                                </Chip>
                            </View>

                            <Title style={styles.studentName}>
                                {result.student.nombre} {result.student.apellidos}
                            </Title>

                            {result.student.correo && (
                                <Paragraph style={styles.detail}>
                                    📧 {result.student.correo}
                                </Paragraph>
                            )}

                            <Paragraph style={styles.detail}>
                                🆔 ID: {result.student.id}
                            </Paragraph>

                            {result.student.requisitoriado && (
                                <Chip
                                    mode="flat"
                                    style={styles.alertChip}
                                    textStyle={{color: '#C62828'}}>
                                    ⚠️ REQUISITORIADO
                                </Chip>
                            )}

                            <Divider style={styles.divider} />

                            <View style={styles.metricsContainer}>
                                <Paragraph style={styles.metricTitle}>
                                    Métricas de Reconocimiento:
                                </Paragraph>

                                <View style={styles.metricRow}>
                                    <Paragraph>Similitud:</Paragraph>
                                    <Paragraph style={styles.metricValue}>
                                        {(result.similarity * 100).toFixed(1)}%
                                    </Paragraph>
                                </View>

                                <View style={styles.metricRow}>
                                    <Paragraph>Confianza:</Paragraph>
                                    <Chip
                                        mode="flat"
                                        style={[
                                            styles.confidenceChip,
                                            {backgroundColor: getConfidenceColor(result.confidence)},
                                        ]}
                                        textStyle={{color: 'white'}}>
                                        {result.confidence}
                                    </Chip>
                                </View>
                            </View>
                        </>
                    ) : (
                        <>
                            <View style={styles.statusContainer}>
                                <Chip
                                    mode="flat"
                                    style={[
                                        styles.statusChip,
                                        {backgroundColor: '#FFEBEE'},
                                    ]}
                                    textStyle={{color: '#C62828'}}>
                                    ✗ Estudiante No Encontrado
                                </Chip>
                            </View>

                            <Title style={styles.noResultTitle}>
                                No se encontró coincidencia
                            </Title>

                            <Paragraph style={styles.noResultText}>
                                El rostro no corresponde a ningún estudiante registrado en el sistema.
                            </Paragraph>

                            {result.best_similarity && (
                                <Paragraph style={styles.detail}>
                                    Mejor similitud: {(result.best_similarity * 100).toFixed(1)}%
                                </Paragraph>
                            )}
                        </>
                    )}
                </Card.Content>
            </Card>

            <View style={styles.buttonContainer}>
                <Button
                    mode="contained"
                    onPress={() => navigation.navigate('Camera')}
                    style={styles.button}
                    icon="camera">
                    Reconocer Otro
                </Button>

                <Button
                    mode="outlined"
                    onPress={() => navigation.navigate('Home')}
                    style={styles.button}
                    icon="home">
                    Inicio
                </Button>
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    imageCard: {
        margin: 20,
        elevation: 4,
    },
    image: {
        width: '100%',
        height: 200,
        borderRadius: 8,
    },
    resultCard: {
        margin: 20,
        elevation: 4,
    },
    statusContainer: {
        alignItems: 'center',
        marginBottom: 20,
    },
    statusChip: {
        paddingHorizontal: 10,
    },
    studentName: {
        textAlign: 'center',
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1976D2',
        marginBottom: 10,
    },
    detail: {
        fontSize: 16,
        marginBottom: 8,
        textAlign: 'center',
    },
    alertChip: {
        alignSelf: 'center',
        marginTop: 10,
        backgroundColor: '#FFEBEE',
    },
    divider: {
        marginVertical: 20,
    },
    metricsContainer: {
        backgroundColor: '#f9f9f9',
        padding: 15,
        borderRadius: 8,
    },
    metricTitle: {
        fontWeight: 'bold',
        marginBottom: 10,
    },
    metricRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    metricValue: {
        fontWeight: 'bold',
        color: '#1976D2',
    },
    confidenceChip: {
        paddingHorizontal: 5,
    },
    noResultTitle: {
        textAlign: 'center',
        color: '#C62828',
        marginBottom: 10,
    },
    noResultText: {
        textAlign: 'center',
        marginBottom: 20,
    },
    buttonContainer: {
        padding: 20,
        gap: 15,
    },
    button: {
        paddingVertical: 8,
    },
});

export default ResultScreen;