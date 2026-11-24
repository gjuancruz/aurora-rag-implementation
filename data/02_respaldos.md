# Manual ficticio de Aurora: respaldos

## Alcance

Este manual educativo define el respaldo de la configuración y de los archivos
procesados por Aurora. Un respaldo contiene una copia cifrada de esos elementos
y un manifiesto de integridad. El manifiesto lista los identificadores y las sumas
de comprobación de los objetos incluidos. La copia no contiene contraseñas en texto
plano. La custodia de las claves corresponde al equipo de Plataforma.

## Frecuencia y retención

Aurora realiza un respaldo completo todos los días a las 01:00, hora de Buenos Aires.
Los respaldos se conservan durante 30 días.
La tarea automática registra el inicio, el fin y el resultado de la copia. Si el
respaldo falla, el operador revisa el código de error, comprueba el espacio disponible
y vuelve a ejecutar la tarea cuando resuelve la causa. Una ejecución fallida no
reemplaza la última copia válida. El tablero de operación muestra por separado la
fecha del último intento y la fecha del último respaldo válido.

## Verificación

Después de cada copia se comparan las sumas de comprobación con el manifiesto.
Una diferencia invalida la copia y genera un incidente. El operador no marca como
válido un respaldo que no pasó la verificación. Todas las semanas se restaura una
copia en un entorno aislado, utilizando archivos de prueba. El resultado se registra
en el tablero de respaldos con la fecha y el responsable de la comprobación.

## Restauración

Para restaurar, el operador selecciona el último respaldo válido anterior al incidente,
comprueba su manifiesto y solicita al responsable de Plataforma la apertura de la
ventana de recuperación. Durante la restauración se mantiene pausada la recepción
de archivos. Al terminar, se revisan la integridad y la prueba de salud. El registro
final identifica la copia utilizada y el resultado de la prueba. Si la prueba falla,
la recepción sigue pausada y el caso se mantiene abierto para investigación.

## Acceso a las copias

Solo el equipo de Plataforma puede iniciar una restauración. Soporte puede consultar
el estado de las tareas, pero no descargar las copias. Las descargas autorizadas
quedan registradas con fecha, identidad y motivo. Los respaldos vencidos se eliminan
mediante la tarea de retención después de verificar que exista otra copia válida.
