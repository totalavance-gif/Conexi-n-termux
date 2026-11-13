# Muse Control - servidor

Servidor local que recibe órdenes de la app Android y arranca
【entity-Muse¦canonical_name=Muse】 en este mismo equipo. Solo acepta
conexiones de localhost y comandos de una lista blanca fija.

## Iniciar

```sh
cd server
python3 server.py
```

Escucha en `http://127.0.0.1:8080` (solo este equipo, nunca internet).

## Token secreto

Antes de arrancar, define tu token (el mismo que escribas en la app):

```sh
export MUSE_TOKEN="tu-token-largo-y-aleatorio"
python3 server.py
```

Sin `MUSE_TOKEN` usa el valor de ejemplo `MI_TOKEN_SECRETO_123`
y muestra un aviso. No compartas tu token.

## Lista blanca

Los únicos comandos aceptados (cualquier otro se rechaza sin ejecutar):

- `muse`
- `muse --yolo`
- `proot-distro login ubuntu`
- `proot-distro login ubuntu -c muse --yolo`

## Archivos

- `commands.log`: un renglón JSON por cada comando recibido
  (fecha, cliente, comando, si se permitió, PID). Nunca guarda el token.
- `runs/run-*.log`: salida de cada comando ejecutado.

## Notas

- El servidor inicia el proceso en segundo plano; para interactuar
  con 【entity-Muse¦canonical_name=Muse】 abre tu terminal de Termux/Ubuntu como siempre.
- `GET /health` responde `{"status": "ok"}` si el servidor está vivo.
- Detener: `Ctrl+C` en la terminal donde corre.
