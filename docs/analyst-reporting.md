# Reportes y reinicio de sesión

`Reset lab` obtiene un límite de registros desde `/api/lab/baseline` y lo guarda
en este navegador para este backend. Las métricas, el historial visible, los logs,
los paneles y los formularios empiezan de nuevo. El límite persiste al recargar.
Los registros y PDF anteriores se conservan; el botón no modifica los Docker ni
cancela una prueba en curso. Los pasos tardíos de campañas anteriores quedan
fuera de la nueva sesión.

Cada resultado, panel y PDF de campaña comparte la clasificación de
`app/analyst.py`. Un estado de ejecución `success` no acredita por sí solo una
vulnerabilidad. Las simulaciones, observaciones, hallazgos con evidencia y
resultados inconclusos se reportan por separado. La decisión es una recomendación
para revisión humana, no una acción enviada al SIEM. Sin evidencia suficiente
o con errores se recomienda escalar; nunca cerrar por falta de conectividad.

## Qué miraría un analista

El campo tiene tres líneas: fuente del log, Event ID o campos reales, y decisión
con una nota breve. Las fuentes sugeridas deben cotejarse con logs originales:
CyberSim no ingiere Windows Security, Windows System, correo ni firewall.

| Prueba existente | Fuente y campos |
| --- | --- |
| Fuerza bruta HTTP / Hydra web | Aplicación web: HTTP 401 o 403 repetidos, usuario, IP, hora |
| Fuerza bruta SSH / Hydra SSH | Linux auth: usuario, IP, hora y mensajes de sshd |
| SQLi, sqlmap, XSS, IDOR, bypass, bug bounty | Aplicación web: código HTTP, ruta, respuesta, usuario, IP, hora |
| Phishing simulado | Correo modelado: remitente, destinatario, mensaje, enlace, hora |
| Escaneo | Firewall a correlacionar: IP, puerto, protocolo, acción, hora |
| Carga acotada | Aplicación web: HTTP, volumen, errores, latencia, hora |
| Malware / RAT simulados | Telemetría de aplicación simulada; Security/System solo como correlación condicional |

HTTP, SSH, SQLi, XSS, IDOR y autorización no reciben un Event ID de Windows.
Un escaneo no se interpreta como inicio de sesión. Las señales de malware o
phishing simuladas no se presentan como eventos de Windows observados.

Las referencias Windows solo se aplican con la fuente y el hecho originales:

| Hecho | Fuente | Referencia |
| --- | --- | --- |
| Fuerza bruta Windows | Windows Security | Varios 4625; 4624 solo si después hubo acceso |
| Programa abierto | Windows Security | 4688 |
| Servicio instalado | Windows System | 7045 |
| Cuenta nueva | Windows Security | 4720 |
| Contraseña reiniciada por otra persona | Windows Security | 4724 |
| Cuenta bloqueada | Windows Security | 4740 |
| Privilegios de administrador | Windows Security | 4672 correlacionado con 4624 de la misma sesión |

En phishing, 4688 solo corresponde si se abrió un programa y 4624 solo si hubo
un acceso posterior con esa cuenta. Si falta confirmación: "sin Event ID confirmado".

Referencias oficiales para la correlación: [4625](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4625),
[4688](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688)
y [4672](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4672).

## Verificación

Desde `backend`: instalar `requirements-dev.txt` y ejecutar
`python -m unittest discover -s tests -v`. Las pruebas usan SQLite en memoria y
resultados de muestra; no lanzan módulos ni peticiones a objetivos.
El dashboard se verifica con `npm run build` desde `dashboard`.

Desplegar primero el backend de Railway y después el dashboard de Vercel.
No se necesitan claves nuevas para estas funciones.
