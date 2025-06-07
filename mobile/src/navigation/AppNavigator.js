import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Screens
import MenuScreen from '../screens/MenuScreen';
import RecognitionScreen from '../screens/RecognitionScreen';
import StudentsListScreen from '../screens/StudentsListScreen';
import CreateStudentScreen from '../screens/CreateStudentScreen';
import EditStudentScreen from '../screens/EditStudentScreen';

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
                    },
                    headerTitleAlign: 'center',
                }}>

                <Stack.Screen
                    name="Menu"
                    component={MenuScreen}
                    options={{ title: '🎓 Sistema Facial' }}
                />

                <Stack.Screen
                    name="Recognition"
                    component={RecognitionScreen}
                    options={{ title: '📷 Reconocimiento' }}
                />

                <Stack.Screen
                    name="StudentsList"
                    component={StudentsListScreen}
                    options={{ title: '👥 Estudiantes' }}
                />

                <Stack.Screen
                    name="CreateStudent"
                    component={CreateStudentScreen}
                    options={{ title: '➕ Nuevo Estudiante' }}
                />

                <Stack.Screen
                    name="EditStudent"
                    component={EditStudentScreen}
                    options={{ title: '✏️ Editar Estudiante' }}
                />

            </Stack.Navigator>
        </NavigationContainer>
    );
};

export default AppNavigator;