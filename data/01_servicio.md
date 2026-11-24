# Manual ficticio de Aurora: operación del servicio

Este documento pertenece a un dataset educativo inventado. Aurora es un servicio
interno de procesamiento de archivos. No describe una empresa ni un producto real.
Los procedimientos de este corpus son la única fuente autorizada para el ejercicio.

## Horario y responsables

La ventana de mantenimiento de Aurora es los martes de 02:00 a 03:00, hora de Buenos Aires.
El equipo de Plataforma coordina los cambios durante esa ventana. Antes de un cambio,
el operador registra el identificador de la tarea en el tablero de mantenimiento y
confirma que no haya cargas activas. Si hay una carga activa, espera a que termine
antes de suspender la recepción de archivos. No interrumpe trabajos en ejecución.

## Reinicio controlado

Para reiniciar Aurora, primero se pausa la recepción de archivos, luego se espera
a que la cola quede vacía y finalmente se reinicia el proceso del servicio.
Después del reinicio, se comprueba el indicador de salud y se envía un archivo de
prueba sin datos personales. El operador comprueba que el archivo termine en estado
procesado y que el registro de eventos contenga su identificador. Solo entonces
vuelve a habilitar la recepción. Si falla la prueba, mantiene la recepción pausada
y sigue el procedimiento de incidentes, dejando registrado el paso que falló.

## Estados y seguimiento

Los estados de un archivo son recibido, en cola, procesando, procesado y rechazado.
Un archivo rechazado conserva un código de motivo. El equipo de soporte utiliza ese
código y el identificador de carga para investigar el problema. No solicita el
contenido completo del archivo por correo. Los registros operativos muestran la
fecha, el estado y el identificador, pero no incluyen el contenido del documento.
Cada cambio de estado se registra una sola vez y puede consultarse por identificador.

## Cierre del mantenimiento

Al terminar la ventana, el operador anota la hora de finalización, los identificadores
de los cambios aplicados y el resultado de la prueba de salud. Si un cambio quedó
pendiente, lo deja registrado para la siguiente ventana. El responsable de Plataforma
revisa el registro antes de cerrar la tarea. Un mantenimiento que no pasó la prueba
de salud no se declara completo. Los avisos a usuarios se publican en el tablero
interno y describen el estado del servicio sin incluir información privada.
