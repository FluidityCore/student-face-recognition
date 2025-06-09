// mobile/context/ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useColorScheme } from 'react-native';

export interface AppTheme {
    dark: boolean;
    colors: {
        primary: string;
        background: string;
        surface: string;
        text: string;
        textSecondary: string;
        border: string;
        card: string;
        success: string;
        warning: string;
        error: string;
        info: string;
    };
}

const lightTheme: AppTheme = {
    dark: false,
    colors: {
        primary: '#2196F3',
        background: '#F8F9FA',
        surface: '#FFFFFF',
        text: '#212121',
        textSecondary: '#666666',
        border: '#E0E0E0',
        card: '#FFFFFF',
        success: '#4CAF50',
        warning: '#FF9800',
        error: '#F44336',
        info: '#2196F3',
    },
};

const darkTheme: AppTheme = {
    dark: true,
    colors: {
        primary: '#64B5F6',
        background: '#121212',
        surface: '#1E1E1E',
        text: '#FFFFFF',
        textSecondary: '#B0B0B0',
        border: '#333333',
        card: '#2C2C2C',
        success: '#66BB6A',
        warning: '#FFB74D',
        error: '#EF5350',
        info: '#64B5F6',
    },
};

interface ThemeContextType {
    theme: AppTheme;
    isDark: boolean;
    toggleTheme: () => void;
    setThemeMode: (mode: 'light' | 'dark' | 'auto') => void;
    themeMode: 'light' | 'dark' | 'auto';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const systemColorScheme = useColorScheme();
    const [themeMode, setThemeMode] = useState<'light' | 'dark' | 'auto'>('auto');

    const isDark = themeMode === 'auto'
        ? systemColorScheme === 'dark'
        : themeMode === 'dark';

    const theme = isDark ? darkTheme : lightTheme;

    const toggleTheme = () => {
        setThemeMode(current => current === 'dark' ? 'light' : 'dark');
    };

    return (
        <ThemeContext.Provider value={{
            theme,
            isDark,
            toggleTheme,
            setThemeMode,
            themeMode,
        }}>
            {children}
        </ThemeContext.Provider>
    );
};
