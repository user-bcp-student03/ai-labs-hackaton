# Python Clean Architecture -> Proposal Checklist

## 1. Summary
Separar la creación de pedidos en un caso de uso independiente del framework y del ORM, manteniendo el contrato HTTP actual.

## 2. Scope
- **Dentro del alcance:** caso de uso de creación, puerto del repositorio y adaptadores HTTP y SQLAlchemy.
- **Fuera del alcance:** reemplazo del framework, cambio del contrato HTTP y rediseño completo del dominio.

## 3. Propuesta de arquitectura
- **Dominio:** reglas e invariantes del pedido; sin imports de FastAPI ni SQLAlchemy.
- **Aplicación:** caso de uso `CreateOrder` y un puerto `OrderRepository` expresado como `Protocol` o interfaz equivalente.
- **Adaptadores:** ruta FastAPI traduce HTTP a una entrada del caso de uso; repositorio SQLAlchemy implementa el puerto.
- **Composición:** la configuración de la aplicación conecta el caso de uso con el adaptador concreto. Las dependencias apuntan hacia dominio/aplicación.

## 4. Decisiones técnicas
- Mantener FastAPI y SQLAlchemy como adaptadores externos durante esta entrega.
- Usar un puerto de repositorio mínimo, limitado a las operaciones necesarias por el caso de uso.
- No crear una capa de dominio adicional si las reglas actuales no la requieren.

## 5. Riesgos y mitigaciones
- **Cambio accidental del contrato HTTP:** conservar pruebas de regresión para solicitudes, respuestas y códigos de error.
- **Acoplamiento del dominio al ORM:** comprobar imports y usar modelos de persistencia solo dentro del adaptador.
- **Persistencia parcial durante la migración:** probar límites transaccionales en la integración del repositorio.

## 6. Acceptance criteria (measurable)
- El caso de uso se prueba sin iniciar FastAPI ni abrir una conexión de base de datos.
- El dominio y la aplicación no importan módulos de FastAPI o SQLAlchemy.
- La solicitud, respuesta y códigos HTTP del endpoint existente conservan su comportamiento cubierto por las pruebas de regresión.
- Una prueba de integración verifica que el adaptador de persistencia implemente el contrato requerido por el caso de uso.

## 7. Plan de validación
- Pruebas unitarias del dominio y del caso de uso con un repositorio falso.
- Pruebas de integración del adaptador SQLAlchemy y sus límites transaccionales.
- Pruebas de regresión del endpoint para los formatos de solicitud y respuesta existentes.
- Revisar dependencias/imports para confirmar que los módulos internos no dependan del framework ni del ORM.

## 8. Plan de implementación
1. Caracterizar el comportamiento actual del endpoint y las reglas de creación.
2. Definir el puerto mínimo requerido por el caso de uso.
3. Implementar el caso de uso y probarlo sin infraestructura.
4. Adaptar el repositorio SQLAlchemy y conectar dependencias desde el punto de composición.
5. Mantener la ruta como adaptador HTTP y ejecutar las pruebas de regresión e integración.

## 9. Preguntas abiertas
- ¿Qué comportamiento y código de error existentes deben conservarse para pedidos inválidos?
- ¿La aplicación ya cuenta con un punto de composición para inyectar dependencias?
