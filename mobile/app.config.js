const withAndroidNetworkConfig = require('./plugins/withAndroidNetworkConfig');

export default ({ config }) => {
    const isProduction = process.env.NODE_ENV === 'production';

    return withAndroidNetworkConfig({
        ...config,
        name: "Student Face Recognition",
        slug: "student-face-recognition-mobile",
        version: "1.0.0",
        orientation: "portrait",
        userInterfaceStyle: "automatic",

        // Configuración de íconos y splash
        icon: "./assets/icon.png",
        splash: {
            image: "./assets/splash.png",
            resizeMode: "contain",
            backgroundColor: "#2196F3"
        },

        // Variables de entorno para la app
        extra: {
            apiUrl: isProduction
                ? "https://student-face-recognition-production.up.railway.app"
                : "https://student-face-recognition-production.up.railway.app",
            environment: isProduction ? "production" : "development",
            eas: {
                projectId: "7d3ba5fc-d73a-4cfa-ab2c-586d3332e795"
            }
        },

        ios: {
            supportsTablet: true,
            bundleIdentifier: "com.deadmailsdoc.studentfacerecognitionmobile",
            infoPlist: {
                NSCameraUsageDescription: "Esta aplicación necesita acceso a la cámara para reconocimiento facial de estudiantes",
                NSPhotoLibraryUsageDescription: "Esta aplicación necesita acceso a la galería para seleccionar fotos de estudiantes",
                NSAppTransportSecurity: {
                    NSAllowsArbitraryLoads: true,
                    NSExceptionDomains: {
                        "student-face-recognition-production.up.railway.app": {
                            NSExceptionAllowsInsecureHTTPLoads: true,
                            NSExceptionMinimumTLSVersion: "TLSv1.0",
                            NSIncludesSubdomains: true
                        }
                    }
                }
            }
        },

        android: {
            package: "com.deadmailsdoc.studentfacerecognitionmobile",
            permissions: [
                "android.permission.CAMERA",
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE",
                "android.permission.RECORD_AUDIO",
                "android.permission.INTERNET",
                "android.permission.ACCESS_NETWORK_STATE",
                "android.permission.ACCESS_WIFI_STATE"
            ],
            usesCleartextTraffic: true,
            networkSecurityConfig: "network_security_config",
            adaptiveIcon: {
                foregroundImage: "./assets/adaptive-icon.png",
                backgroundColor: "#2196F3"
            }
        },

        plugins: [
            [
                "expo-camera",
                {
                    cameraPermission: "Permitir $(PRODUCT_NAME) acceder a tu cámara para reconocimiento facial."
                }
            ],
            [
                "expo-image-picker",
                {
                    photosPermission: "La aplicación accede a tus fotos para seleccionar imágenes de estudiantes."
                }
            ]
        ]
    });
};