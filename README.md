# AccessFlow

Plataforma de solicitudes de acceso interno

**Caso de negocio:** AccessFlow  
**Integrantes:** 
Santiago Reátegui - María Emilia Cueva - Raymond Portilla - Liam Huang

---

## 1. Descripción del problema

Las empresas que utilizan múltiples herramientas internas (GitHub, bases de datos, dashboards financieros, CRM, herramientas de soporte, ambientes cloud y paneles administrativos) suelen gestionar las solicitudes de acceso de forma informal: Slack, correo electrónico o mensajes directos al equipo de IT.

Este proceso genera problemas graves:

- **Falta de trazabilidad:** no queda registro claro de quién solicitó qué, quién lo aprobó ni por cuánto tiempo debería mantenerse el acceso.
- **Riesgo de seguridad:** existen accesos antiguos que nunca fueron revocados y no se sabe si siguen siendo necesarios.
- **Proceso inconsistente:** a veces el manager aprueba por mensaje, otras veces IT da acceso directamente, sin un flujo estandarizado.
- **Preocupación de auditoría:** las empresas en crecimiento enfrentan auditorías internas de seguridad que requieren respuestas claras sobre quién tiene acceso a qué.

**AccessFlow** es la solución que centraliza las solicitudes de acceso en una plataforma con roles definidos, flujo de aprobación controlado, notificaciones automáticas y auditoría completa.

---

## 2. Stack técnico

| Componente | Tecnología |
|------------|------------|
| **Backend** | FastAPI (Python) |
| **Frontend** | Streamlit |
| **Base de datos** | PostgreSQL |
| **ORM** | SQLAlchemy |
| **Infraestructura** | Docker Compose |
| **CI/CD** | GitHub Actions + Docker Hub + Render |
| **Arquitectura** | Hexagonal (Ports & Adapters) |

---

## 3. Arquitectura propuesta

El sistema sigue **Arquitectura Hexagonal**, que garantiza que el dominio no dependa de ninguna tecnología externa. Las reglas de negocio están completamente aisladas de FastAPI, Streamlit, SQLAlchemy y servicios externos.

### Capas

| Capa | Responsabilidad |
|------|-----------------|
| **Domain** | Entidades, value objects, enums, reglas de negocio, estados, eventos, interfaces de repositorios y abstracciones de patrones de diseño. No depende de ninguna librería externa. |
| **Application** | Casos de uso, DTOs y orquestación del flujo entre dominio e infraestructura. Coordina las operaciones sin contener lógica de negocio. |
| **Infrastructure** | Modelos ORM, repositorios concretos, Event Bus, observers, autenticación JWT y conexión a base de datos. |
| **API** | Rutas FastAPI, guards de autorización, dependencias e inyección de servicios. |
| **Frontend** | Vistas Streamlit, formularios, manejo de sesión y cliente HTTP para consumir la API. |

### Patrones de diseño aplicados

El proyecto aplica **8 patrones de diseño** de forma práctica y justificada por las reglas de negocio del caso.

---

#### Patrones creacionales

**Factory Method**
> **Problema:** Crear una solicitud de acceso no es trivial. Según el nivel (READ, WRITE, ADMIN) cambian las validaciones, el flujo de aprobación y si la fecha de expiración es obligatoria.
>
> **Solución:** Una factory centraliza la creación de `AccessRequest`, aplicando las validaciones correctas según el nivel y asignando la expiración obligatoria para accesos ADMIN.
>
> **Beneficio:** La lógica de creación no está dispersa en endpoints ni casos de uso. Agregar un nuevo nivel solo requiere extender la factory.

**Abstract Factory**
> **Problema:** El pipeline de aprobación varía según el nivel de acceso y el sistema solicitado. READ/WRITE requiere solo Manager. ADMIN requiere Manager + Security. Bases de datos productivas siempre requieren Security, sin importar el nivel.
>
> **Solución:** Una Abstract Factory compone familias coherentes de pasos de aprobación. `StandardApprovalFlowFactory`, `AdminApprovalFlowFactory` y `ProductiveDatabaseFlowFactory` crean el pipeline correcto según el contexto.
>
> **Beneficio:** El motor de flujo no necesita saber qué pasos componer. Agregar un nuevo tipo de flujo solo requiere una nueva factory.

**Singleton**
> **Problema:** El Event Bus debe ser único para que todos los observers reciban los mismos eventos. La configuración y la conexión a base de datos también deben ser únicas para evitar múltiples instancias compitiendo.
>
> **Solución:** Singleton aplicado exclusivamente al Event Bus y a la configuración de la aplicación.
>
> **Beneficio:** Garantiza consistencia en recursos compartidos sin afectar el estado de negocio.

---

#### Patrones de comportamiento

**State**
> **Problema:** El ciclo de vida de una solicitud tiene múltiples estados: DRAFT → SUBMITTED → MANAGER_REVIEW → SECURITY_REVIEW → APPROVED → READY_FOR_PROVISIONING → COMPLETED, más REJECTED, CANCELLED y CHANGES_REQUESTED. No todas las transiciones son válidas: una solicitud rechazada no puede reabrirse, solo IT Admin puede completar el provisioning, y el solicitante no puede aprobar su propia solicitud.
>
> **Solución:** El patrón State encapsula cada estado en su propia clase con reglas de transición explícitas. La entidad `AccessRequest` delega en su estado actual para cada acción posible.
>
> **Beneficio:** Las reglas de transición están centralizadas y son auditables. Agregar un nuevo estado no requiere modificar los existentes.

**Observer**
> **Problema:** Cada evento del sistema debe disparar múltiples reacciones independientes. Los casos de uso no deberían conocer estos detalles.
>
> **Solución:** El `EventBus` publica eventos. `NotificationObserver` y `AuditLogObserver` se suscriben y reaccionan sin que el emisor sepa de su existencia.
>
> **Beneficio:** Agregar una nueva reacción a un evento (ej. enviar a un canal de Slack) solo requiere crear un nuevo observer sin modificar el flujo principal.

**Command**
> **Problema:** Acciones como aprobar, rechazar o provisionar un acceso implican múltiples pasos: validar reglas de negocio, cambiar estado, persistir, publicar evento, registrar auditoría. Sin encapsulamiento, esta lógica se dispersaría en servicios extensos y difíciles de mantener.
>
> **Solución:** Cada acción del sistema se encapsula en su propio comando con validaciones y efectos secundarios bien definidos.
>
> **Beneficio:** Cada comando tiene una responsabilidad clara. La validación de "no auto-aprobarse" está donde pertenece, no repetida en múltiples lugares.

**Strategy**
> **Problema:** Las reglas de quién debe aprobar cambian según el nivel de acceso y el sistema solicitado. No se quiere lógica condicional dispersa por el motor de flujo.
>
> **Solución:** `ApprovalPolicy` define una interfaz común. `StandardApprovalPolicy`, `AdminApprovalPolicy` y `ProductiveDatabasePolicy` implementan las reglas específicas. Una factory selecciona la política correcta según el contexto de la solicitud.
>
> **Beneficio:** Agregar una nueva política de aprobación solo requiere crear una nueva clase sin modificar el motor de flujo. Principio Open/Closed.

**Template Method**
> **Problema:** La verificación de expiración de accesos sigue un algoritmo fijo (¿tiene fecha? → ¿cuántos días faltan? → ¿expirado? → ¿por expirar? → resultado) pero las reglas varían: ADMIN tiene expiración obligatoria y se notifica con 7 días de anticipación; READ/WRITE tiene expiración opcional y se notifica con 3 días.
>
> **Solución:** `ExpirationChecker` define el esqueleto del algoritmo. `AdminExpirationChecker` y `StandardExpirationChecker` implementan solo los pasos que varían: umbral de aviso, obligatoriedad de fecha y severidad de la notificación.
>
> **Beneficio:** El algoritmo de verificación no se duplica. Agregar una nueva política de expiración solo requiere una nueva subclase.

---

## 4. Cómo correr localmente

### Pre-requisitos

- Python 3.11+
- PostgreSQL 15
- pip

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### Variables de entorno

Crear un archivo `.env` en `backend/` con:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/accessflow
JWT_SECRET=your-secret-key
```

---

## 5. Cómo correr con Docker Compose

```bash
docker compose up --build
```

Esto levanta tres servicios:

| Servicio | Puerto local | Descripción |
|----------|-------------|-------------|
| `db`     | 5433        | PostgreSQL 15 |
| `api`    | 8000        | Backend FastAPI |
| `ui`     | 8501        | Frontend Streamlit |

### Verificar que el backend está listo

```bash
curl http://localhost:8000/docs
```

### Acceder al frontend

Abre tu navegador en: [http://localhost:8501](http://localhost:8501)

---

## 6. Explicación del flujo GitHub Actions

El proyecto cuenta con un pipeline CI/CD definido en `.github/workflows/ci-cd.yml`:

### CI en desarrollo (rama `dev`)

| Evento | Acciones |
|--------|----------|
| **Pull Request → `dev`** | Instalación de dependencias, lint, tests, build de imagen Docker dev |
| **Merge a `dev`** | Validaciones, build de imagen, push a Docker Hub con tag `dev`, redeploy automático en Render dev |

### CD a producción (rama `main`)

| Evento | Acciones |
|--------|----------|
| **Push de tag a `main/master`** | Validaciones, build de imagen producción, push a Docker Hub, redeploy automático en Render prod |

No se acepta despliegue directo a producción desde ramas feature. El flujo garantiza que solo código revisado y mergeado a `main` con un tag llegue a producción.

### Secrets configurados en GitHub

- `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`
- `RENDER_DEV_DEPLOY_HOOK` y `RENDER_PROD_DEPLOY_HOOK`

---

## 7. Ambientes desplegados en Render

| Ambiente | Servicio | URL |
|----------|----------|-----|
| **Dev** | Frontend | [https://pset-accesflow-frontend-dev.onrender.com](https://pset-accesflow-frontend-dev.onrender.com) |
| **Dev** | Backend | [https://pset-accesflow-backend-dev.onrender.com](https://pset-accesflow-backend-dev.onrender.com) |
| **Prod** | Frontend | [https://pset-accesflow-frontend-prod.onrender.com](https://pset-accesflow-frontend-prod.onrender.com) |
| **Prod** | Backend | [https://pset-accesflow-backend-prod.onrender.com](https://pset-accesflow-backend-prod.onrender.com) |

---

## 8. Usuarios de prueba

El sistema incluye cinco usuarios predefinidos que se crean automáticamente al iniciar la aplicación:

| Rol | Email | Contraseña | Permisos |
|-----|-------|-----------|----------|
| **Employee** | `employee@accessflow.com` | `employee123` | Crear solicitudes de acceso, ver sus solicitudes, recibir notificaciones |
| **Manager** | `manager@accessflow.com` | `manager123` | Aprobar, rechazar o solicitar cambios en solicitudes de su equipo |
| **Security Reviewer** | `security@accessflow.com` | `security123` | Revisar accesos sensibles (ADMIN y bases de datos productivas), aprobar o rechazar |
| **IT Admin** | `itadmin@accessflow.com` | `itadmin123` | Completar el provisioning de accesos aprobados |
| **System Admin** | `admin@accessflow.com` | `admin123` | Acceso total: ver todas las solicitudes, auditoría global, notificaciones |

---

## 9. Flujo principal del sistema

1. **Inicio de sesión:** El usuario accede con su email y contraseña. El sistema valida sus credenciales y carga la vista correspondiente a su rol.

2. **Creación de solicitud (Employee):** El empleado completa el formulario con el sistema de destino, el tipo de sistema, el nivel de acceso (READ/WRITE/ADMIN) y una justificación. Si el nivel es ADMIN, la fecha de expiración es obligatoria; para READ y WRITE es opcional.

3. **Envío a revisión:** La solicitud se crea en estado DRAFT y se envía automáticamente a SUBMITTED y luego a MANAGER_REVIEW. El sistema notifica al Manager correspondiente.

4. **Aprobación del Manager:** El Manager revisa la solicitud en su bandeja. Puede **aprobar** (si el acceso es READ o WRITE y no es a base productiva, pasa directamente a APPROVED), **rechazar** (la solicitud queda en estado final REJECTED y no puede reabrirse) o **solicitar cambios** (el empleado deberá editar y reenviar la solicitud).

5. **Revisión de seguridad (si aplica):** Si el acceso es ADMIN o a una base de datos productiva, una vez que el Manager aprueba la solicitud, el sistema la mueve automáticamente a SECURITY_REVIEW. El Security Reviewer puede entonces aprobarla o rechazarla.

6. **Preparación para provisioning:** Una vez que la solicitud llega al estado APPROVED, el sistema la mueve automáticamente a READY_FOR_PROVISIONING y notifica al IT Admin.

7. **Provisionamiento (IT Admin):** El IT Admin ve las solicitudes listas para provisioning y, tras ejecutar la acción, la solicitud pasa al estado final COMPLETED. El acceso queda registrado y el solicitante recibe una notificación.

8. **Notificaciones y auditoría:** Durante todo el flujo, los usuarios reciben notificaciones en la aplicación sobre los eventos relevantes. Cada acción queda registrada en el log de auditoría, visible para el System Admin y asociada a cada solicitud.

---

## 10. Limitaciones conocidas

- **Provisión de acceso simulada:** Completar el provisioning no ejecuta ninguna acción real sobre los sistemas externos (GitHub, bases de datos, etc.). Es un registro simbólico en la plataforma.
- **Revocación no automática:** El sistema detecta y notifica accesos próximos a expirar, pero no revoca los accesos de forma automática. Esta funcionalidad está fuera del alcance del MVP.
- **Sin integración con Active Directory ni escaneo real de permisos:** El sistema no sincroniza con directorios externos ni realiza verificaciones automáticas de los permisos existentes fuera de la plataforma.
- **Reportes de compliance básicos:** La auditoría y las consultas son funcionales, pero los reportes avanzados de cumplimiento (exportación, dashboards específicos) no están incluidos en esta versión.
