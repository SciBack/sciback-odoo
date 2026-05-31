### Informe Técnico Operativo: Protocolos de Control, Configuración y Matrícula en el Sistema SIAGIE

#### 1\. Introducción y Marco Operativo del Sistema

El Sistema de Información de Apoyo a la Gestión de la Institución Educativa (SIAGIE) constituye la plataforma central del Ministerio de Educación (MINEDU) para la administración de la trayectoria educativa a nivel nacional. La observancia estricta de sus instructivos oficiales no es opcional, sino una necesidad estratégica para salvaguardar la integridad y seguridad de la información académica y administrativa, garantizando que los documentos oficiales emitidos posean plena validez legal.La arquitectura operativa del SIAGIE se fundamenta en un esquema de controles y validaciones sistémicas secuenciales. Este diseño previene la generación de inconsistencias mediante bloqueos lógicos que aseguran que el registro de datos se realice bajo condiciones de coherencia administrativa. En este sentido, la gestión eficiente del sistema inicia con la configuración precisa de los ciclos académicos, donde el cierre técnico de una etapa es la condición habilitante para el inicio de la siguiente.

#### 2\. Gestión del Ciclo Académico: Año Escolar, Fases y Periodos

La secuencialidad de las fases en el SIAGIE es un factor crítico; cualquier alteración en el orden de cierre y apertura compromete la estabilidad del historial del estudiante y la emisión de documentos oficiales.

##### Cierre del Año Escolar

Para proceder con el cierre definitivo, el usuario debe seguir la ruta:  **Administración IE \> Configuración Año Escolar \> Año escolar** . El sistema realiza una validación exhaustiva de los estados previos:

* **Requisito Obligatorio:**  Todas las fases de evaluación registradas deben estar en estado  **CERRADA** .  
* **Mensaje de Bloqueo:**  En caso de existir fases abiertas, el sistema emitirá el siguiente mensaje literal:  *“Para poder cerrar el Año academico debe tener cerrada las fases correspondientes del año seleccionado.”*

##### Apertura y Cierre de Fases de Evaluación

La gestión de fases opera bajo una jerarquía de dependencia técnica:

* **Fase Regular:**  La activación de esta fase requiere obligatoriamente que el año académico anterior precedente esté en estado  **CERRADO** . Para su clausura, el sistema valida que las Actas de Evaluación Final estén generadas y aprobadas en su totalidad.  
* **Fase de Recuperación:**  Se rige por un  **bloqueo sistémico** : solo puede activarse si la Fase Regular está estrictamente  **CERRADA** . El sistema validará esta condición con el mensaje:  *“Para Activar fase de recuperación la fase regular debe estar cerrada.”*  Su cierre definitivo exige que se hayan generado y aprobado las actas de recuperación en todos los grados con secciones de dicha naturaleza.

##### Control y Reapertura de Periodos

La herramienta "Reapertura de periodos de evaluación" permite modificar calificaciones bimestrales o trimestrales, pero su acceso está condicionado al estado de la fase:

* **Fase Activa:**  Permite la edición y gestión de periodos.  
* **Fase Inactiva o Cerrada:**  Los campos permanecen bloqueados. Si se intenta abrir un periodo en una fase cerrada, el sistema notificará:  *“La Fase Regular se encuentra CERRADA deberá activarla para Abrir el periodo”* .

#### 3\. Integridad y Modificación de Datos del Estudiante

La veracidad de los datos personales es el pilar de la interoperabilidad con RENIEC y la UGEL. La modificación de la fecha de nacimiento, al ser un dato biográfico sensible, está sujeta a restricciones sistémicas según el estado de la matrícula.

##### Análisis de Escenarios de Modificación

Escenario,Estado del Estudiante,Mensaje del Sistema / Restricción,Acción Requerida  
A,Matrícula registrada sin Nómina.,"""El estudiante ya cuenta con matrícula en el año 2023, deberá eliminar la Matrícula del estudiante para poder modificar la Fecha de Nacimiento.""",Eliminar matrícula previa.  
B,Nómina de Matrícula Generada.,"""La matrícula del estudiante ya se encuentra en una Nómina de Matrícula Generada, deberá eliminar la Nómina y luego eliminar la matrícula del estudiante para poder modificar la Fecha de Nacimiento.""",Eliminar nómina y luego matrícula.  
C,Nómina de Matrícula Aprobada.,"“La matrícula del estudiante ya se encuentra en Nómina de Matrícula Aprobada por la UGEL, deberá registrar y remitir la Solicitud de Rectificación de Nómina de Matrícula y esperar su aprobación para poder modificar la Fecha de Nacimiento.”",Gestionar Solicitud de Rectificación ante UGEL.  
Una vez que la UGEL otorga la aprobación sistémica, el usuario debe procesar la rectificación. Al concluir la operación con éxito, el sistema emitirá la confirmación:  *“No olvide generar y remitir la Rectificación de Nómina de Matrícula”* .

#### 4\. Validación de Extraedad en el Nivel Inicial (R.M. Nro. 028-2013-ED)

La matrícula en Inicial está normada por la  **Resolución Ministerial Nro. 028-2013-ED** , que establece el 31 de marzo como fecha de corte para el cálculo de la edad cronológica.

##### Reglas de Negocio y Síntesis Experta

La normativa permite autorizar el ingreso o la permanencia (definida como el acto de repetir el grado a los 5 años por solicitud del apoderado) bajo los siguientes criterios:

* **Diferencia de 1 año:**  Se permite la matrícula previa acreditación (ej. Informe Psicológico).  
* **Diferencia de 2 años o más:**  El sistema aplica una  **prohibición absoluta** . Ejemplo: Un niño de 7 años cumplidos al 31/03 no puede matricularse en el grado de 5 años.  
* **El Umbral Crítico (Caso 6 años):**  
* Si el niño cumple 6 años el  **31/03** , se considera que tiene extraedad para 5 años y requiere autorización/acreditación.  
* Si el niño cumple 6 años el  **01/04** , el sistema lo procesa sin requerir acreditación adicional, permitiendo su matrícula regular en el grado de 5 años.

##### Configuración Operativa

En la ruta  **Configuración general \> Grados** , el administrador debe establecer los límites de "Edad Desde" y "Edad Hasta" para cada grado de Inicial. Cuando el sistema detecta la diferencia de un año permitida, exige completar obligatoriamente el  **Tipo de documento**  y  **Número de documento**  de acreditación para validar el registro.

#### 5\. Metodologías de Matrícula y Cambio de Estados

El SIAGIE ofrece diversas modalidades de carga de datos, todas integradas con las validaciones de extraedad y continuidad académica.

##### Modalidades Operativas

1. **Matrícula Individual:**  Gestión manual caso por caso, necesaria cuando se deben ingresar documentos de acreditación por extraedad.  
2. **Matrícula Masiva (Excel):**  Procesamiento por lotes mediante plantillas. Si existen inconsistencias de extraedad, el sistema marcará el registro y generará un  **"Reporte de observaciones de extra-edad"** , obligando a que dichos casos se resuelvan vía Matrícula Individual.  
3. **Matrícula Automática (Pre-matrícula):**  Generación masiva basada en el diseño curricular y la situación académica del año anterior.  
4. **Gestión de Traslado – Ingreso:**  Este proceso también activa la validación de edad, exigiendo el "Tipo y número de documento de acreditación" si el estudiante se encuentra en el rango de un año de extraedad.

##### Procedimiento para la Anulación de Matrícula

Desde la ruta  **Estudiantes \> Estudiantes por Sección** , el administrador puede gestionar la vigencia de los registros. Al cambiar el estado a  **ANULADO** , el sistema emitirá un mensaje de confirmación crítico con la siguiente literalidad:*“¿Está seguro de cambiar el estado de la matrícula a ANULADO. Luego de ello la matrícula no será válida para los procesos SIAGIE?”*

#### 6\. Fuentes y Referencias Documentales

* *Instructivo de controles en año escolar, fases y periodos \- Proyecto SIAGIE (MINEDU).*  
* *Instructivo de control de modificación de la fecha de nacimiento del estudiante (MINEDU).*  
* *Instructivo de validación de la extraedad para Inicial \- R.M. Nro. 028-2013-ED (MINEDU).*  
* *Manual de usuario de SIAGIE: Apertura, configuración y matrícula \- UGEL Chincheros (2025).*  
* *Recursos Audiovisuales: Canal Oficial MINEDU SIAGIE v5.*

