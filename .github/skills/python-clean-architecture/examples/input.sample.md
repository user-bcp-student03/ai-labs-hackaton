## Business context (brief)
El servicio Python ha mezclado reglas de negocio con HTTP y persistencia, por lo que cambiar el almacenamiento requiere modificar la lógica de la funcionalidad.

## Feature request / user story
Como equipo de desarrollo, queremos separar el caso de uso de creación de pedidos de FastAPI y del ORM para probar las reglas y poder cambiar adaptadores sin alterar el comportamiento.

## Expected impact
Las reglas de creación de pedidos pueden probarse sin iniciar la aplicación web ni conectarse a una base de datos real.

## Scope (in/out)
In: caso de uso de creación, validación de reglas, contrato del repositorio y adaptadores HTTP y de persistencia existentes.
Out: reemplazo del framework, cambio del contrato HTTP y rediseño completo del modelo de dominio.

## Known technical constraints
Python 3.12, FastAPI, SQLAlchemy y pytest. El endpoint existente debe conservar su formato de solicitud y respuesta.

## Known risks
Cambios en códigos de error, persistencia parcial durante la transición y fuga de detalles del ORM hacia el dominio.

## Dependencies
Base de datos relacional existente, autenticación actual y adaptador de persistencia del proyecto.

## Team Definition of Done (DoD)
Pruebas del caso de uso sin infraestructura, pruebas de integración del adaptador, regresión del endpoint y documentación breve de la dirección de dependencias.

## Current architecture (if available)
La ruta HTTP valida la solicitud, ejecuta reglas de negocio y realiza consultas ORM en la misma función.
