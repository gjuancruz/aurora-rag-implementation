# Manual ficticio de Aurora: incidentes

## Clasificación

Un incidente P1 corresponde a una interrupción total del procesamiento de archivos.
Un incidente P2 corresponde a degradación parcial con procesamiento todavía disponible.
Un incidente P3 corresponde a una consulta o falla sin impacto en la disponibilidad.
El operador registra evidencia observable y el alcance del impacto antes de asignar
la prioridad. Una demora aislada no implica por sí sola una interrupción total.

## Primera respuesta

Para incidentes P1, el objetivo de primera respuesta es de 15 minutos.
El equipo de guardia reconoce el caso en el tablero y asigna una persona responsable.
El objetivo de primera respuesta no es un compromiso de resolución. La persona a
cargo registra el estado de la cola y el indicador de salud. Luego comprueba si hay
un cambio reciente relacionado con el inicio de la falla. Cada acción se anota con
su hora para mantener una secuencia verificable de la investigación.

## Comunicación y recuperación

Durante una interrupción, el responsable publica una actualización cada 30 minutos.
Las actualizaciones describen el impacto conocido y las acciones realizadas. Si la
causa todavía no fue confirmada, se indica que sigue en investigación. No se publican
hipótesis como hechos ni se promete una hora de recuperación sin evidencia. Cuando
el servicio vuelve a estar saludable, se verifica una carga de prueba y se observa
que la cola avance antes de comunicar la recuperación.

## Cierre y revisión

Para cerrar un incidente se necesitan una prueba de salud exitosa, una carga de
prueba procesada y una descripción de las acciones realizadas. La revisión posterior
identifica la causa confirmada, los factores contribuyentes y las acciones pendientes.
Cada acción pendiente tiene un responsable y una fecha de seguimiento. Si la causa
no fue determinada, la revisión lo declara explícitamente y conserva la investigación
como tarea separada. El cierre operativo no elimina los registros de diagnóstico.

## Protección de información

Los registros compartidos en el tablero deben excluir contenido privado de archivos,
contraseñas y claves. Se utilizan identificadores de carga para enlazar evidencias.
Si se detecta información privada en un registro, se restringe el acceso al registro
y se informa al responsable de Plataforma. Las capturas de pantalla siguen las
mismas reglas de protección que los registros de texto.
