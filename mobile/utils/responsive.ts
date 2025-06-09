// mobile/utils/responsive.ts
import { Dimensions, PixelRatio } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Dimensiones base para el diseño (iPhone 11 Pro)
const BASE_WIDTH = 375;
const BASE_HEIGHT = 812;

// Función para escalar horizontalmente
export const wp = (percentage: number): number => {
    const value = (percentage * SCREEN_WIDTH) / 100;
    return Math.round(PixelRatio.roundToNearestPixel(value));
};

// Función para escalar verticalmente
export const hp = (percentage: number): number => {
    const value = (percentage * SCREEN_HEIGHT) / 100;
    return Math.round(PixelRatio.roundToNearestPixel(value));
};

// Función para escalar fuentes
export const fp = (size: number): number => {
    const scale = SCREEN_WIDTH / BASE_WIDTH;
    const newSize = size * scale;
    return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

// Dimensiones responsivas para diferentes elementos
export const responsive = {
    // Tamaños de pantalla
    screen: {
        width: SCREEN_WIDTH,
        height: SCREEN_HEIGHT,
        isSmall: SCREEN_WIDTH < 350,
        isMedium: SCREEN_WIDTH >= 350 && SCREEN_WIDTH < 414,
        isLarge: SCREEN_WIDTH >= 414,
        isTablet: SCREEN_WIDTH >= 768,
    },

    // Espaciado responsivo
    spacing: {
        xs: wp(1),      // 4px en pantalla base
        sm: wp(2),      // 8px
        md: wp(4),      // 16px
        lg: wp(6),      // 24px
        xl: wp(8),      // 32px
        xxl: wp(12),    // 48px
    },

    // Tamaños de fuente responsivos
    fontSize: {
        xs: fp(10),
        sm: fp(12),
        md: fp(14),
        lg: fp(16),
        xl: fp(18),
        xxl: fp(20),
        xxxl: fp(24),
        title: fp(28),
        header: fp(32),
    },

    // Radios de borde responsivos
    borderRadius: {
        xs: wp(1),      // 4px
        sm: wp(2),      // 8px
        md: wp(3),      // 12px
        lg: wp(4),      // 16px
        xl: wp(5),      // 20px
        xxl: wp(6),     // 24px
        round: wp(50),  // Completamente redondo
    },

    // Tamaños de iconos responsivos
    iconSize: {
        xs: fp(16),
        sm: fp(20),
        md: fp(24),
        lg: fp(28),
        xl: fp(32),
        xxl: fp(40),
    },

    // Alturas de elementos responsivos
    heights: {
        button: hp(6),      // ~48px
        input: hp(7),       // ~56px
        card: hp(12),       // ~96px
        image: wp(40),      // 40% del ancho
        header: hp(12),     // ~96px
    },

    // Márgenes y padding por pantalla
    layout: {
        paddingHorizontal: SCREEN_WIDTH < 350 ? wp(3) : wp(4), // 12px o 16px
        paddingVertical: hp(2), // ~16px
        cardMargin: wp(4), // 16px
        sectionGap: hp(3), // ~24px
    },
};

// Hook para obtener dimensiones actualizadas
export const useResponsive = () => {
    const [dimensions, setDimensions] = React.useState(Dimensions.get('window'));

    React.useEffect(() => {
        const subscription = Dimensions.addEventListener('change', ({ window }) => {
            setDimensions(window);
        });

        return () => subscription?.remove();
    }, []);

    return {
        ...responsive,
        screen: {
            ...responsive.screen,
            width: dimensions.width,
            height: dimensions.height,
        },
    };
};

// Estilos base responsivos reutilizables
export const baseStyles = {
    container: {
        flex: 1,
        paddingHorizontal: responsive.layout.paddingHorizontal,
        paddingVertical: responsive.layout.paddingVertical,
    },

    card: {
        borderRadius: responsive.borderRadius.lg,
        marginBottom: responsive.spacing.md,
        padding: responsive.spacing.md,
        elevation: 3,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },

    button: {
        borderRadius: responsive.borderRadius.xl,
        height: responsive.heights.button,
        justifyContent: 'center' as const,
        alignItems: 'center' as const,
    },

    input: {
        borderRadius: responsive.borderRadius.md,
        height: responsive.heights.input,
        marginBottom: responsive.spacing.md,
    },

    text: {
        title: {
            fontSize: responsive.fontSize.title,
            fontWeight: 'bold' as const,
            textAlign: 'center' as const,
            marginBottom: responsive.spacing.lg,
        },

        subtitle: {
            fontSize: responsive.fontSize.xl,
            fontWeight: '600' as const,
            marginBottom: responsive.spacing.md,
        },

        body: {
            fontSize: responsive.fontSize.md,
            lineHeight: responsive.fontSize.md * 1.4,
        },

        caption: {
            fontSize: responsive.fontSize.sm,
            lineHeight: responsive.fontSize.sm * 1.3,
        },
    },

    shadow: {
        small: {
            elevation: 2,
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.1,
            shadowRadius: 2,
        },

        medium: {
            elevation: 4,
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.15,
            shadowRadius: 4,
        },

        large: {
            elevation: 8,
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.2,
            shadowRadius: 8,
        },
    },
};

import React from 'react';