// mobile/App.tsx - VERSIÓN MEJORADA CON TEMAS
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Provider as PaperProvider, MD3LightTheme, MD3DarkTheme } from 'react-native-paper';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Screens
import MenuScreen from './screens/MenuScreen';
import RecognizeScreen from './screens/RecognizeScreen';
import AddStudentScreen from './screens/AddStudentScreen';
import StudentsListScreen from './screens/StudentsListScreen';
import EditStudentScreen from './screens/EditStudentScreen';

// Theme Provider
import { ThemeProvider, useTheme } from './context/ThemeContext';

const queryClient = new QueryClient();
const Stack = createNativeStackNavigator();

// Componente interno que usa el tema
function AppContent() {
    const { theme, isDark } = useTheme();

    // Tema personalizado para React Native Paper
    const paperTheme = {
        ...(isDark ? MD3DarkTheme : MD3LightTheme),
        colors: {
            ...(isDark ? MD3DarkTheme.colors : MD3LightTheme.colors),
            primary: theme.colors.primary,
            background: theme.colors.background,
            surface: theme.colors.surface,
            onSurface: theme.colors.text,
            outline: theme.colors.border,
        },
    };

    // Tema para React Navigation
    const navigationTheme = {
        ...(isDark ? DarkTheme : DefaultTheme),
        colors: {
            ...(isDark ? DarkTheme.colors : DefaultTheme.colors),
            primary: theme.colors.primary,
            background: theme.colors.background,
            card: theme.colors.surface,
            text: theme.colors.text,
            border: theme.colors.border,
        },
    };

    return (
        <PaperProvider theme={paperTheme}>
            <NavigationContainer theme={navigationTheme}>
                <StatusBar style={isDark ? "light" : "dark"} />
                <Stack.Navigator
                    initialRouteName="Menu"
                    screenOptions={{
                        headerStyle: {
                            backgroundColor: theme.colors.surface,
                        },
                        headerTintColor: theme.colors.text,
                        headerTitleStyle: {
                            fontWeight: 'bold',
                            color: theme.colors.text,
                        },
                        headerShadowVisible: !isDark,
                    }}
                >
                    <Stack.Screen
                        name="Menu"
                        component={MenuScreen}
                        options={{
                            title: 'Reconocimiento Facial',
                            headerShown: false, // Ocultamos header en menu principal
                        }}
                    />
                    <Stack.Screen
                        name="Recognize"
                        component={RecognizeScreen}
                        options={{ title: 'Reconocer Estudiante' }}
                    />
                    <Stack.Screen
                        name="AddStudent"
                        component={AddStudentScreen}
                        options={{ title: 'Agregar Estudiante' }}
                    />
                    <Stack.Screen
                        name="StudentsList"
                        component={StudentsListScreen}
                        options={{ title: 'Lista de Estudiantes' }}
                    />
                    <Stack.Screen
                        name="EditStudent"
                        component={EditStudentScreen}
                        options={{ title: 'Editar Estudiante' }}
                    />
                </Stack.Navigator>
            </NavigationContainer>
        </PaperProvider>
    );
}

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider>
                <AppContent />
            </ThemeProvider>
        </QueryClientProvider>
    );
}