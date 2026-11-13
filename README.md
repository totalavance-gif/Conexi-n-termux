# Muse Control

Control remoto local para 【entity-Muse¦canonical_name=Muse】: una app Android manda
órdenes a un servidor Python que corre en el mismo celular
(Termux / Ubuntu con proot-distro) y arranca 【entity-Muse¦canonical_name=Muse】.

Nada sale a internet: el servidor solo escucha en `127.0.0.1:8080`,
cada orden necesita el token secreto y solo acepta comandos de una
lista blanca fija.

## Estructura

```
├── server/
│   ├── server.py          # Servidor localhost:8080 (solo stdlib)
│   ├── requirements.txt   # Sin dependencias
│   └── README.md          # Cómo iniciar el servidor
├── app/                   # App Android (Kotlin + Jetpack Compose)
├── .github/workflows/     # CI: compila la APK en cada push a main
└── README.md
```

## Servidor

```sh
cd server
export MUSE_TOKEN="tu-token-largo-y-aleatorio"
python3 server.py
```

Detalle en [server/README.md](server/README.md).

## App Android

La app **Muse Control** tiene el campo de token y dos botones:
**Entrar a Muse** y **Entrar con YOLO**. Muestra OK o ERROR
según responda el servidor.

El token por defecto viaja en `BuildConfig`, no en el código:
se pasa al compilar y nunca se commitea en texto plano:

```sh
./gradlew assembleDebug -PMUSE_TOKEN="tu-token"
```

Sin `-PMUSE_TOKEN`, el campo arranca vacío y escribes el token a mano.

## Descargar la APK

Cada push a `main` la compila en Actions: pestaña **Actions** →
último run verde → artifact **muse-control-apk**
(contiene debug + release). Instala la **debug** (la release sale
sin firmar salvo que configures keystore por secretos).
Si un build falla, el workflow abre un issue con el extracto del log.

## Compilar en local

Necesitas JDK 17 + Android SDK (no funciona en Termux/proot):

```sh
./gradlew assembleDebug
```

La APK queda en `app/build/outputs/apk/debug/`.

## Seguridad

- Servidor atado a `127.0.0.1`: inalcanzable desde internet o tu red.
- Token obligatorio (comparación en tiempo constante); el token
  nunca se guarda en `commands.log`.
- Lista blanca exacta de 4 comandos; todo lo demás se rechaza.
- La app solo permite tráfico sin cifrar hacia `127.0.0.1`.
- **No compartas tu token.**
