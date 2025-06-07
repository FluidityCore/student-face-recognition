import React from 'react';
import {StyleSheet} from 'react-native';
import {Card, Title, Paragraph, Chip} from 'react-native-paper';

const StudentCard = ({student}) => {
    return (
        <Card style={styles.card}>
            <Card.Content>
                <Title style={styles.name}>
                    {student.nombre} {student.apellidos}
                </Title>

                {student.correo && (
                    <Paragraph style={styles.email}>
                        📧 {student.correo}
                    </Paragraph>
                )}

                <Paragraph style={styles.id}>
                    🆔 ID: {student.id}
                </Paragraph>

                {student.requisitoriado && (
                    <Chip
                        mode="flat"
                        style={styles.alertChip}
                        textStyle={{color: '#C62828'}}>
                        ⚠️ REQUISITORIADO
                    </Chip>
                )}
            </Card.Content>
        </Card>
    );
};

const styles = StyleSheet.create({
    card: {
        margin: 16,
        elevation: 4,
    },
    name: {
        color: '#1976D2',
        textAlign: 'center',
    },
    email: {
        textAlign: 'center',
        marginTop: 8,
    },
    id: {
        textAlign: 'center',
        marginTop: 4,
    },
    alertChip: {
        alignSelf: 'center',
        marginTop: 12,
        backgroundColor: '#FFEBEE',
    },
});

export default StudentCard;