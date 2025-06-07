import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import HomeScreen from '../screens/HomeScreen';
import CameraScreen from '../screens/CameraScreen';
import ResultScreen from '../screens/ResultScreen';
import SettingsScreen from '../screens/SettingsScreen';

const Stack = createStackNavigator();

const AppNavigator = () => {
    return (
        <Stack.Navigator
            initialRouteName="Home"
            screenOptions={{
                headerStyle: {
                    backgroundColor: '#2196F3',
                },
                headerTintColor: '#fff',
                headerTitleStyle: {
                    fontWeight: 'bold',
                },
            }}>
            <Stack.Screen
                name="Home"
                component={HomeScreen}
                options={{title: 'Reconocimiento Facial'}}
            />
            <Stack.Screen
                name="Camera"
                component={CameraScreen}
                options={{title: 'Cámara'}}
            />
            <Stack.Screen
                name="Result"
                component={ResultScreen}
                options={{title: 'Resultado'}}
            />
            <Stack.Screen
                name="Settings"
                component={SettingsScreen}
                options={{title: 'Configuración'}}
            />
        </Stack.Navigator>
    );
};

export default AppNavigator;