# Especificación de Requerimientos - AccessFlow

## 1. Resumen de la entrevista con el cliente

Se realizó una entrevista con la empresa para entender el proceso actual de gestión de accesos a herramientas internas. Durante la sesión se identificaron los siguientes hallazgos principales:

- El proceso actual es informal: los empleados solicitan acceso por Slack, correo o mensajes directos a IT.
- No existe trazabilidad clara sobre quién pidió acceso, quién lo aprobó y por cuánto tiempo debería mantenerse.
- La empresa está creciendo y se aproximan auditorías internas de seguridad.
- Existen accesos antiguos que nunca fueron revocados y no se sabe si siguen siendo necesarios.
- Los accesos no son todos iguales: hay niveles (READ, WRITE, ADMIN) que implican distintos niveles de riesgo.
- Ciertos sistemas, como bases de datos productivas, requieren controles adicionales sin importar el nivel de acceso.
- La expiración de accesos es una preocupación importante, especialmente para accesos administrativos.

---

## 2. Usuarios y roles

| Rol | Descripción | Responsabilidades |
|-----|-------------|-------------------|
| **Employee** | Empleado que solicita acceso a una herramienta | Crear solicitudes de acceso, consultar el estado de sus solicitudes, recibir notificaciones |
| **Manager** | Responsable de aprobar accesos de su equipo | Revisar, aprobar o rechazar solicitudes de su equipo, solicitar cambios |
| **Security Reviewer** | Encargado de revisar accesos sensibles o críticos | Revisar y aprobar/rechazar accesos ADMIN y a bases de datos productivas |
| **IT Admin** | Persona que otorga o simula la provisión del acceso | Completar el provisioning de accesos aprobados, marcar solicitudes como completadas |
| **System Admin** | Usuario con visibilidad total del sistema | Gestionar usuarios, ver todas las solicitudes, configurar parámetros del sistema |

---

## 3. Requerimientos funcionales

### Solicitudes de acceso

| ID | Requerimiento |
|----|---------------|
| **RF-01** | El sistema debe permitir que un usuario autenticado cree una solicitud de acceso especificando: sistema destino, nivel de acceso (READ/WRITE/ADMIN), justificación y fecha de expiración. |
| **RF-02** | El sistema debe exigir fecha de expiración obligatoria para solicitudes de nivel ADMIN. |
| **RF-03** | El sistema debe permitir fecha de expiración opcional para solicitudes de nivel READ y WRITE. |
| **RF-04** | El sistema debe validar que el solicitante no pueda aprobar su propia solicitud. |

### Flujo de aprobación

| ID | Requerimiento |
|----|---------------|
| **RF-05** | El sistema debe enviar la solicitud al Manager del empleado cuando es creada. |
| **RF-06** | El sistema debe requerir aprobación de Security Reviewer para accesos de nivel ADMIN. |
| **RF-07** | El sistema debe requerir aprobación de Security Reviewer para cualquier acceso a bases de datos productivas, sin importar el nivel. |
| **RF-08** | El sistema debe permitir que un aprobador apruebe una solicitud, cambiando su estado al siguiente paso del flujo. |
| **RF-09** | El sistema debe permitir que un aprobador rechace una solicitud, finalizando el flujo. |
| **RF-10** | El sistema debe impedir que una solicitud rechazada sea reabierta o aprobada posteriormente. |
| **RF-11** | El sistema debe permitir que un aprobador solicite cambios, devolviendo la solicitud a estado DRAFT. |

### Provisioning

| ID | Requerimiento |
|----|---------------|
| **RF-12** | El sistema debe permitir que solo IT Admin marque una solicitud aprobada como completada. |
| **RF-13** | El sistema debe cambiar el estado a READY_FOR_PROVISIONING antes de permitir la finalización. |

### Notificaciones

| ID | Requerimiento |
|----|---------------|
| **RF-14** | El sistema debe notificar al Manager cuando se crea una solicitud de su equipo. |
| **RF-15** | El sistema debe notificar al Security Reviewer cuando una solicitud requiere su revisión. |
| **RF-16** | El sistema debe notificar al solicitante cuando su solicitud es aprobada o rechazada. |
| **RF-17** | El sistema debe notificar a IT Admin cuando una solicitud está lista para provisioning. |
| **RF-18** | El sistema debe notificar al usuario y a IT cuando un acceso está próximo a expirar. |

### Auditoría e historial

| ID | Requerimiento |
|----|---------------|
| **RF-19** | El sistema debe registrar en auditoría cada evento relevante del ciclo de vida de una solicitud. |
| **RF-20** | El sistema debe permitir consultar el historial completo de una solicitud, incluyendo quién realizó cada acción y cuándo. |

### Consultas

| ID | Requerimiento |
|----|---------------|
| **RF-21** | El sistema debe permitir a cada usuario listar sus solicitudes. |
| **RF-22** | El sistema debe permitir a Manager listar las solicitudes de su equipo. |
| **RF-23** | El sistema debe permitir a Security Reviewer listar las solicitudes que requieren su revisión. |
| **RF-24** | El sistema debe permitir a IT Admin y System Admin listar todas las solicitudes. |
| **RF-25** | El sistema debe permitir ver el detalle de cualquier solicitud autorizada para el rol. |

---

## 4. Requerimientos no funcionales

### Seguridad

| ID | Requerimiento |
|----|---------------|
| **RNF-01** | El sistema debe implementar autenticació. |
| **RNF-02** | El sistema debe validar el rol del usuario en cada endpoint protegido. |
| **RNF-03** | La autorización real debe residir en el backend; el frontend solo aplica autorización visual como ayuda. |
| **RNF-04** | El solicitante no debe poder aprobar su propia solicitud. |

### Trazabilidad

| ID | Requerimiento |
|----|---------------|
| **RNF-05** | Toda acción relevante (creación, aprobación, rechazo, provisioning) debe quedar registrada con timestamp, actor y datos del evento. |
| **RNF-06** | El sistema debe permitir reconstruir el historial completo de cualquier solicitud. |

### Mantenibilidad

| ID | Requerimiento |
|----|---------------|
| **RNF-07** | El dominio no debe depender de frameworks externos (FastAPI, SQLAlchemy, Streamlit). |
| **RNF-08** | La lógica de negocio debe residir en la capa de dominio, no en endpoints ni controladores. |
| **RNF-09** | Las consultas ORM deben estar encapsuladas en repositorios; no se aceptan consultas ORM directamente en endpoints. |

### Usabilidad

| ID | Requerimiento |
|----|---------------|
| **RNF-10** | El frontend debe permitir completar el flujo principal sin necesidad de conocer los endpoints. |
| **RNF-11** | Las notificaciones deben ser visibles para el usuario desde la interfaz. |

### Observabilidad

| ID | Requerimiento |
|----|---------------|
| **RNF-12** | Los eventos del sistema deben ser publicados en un Event Bus para permitir monitoreo y reacciones desacopladas. |

### Separación de ambientes

| ID | Requerimiento |
|----|---------------|
| **RNF-13** | Deben existir ambientes separados de desarrollo (dev) y producción (prod). |
| **RNF-14** | El despliegue a producción solo debe ocurrir mediante push de tag a la rama principal. |
| **RNF-15** | Las imágenes Docker de dev y prod deben estar versionadas y publicadas en Docker Hub. |

---

## 5. Reglas de negocio

| ID | Regla |
|----|-------|
| **RB-01** | Los accesos de nivel READ requieren aprobación de Manager. |
| **RB-02** | Los accesos de nivel WRITE requieren aprobación de Manager. |
| **RB-03** | Los accesos de nivel ADMIN requieren aprobación de Manager y Security Reviewer. |
| **RB-04** | Los accesos a bases de datos productivas requieren revisión de Security Reviewer, sin importar el nivel. |
| **RB-05** | Para accesos ADMIN, la fecha de expiración es obligatoria. |
| **RB-06** | Para accesos READ y WRITE, la fecha de expiración es opcional. |
| **RB-07** | El solicitante no puede aprobar su propia solicitud. |
| **RB-08** | Una solicitud rechazada no puede volver a aprobarse; debe crearse una nueva. |
| **RB-09** | Solo IT Admin puede marcar una solicitud como completada. |
| **RB-10** | Una solicitud aprobada debe pasar a READY_FOR_PROVISIONING antes de completarse. |

---

## 6. Estados del flujo principal

### Estados

| Estado | Descripción |
|--------|-------------|
| **DRAFT** | La solicitud está siendo creada por el empleado, aún no se envía. |
| **SUBMITTED** | La solicitud fue enviada y está pendiente de revisión por el Manager. |
| **MANAGER_REVIEW** | La solicitud está siendo revisada por el Manager del solicitante. |
| **SECURITY_REVIEW** | La solicitud requiere revisión adicional de Security Reviewer. |
| **APPROVED** | La solicitud fue aprobada por todos los revisores requeridos. |
| **READY_FOR_PROVISIONING** | La solicitud está lista para que IT Admin complete el provisioning. |
| **COMPLETED** | El acceso fue provisionado y la solicitud está finalizada. |
| **REJECTED** | La solicitud fue rechazada. Estado final, no puede reabrirse. |
| **CANCELLED** | La solicitud fue cancelada por el solicitante antes de completarse. |
| **CHANGES_REQUESTED** | Un aprobador solicitó modificaciones; la solicitud vuelve a DRAFT. |

### Transiciones válidas

```
DRAFT               → SUBMITTED
SUBMITTED           → MANAGER_REVIEW
MANAGER_REVIEW      → SECURITY_REVIEW  (si aplica)
MANAGER_REVIEW      → APPROVED         (si no requiere Security)
SECURITY_REVIEW     → APPROVED
MANAGER_REVIEW      → REJECTED
SECURITY_REVIEW     → REJECTED
MANAGER_REVIEW      → CHANGES_REQUESTED
SECURITY_REVIEW     → CHANGES_REQUESTED
CHANGES_REQUESTED   → DRAFT
SUBMITTED           → CANCELLED
MANAGER_REVIEW      → CANCELLED
APPROVED            → READY_FOR_PROVISIONING
READY_FOR_PROVISIONING → COMPLETED
```

### Transiciones inválidas

- REJECTED no puede transicionar a ningún otro estado.
- COMPLETED no puede transicionar a ningún otro estado.
- CANCELLED no puede transicionar a ningún otro estado.
- DRAFT no puede saltar directamente a APPROVED.

---

## 7. Eventos del sistema

| Evento | Cuándo ocurre | Quién lo dispara | Datos que contiene | Genera notificación | Registra auditoría |
|--------|---------------|------------------|--------------------|:---:|:---:|
| **ACCESS_REQUEST_CREATED** | Al crear una solicitud en DRAFT | Employee | ID, sistema, nivel, solicitante | No | Sí |
| **ACCESS_REQUEST_SUBMITTED** | Al enviar la solicitud | Employee | ID, sistema, nivel, solicitante, manager | Sí (Manager) | Sí |
| **MANAGER_APPROVAL_REQUEST** | Al entrar en MANAGER_REVIEW | Sistema | ID, manager asignado | Sí (Manager) | Sí |
| **SECURITY_REVIEW_REQUEST** | Al entrar en SECURITY_REVIEW | Sistema | ID, security reviewer | Sí (Security) | Sí |
| **ACCESS_REQUEST_APPROVED** | Al ser aprobada completamente | Último aprobador | ID, quién aprobó, timestamp | Sí (Solicitante, IT Admin si aplica) | Sí |
| **ACCESS_REQUEST_REJECTED** | Al ser rechazada | Manager o Security | ID, quién rechazó, motivo | Sí (Solicitante) | Sí |
| **CHANGES_REQUESTED** | Al solicitar cambios | Manager o Security | ID, quién solicitó cambios, comentario | Sí (Solicitante) | Sí |
| **ACCESS_PROVISIONED** | Al completar el provisioning | IT Admin | ID, quién provisionó, timestamp | Sí (Solicitante) | Sí |
| **ACCESS_EXPIRING_SOON** | Al detectar expiración próxima | Sistema (scheduler) | ID, días restantes, nivel | Sí (Usuario, IT Admin, Security si ADMIN) | Sí |
| **ACCESS_EXPIRED** | Al detectar que expiró | Sistema (scheduler) | ID, días vencido, nivel | Sí (Usuario, IT Admin, Security si ADMIN) | Sí |

---

## 8. Notificaciones

| Evento que notifica | Destinatario(s) | Canal | Prioridad |
|---------------------|------------------|-------|:---:|
| ACCESS_REQUEST_CREATED | Manager | In-app | Baja |
| ACCESS_REQUEST_SUBMITTED | Manager | In-app | Media |
| MANAGER_APPROVAL_REQUIRED | Manager | In-app | Media |
| SECURITY_REVIEW_REQUIRED | Security Reviewer | In-app | Alta |
| ACCESS_REQUEST_APPROVED | Solicitante | In-app | Media |
| ACCESS_REQUEST_REJECTED | Solicitante | In-app | Media |
| ACCESS_PROVISIONED | Solicitante | In-app | Media |
| ACCESS_EXPIRING_SOON | Solicitante, IT Admin| In-app | Alta |
| READY_FOR_PROVISIONING | IT Admin | In-app | Alta |
---

## 9. Alcance del MVP

### Incluye

- Registro y autenticación de usuarios con roles (Employee, Manager, Security Reviewer, IT Admin, System Admin)
- Creación de solicitudes de acceso con sistema destino, nivel y expiración
- Flujo de aprobación: Manager Review → Security Review (si aplica) → Approved
- Provisioning por IT Admin y cierre de solicitudes
- Notificaciones por eventos (in-app)
- Registro de auditoría para todas las acciones relevantes
- Verificación de expiración y notificación de accesos próximos a vencer
- Frontend funcional con vistas por rol
- Despliegue en ambientes dev y prod

### Fuera de alcance

- Integración real con GitHub, cloud o bases de datos
- Revocación automática de accesos
- Sincronización con Active Directory
- Escaneo real de permisos existentes
- Reportes avanzados de compliance

---

## 10. Riesgos, supuestos y preguntas abiertas

### Riesgos técnicos

- La verificación periódica de expiración requiere un scheduler, lo cual puede ser complejo en ambiente serverless como Render.
- El MVP no incluye revocación automática, por lo que un acceso expirado seguirá activo hasta que alguien lo revoque manualmente fuera del sistema.
### Riesgos de alcance

- El flujo de aprobación puede volverse más complejo si se agregan nuevos niveles de acceso o sistemas especiales en el futuro.
- La cantidad de estados y transiciones puede crecer si se añaden excepciones por tipo de sistema.

### Supuestos

- Cada empleado tiene un Manager asignado.
- El Security Reviewer es un rol definido y conocido por el sistema.
- La provisión del acceso es un paso manual que realiza IT Admin fuera del sistema.
- Las fechas de expiración son definidas por el solicitante al crear la solicitud.

### Preguntas abiertas

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué niveles de acceso existen? | READ, WRITE y ADMIN. Cada uno implica un riesgo y flujo de aprobación distinto. |
| ¿Todos los accesos siguen el mismo flujo de aprobación? | No. READ y WRITE requieren solo Manager. ADMIN requiere Manager y Security. Bases de datos productivas requieren Security sin importar el nivel. |
| ¿La fecha de expiración es obligatoria para todos los accesos? | No. Para ADMIN es obligatoria. Para READ y WRITE es opcional. |
| ¿Qué restricciones existen sobre quién puede ejecutar cada acción? | El solicitante no puede aprobar su propia solicitud. Solo IT Admin puede completar el provisioning. Una solicitud rechazada no puede reabrirse. |
| ¿Qué sistemas requieren revisión de Security? | Accesos ADMIN y cualquier acceso a bases de datos productivas, sin importar el nivel. |
| ¿Qué entra en el MVP y qué se deja fuera? | Entra: trazabilidad completa, flujo de aprobación, notificaciones, auditoría. Fuera: integración real con sistemas, revocación automática, Active Directory, reportes avanzados. |
| ¿Cuál es el dolor principal que se debe resolver? | La falta de trazabilidad. Seguridad no puede responder quién tiene acceso a qué, quién lo aprobó ni cuándo debería expirar. |
| ¿Qué pasa cuando una solicitud es rechazada? | No puede reabrirse. El solicitante debe crear una nueva si aún necesita el acceso. |
| ¿Quién completa el proceso de provisioning? | Únicamente IT Admin. Una solicitud aprobada debe pasar a READY_FOR_PROVISIONING antes de que IT Admin pueda completarla. |
