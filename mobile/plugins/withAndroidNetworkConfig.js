const { withAndroidManifest } = require('@expo/config-plugins');
const fs = require('fs');
const path = require('path');

function withAndroidNetworkConfig(config) {
    return withAndroidManifest(config, async config => {
        const androidManifest = config.modResults;

        // Agregar usesCleartextTraffic y networkSecurityConfig al application
        const application = androidManifest.manifest.application[0];
        if (application) {
            application.$['android:usesCleartextTraffic'] = 'true';
            application.$['android:networkSecurityConfig'] = '@xml/network_security_config';
        }

        // Crear el archivo network_security_config.xml
        const projectRoot = config.modRequest.projectRoot;
        const androidResDir = path.join(projectRoot, 'android', 'app', 'src', 'main', 'res', 'xml');

        // Crear directorio si no existe
        if (!fs.existsSync(androidResDir)) {
            fs.mkdirSync(androidResDir, { recursive: true });
        }

        // Crear archivo de configuración de red
        const networkConfigContent = `<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">student-face-recognition-production.up.railway.app</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">192.168.1.1</domain>
    </domain-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>`;

        const configPath = path.join(androidResDir, 'network_security_config.xml');
        fs.writeFileSync(configPath, networkConfigContent);

        return config;
    });
}

module.exports = withAndroidNetworkConfig;