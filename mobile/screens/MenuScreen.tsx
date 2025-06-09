// mobile/screens/MenuScreen.tsx - VERSIÓN FINAL RESPONSIVA Y MODERNA
import React from 'react';
import {
    View,
    StyleSheet,
    Alert,
    ScrollView,
    Animated,
} from 'react-native';
import {
    Surface,
    Title,
    Button,
    Text,
    Card,
    IconButton,
    Portal,
    Dialog,
    List,
} from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';
import { responsive, baseStyles, wp, hp, fp } from '../utils/responsive';

const API_BASE = 'https://student-face-recognition-production.up.railway.app';

const apiService = {
    healthCheck: async () => {
        const response = await fetch(`${API_BASE}/health`);
        return response.json();
    },
    getStats: async () => {
        const response = await fetch(`${API_BASE}/api/recognition/stats`);
        return response.json();
    }
};

export default function MenuScreen() {
    const navigation = useNavigation();
    const { theme, isDark, themeMode, setThemeMode } = useTheme();
    const [showThemeDialog, setShowThemeDialog] = React.useState(false);
    const [fadeAnim] = React.useState(new Animated.Value(0));

    // Animación de entrada
    React.useEffect(() => {
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
        }).start();
    }, []);

    // Verificar conexión con API
    const { data: health, isLoading: healthLoading } = useQuery({
        queryKey: ['health'],
        queryFn: apiService.healthCheck,
        retry: 2,
    });

    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: apiService.getStats,
        retry: 1,
    });

    const menuOptions = [
        {
            title: 'Reconocer Estudiante',
            subtitle: 'Tomar foto y identificar estudiante',
            icon: 'camera',
            emoji: '🔍',
            onPress: () => navigation.navigate('Recognize' as never),
            gradient: isDark ? ['#4A90E2', '#357ABD'] : ['#667eea', '#764ba2'],
        },
        {
            title: 'Agregar Estudiante',
            subtitle: 'Registrar nuevo estudiante con foto',
            icon: 'account-plus',
            emoji: '➕',
            onPress: () => navigation.navigate('AddStudent' as never),
            gradient: isDark ? ['#E25A6A', '#C44569'] : ['#f093fb', '#f5576c'],
        },
        {
            title: 'Lista de Estudiantes',
            subtitle: 'Ver, editar y eliminar estudiantes',
            icon: 'account-group',
            emoji: '👥',
            onPress: () => navigation.navigate('StudentsList' as never),
            gradient: isDark ? ['#4FACFE', '#00D4FF'] : ['#4facfe', '#00f2fe'],
        },
        {
            title: 'Probar Conexión',
            subtitle: 'Verificar conexión con el servidor',
            icon: 'wifi',
            emoji: '⚙️',
            onPress: testConnection,
            gradient: isDark ? ['#A8E6CF', '#88D8A3'] : ['#a8edea', '#fed6e3'],
        },
    ];

    async function testConnection() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            const data = await response.json();

            Alert.alert(
                'Test de Conexión',
                response.ok
                    ? `✅ Conectado correctamente\nServidor: ${data.server || 'Railway'}\nEstado: ${data.status}`
                    : '❌ Error de conexión',
                [{ text: 'OK' }]
            );
        } catch (error) {
            Alert.alert('Error', '❌ No se pudo conectar al servidor');
        }
    }

    const getStatusColor = () => {
        if (healthLoading) return theme.colors.warning;
        return health?.status === 'healthy' ? theme.colors.success : theme.colors.error;
    };

    const getStatusText = () => {
        if (healthLoading) return 'Conectando...';
        return health?.status === 'healthy' ? 'Servidor conectado' : 'Sin conexión';
    };

    const renderHeader = () => (
        <Animated.View style={[{ opacity: fadeAnim }]}>
            <LinearGradient
                colors={isDark ? ['#1a1a2e', '#16213e', '#0f3460'] : ['#667eea', '#764ba2', '#667eea']}
                style={styles.header}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
            >
                <View style={styles.headerContent}>
                    <View style={styles.headerTop}>
                        <View style={styles.titleContainer}>
                            <Text style={styles.headerEmoji}>🎓</Text>
                            <Title style={styles.title}>Sistema de Reconocimiento</Title>
                        </View>

                        <IconButton
                            icon={isDark ? 'white-balance-sunny' : 'moon-waning-crescent'}
                            size={responsive.iconSize.lg}
                            iconColor="#FFFFFF"
                            style={styles.themeButton}
                            onPress={() => setShowThemeDialog(true)}
                        />
                    </View>

                    {/* Estado de conexión mejorado */}
                    <Card style={[styles.statusCard, { backgroundColor: theme.colors.surface }]}>
                        <Card.Content style={styles.statusContent}>
                            <View style={styles.statusRow}>
                                <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
                                <Text style={[styles.statusText, { color: theme.colors.text }]}>
                                    {getStatusText()}
                                </Text>
                            </View>

                            {stats && !statsLoading && (
                                <Text style={[styles.statsText, { color: theme.colors.textSecondary }]}>
                                    📊 {stats.total_students || 0} estudiantes registrados
                                </Text>
                            )}
                        </Card.Content>
                    </Card>
                </View>
            </LinearGradient>
        </Animated.View>
    );

    const renderQuickStats = () => {
        if (!stats || statsLoading) return null;

        return (
            <Animated.View style={[{ opacity: fadeAnim, transform: [{ translateY: fadeAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [20, 0]
                    }) }] }]}>
                <Card style={[styles.quickStatsCard, { backgroundColor: theme.colors.surface }]}>
                    <Card.Content>
                        <Text style={[styles.quickStatsTitle, { color: theme.colors.text }]}>
                            📈 Estadísticas Rápidas
                        </Text>

                        <View style={styles.quickStats}>
                            <View style={styles.quickStatItem}>
                                <Text style={[styles.quickStatNumber, { color: theme.colors.success }]}>
                                    {stats.successful_recognitions || 0}
                                </Text>
                                <Text style={[styles.quickStatLabel, { color: theme.colors.textSecondary }]}>
                                    Reconocimientos Exitosos
                                </Text>
                            </View>

                            <View style={[styles.statDivider, { backgroundColor: theme.colors.border }]} />

                            <View style={styles.quickStatItem}>
                                <Text style={[styles.quickStatNumber, { color: theme.colors.info }]}>
                                    {stats.success_rate || 0}%
                                </Text>
                                <Text style={[styles.quickStatLabel, { color: theme.colors.textSecondary }]}>
                                    Tasa de Éxito
                                </Text>
                            </View>

                            <View style={[styles.statDivider, { backgroundColor: theme.colors.border }]} />

                            <View style={styles.quickStatItem}>
                                <Text style={[styles.quickStatNumber, { color: theme.colors.warning }]}>
                                    {stats.total_students || 0}
                                </Text>
                                <Text style={[styles.quickStatLabel, { color: theme.colors.textSecondary }]}>
                                    Total Estudiantes
                                </Text>
                            </View>
                        </View>
                    </Card.Content>
                </Card>
            </Animated.View>
        );
    };

    const renderMenuGrid = () => (
        <View style={styles.menuContainer}>
            {menuOptions.map((option, index) => (
                <Animated.View
                    key={index}
                    style={[{
                        opacity: fadeAnim,
                        transform: [{
                            translateY: fadeAnim.interpolate({
                                inputRange: [0, 1],
                                outputRange: [30 * (index + 1), 0]
                            })
                        }]
                    }]}
                >
                    <Card style={[styles.menuCard, { backgroundColor: theme.colors.surface }]}>
                        <LinearGradient
                            colors={option.gradient as [string, string]}
                            style={styles.menuGradient}
                            start={{ x: 0, y: 0 }}
                            end={{ x: 1, y: 1 }}
                        >
                            <Button
                                mode="text"
                                onPress={option.onPress}
                                style={styles.menuButton}
                                contentStyle={styles.menuButtonContent}
                                labelStyle={styles.menuButtonLabel}
                            >
                                <View style={styles.menuButtonInner}>
                                    <View style={styles.menuIconContainer}>
                                        <Text style={styles.menuEmoji}>{option.emoji}</Text>
                                    </View>

                                    <View style={styles.menuTextContainer}>
                                        <Text style={styles.menuTitle}>{option.title}</Text>
                                        <Text style={styles.menuSubtitle}>{option.subtitle}</Text>
                                    </View>

                                    <IconButton
                                        icon="chevron-right"
                                        size={responsive.iconSize.md}
                                        iconColor="#FFFFFF"
                                        style={styles.menuArrow}
                                    />
                                </View>
                            </Button>
                        </LinearGradient>
                    </Card>
                </Animated.View>
            ))}
        </View>
    );

    const renderFooter = () => (
        <Animated.View style={[{ opacity: fadeAnim }]}>
            <Card style={[styles.footerCard, { backgroundColor: theme.colors.surface }]}>
                <Card.Content>
                    <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
                        🌐 API: {API_BASE.replace('https://', '')}
                    </Text>
                    <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
                        📱 Modo: {themeMode === 'auto' ? 'Automático' : themeMode === 'dark' ? 'Oscuro' : 'Claro'}
                    </Text>
                    <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
                        📱 Pantalla: {responsive.screen.width}x{responsive.screen.height}
                        {responsive.screen.isSmall ? ' (Pequeña)' : responsive.screen.isLarge ? ' (Grande)' : ' (Mediana)'}
                    </Text>
                </Card.Content>
            </Card>
        </Animated.View>
    );

    return (
        <Surface style={[styles.container, { backgroundColor: theme.colors.background }]}>
            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                {renderHeader()}
                {renderQuickStats()}
                {renderMenuGrid()}
                {renderFooter()}
            </ScrollView>

            {/* Dialog para cambiar tema */}
            <Portal>
                <Dialog
                    visible={showThemeDialog}
                    onDismiss={() => setShowThemeDialog(false)}
                    style={{ backgroundColor: theme.colors.surface }}
                >
                    <Dialog.Title style={{ color: theme.colors.text }}>
                        🌓 Seleccionar Tema
                    </Dialog.Title>
                    <Dialog.Content>
                        <List.Item
                            title="☀️ Modo Claro"
                            onPress={() => {
                                setThemeMode('light');
                                setShowThemeDialog(false);
                            }}
                            left={() => (
                                <List.Icon
                                    icon={themeMode === 'light' ? 'radiobox-marked' : 'radiobox-blank'}
                                    color={theme.colors.primary}
                                />
                            )}
                            titleStyle={{ color: theme.colors.text }}
                        />
                        <List.Item
                            title="🌙 Modo Oscuro"
                            onPress={() => {
                                setThemeMode('dark');
                                setShowThemeDialog(false);
                            }}
                            left={() => (
                                <List.Icon
                                    icon={themeMode === 'dark' ? 'radiobox-marked' : 'radiobox-blank'}
                                    color={theme.colors.primary}
                                />
                            )}
                            titleStyle={{ color: theme.colors.text }}
                        />
                        <List.Item
                            title="🔄 Automático"
                            onPress={() => {
                                setThemeMode('auto');
                                setShowThemeDialog(false);
                            }}
                            left={() => (
                                <List.Icon
                                    icon={themeMode === 'auto' ? 'radiobox-marked' : 'radiobox-blank'}
                                    color={theme.colors.primary}
                                />
                            )}
                            titleStyle={{ color: theme.colors.text }}
                        />
                    </Dialog.Content>
                </Dialog>
            </Portal>
        </Surface>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        flexGrow: 1,
    },
    header: {
        paddingTop: hp(8), // Responsivo para status bar
        paddingBottom: responsive.spacing.xl,
        paddingHorizontal: responsive.layout.paddingHorizontal,
    },
    headerContent: {
        alignItems: 'center',
    },
    headerTop: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
        marginBottom: responsive.spacing.lg,
    },
    titleContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
    },
    headerEmoji: {
        fontSize: responsive.screen.isSmall ? fp(28) : fp(32),
        marginRight: responsive.spacing.md,
    },
    title: {
        fontSize: responsive.screen.isSmall ? responsive.fontSize.xl : responsive.fontSize.xxl,
        fontWeight: 'bold',
        color: '#FFFFFF',
        flex: 1,
        flexWrap: 'wrap',
    },
    themeButton: {
        backgroundColor: 'rgba(255,255,255,0.2)',
        borderRadius: responsive.borderRadius.lg,
    },
    statusCard: {
        width: '100%',
        borderRadius: responsive.borderRadius.xl,
        ...baseStyles.shadow.medium,
    },
    statusContent: {
        paddingVertical: responsive.spacing.md,
    },
    statusRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: responsive.spacing.sm,
    },
    statusDot: {
        width: responsive.screen.isSmall ? wp(3) : wp(3.5),
        height: responsive.screen.isSmall ? wp(3) : wp(3.5),
        borderRadius: wp(2),
        marginRight: responsive.spacing.md,
    },
    statusText: {
        fontSize: responsive.fontSize.md,
        fontWeight: '600',
    },
    statsText: {
        fontSize: responsive.fontSize.sm,
        marginLeft: responsive.spacing.xl,
    },
    quickStatsCard: {
        margin: responsive.layout.paddingHorizontal,
        borderRadius: responsive.borderRadius.xl,
        ...baseStyles.shadow.medium,
    },
    quickStatsTitle: {
        fontSize: responsive.fontSize.lg,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.lg,
        textAlign: 'center',
    },
    quickStats: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    quickStatItem: {
        flex: 1,
        alignItems: 'center',
    },
    quickStatNumber: {
        fontSize: responsive.screen.isSmall ? responsive.fontSize.xxl : responsive.fontSize.title,
        fontWeight: 'bold',
        marginBottom: responsive.spacing.xs,
    },
    quickStatLabel: {
        fontSize: responsive.fontSize.xs,
        textAlign: 'center',
        lineHeight: responsive.fontSize.xs * 1.3,
    },
    statDivider: {
        width: 1,
        height: hp(5),
        marginHorizontal: responsive.spacing.md,
    },
    menuContainer: {
        paddingHorizontal: responsive.layout.paddingHorizontal,
        gap: responsive.spacing.lg,
        paddingVertical: responsive.spacing.lg,
    },
    menuCard: {
        borderRadius: responsive.borderRadius.xxl,
        ...baseStyles.shadow.large,
        overflow: 'hidden',
    },
    menuGradient: {
        borderRadius: responsive.borderRadius.xxl,
    },
    menuButton: {
        margin: 0,
        borderRadius: responsive.borderRadius.xxl,
    },
    menuButtonContent: {
        height: responsive.screen.isSmall ? hp(11) : hp(12),
        paddingHorizontal: 0,
    },
    menuButtonLabel: {
        margin: 0,
    },
    menuButtonInner: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: responsive.spacing.lg,
        width: '100%',
    },
    menuIconContainer: {
        marginRight: responsive.spacing.lg,
    },
    menuEmoji: {
        fontSize: responsive.screen.isSmall ? fp(28) : fp(32),
    },
    menuTextContainer: {
        flex: 1,
    },
    menuTitle: {
        fontSize: responsive.screen.isSmall ? responsive.fontSize.lg : responsive.fontSize.xl,
        fontWeight: 'bold',
        color: '#FFFFFF',
        marginBottom: responsive.spacing.xs,
    },
    menuSubtitle: {
        fontSize: responsive.fontSize.sm,
        color: 'rgba(255,255,255,0.9)',
        lineHeight: responsive.fontSize.sm * 1.3,
    },
    menuArrow: {
        margin: 0,
    },
    footerCard: {
        margin: responsive.layout.paddingHorizontal,
        marginTop: 0,
        borderRadius: responsive.borderRadius.xl,
        ...baseStyles.shadow.small,
    },
    footerText: {
        fontSize: responsive.fontSize.xs,
        textAlign: 'center',
        marginBottom: responsive.spacing.xs,
        lineHeight: responsive.fontSize.xs * 1.4,
    },
});