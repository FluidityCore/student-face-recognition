import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Screens
import MenuScreen from '../screens/MenuScreen';
import RecognitionScreen from '../screens/RecognitionScreen';
import StudentsListScreen from '../screens/StudentsListScreen';
import CreateStudentScreen from '../screens/CreateStudentScreen';
import EditStudentScreen from '../screens/EditStudentScreen';
import SettingsScreen from '../screens/SettingsScreen';

const Stack = createStackNavigator();

const AppNavigator = () => {
    return (
        <NavigationContainer>
            <Stack.Navigator
                initialRouteName="Menu"
                screenOptions={{
                    headerStyle: {
                        backgroundColor: '#2196F3',
                    },
                    headerTintColor: '#fff',
                    headerTitleStyle: {
                        fontWeight: 'bold',
                        fontSize: 18,
                    },
                    headerTitleAlign: 'center',
                    headerBackTitleVisible: false,
                }}>

                <Stack.Screen
                    name="Menu"
                    component={MenuScreen}
                    options={{
                        title: '🎓 Sistema Facial',
                        headerLeft: null, // Deshabilitar botón de volver en menú principal
                    }}
                />

                <Stack.Screen
                    name="Recognition"
                    component={RecognitionScreen}
                    options={{
                        title: '📷 Reconocimiento',
                        headerBackTitle: 'Menú',
                    }}
                />

                <Stack.Screen
                    name="StudentsList"
                    component={StudentsListScreen}
                    options={{
                        title: '👥 Estudiantes',
                        headerBackTitle: 'Menú',
                    }}
                />

                <Stack.Screen
                    name="CreateStudent"
                    component={CreateStudentScreen}
                    options={{
                        title: '➕ Nuevo Estudiante',
                        headerBackTitle: 'Atrás',
                    }}
                />

                <Stack.Screen
                    name="EditStudent"
                    component={EditStudentScreen}
                    options={{
                        title: '✏️ Editar Estudiante',
                        headerBackTitle: 'Lista',
                    }}
                />

                <Stack.Screen
                    name="Settings"
                    component={SettingsScreen}
                    options={{
                        title: '⚙️ Configuración',
                        headerBackTitle: 'Menú',
                    }}
                />

            </Stack.Navigator>
        </NavigationContainer>
    );
};

export default AppNavigator;