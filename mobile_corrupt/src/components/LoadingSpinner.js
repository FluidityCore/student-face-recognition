import React from 'react';
import {View, StyleSheet} from 'react-native';
import {ActivityIndicator, Text} from 'react-native-paper';

const LoadingSpinner = ({message = 'Cargando...'}) => {
    return (
        <View style={styles.container}>
            <ActivityIndicator size="large" color="#2196F3" />
            <Text style={styles.message}>{message}</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    message: {
        marginTop: 16,
        fontSize: 16,
        color: '#666',
    },
});

export default LoadingSpinner;