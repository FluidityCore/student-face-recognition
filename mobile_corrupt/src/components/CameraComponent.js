import React from 'react';
import {View, StyleSheet} from 'react-native';
import {Button} from 'react-native-paper';

const CameraComponent = ({onCapture}) => {
    return (
        <View style={styles.container}>
            <Button
                mode="contained"
                onPress={onCapture}
                icon="camera"
                style={styles.button}>
                Tomar Foto
            </Button>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    button: {
        paddingVertical: 10,
    },
});

export default CameraComponent;