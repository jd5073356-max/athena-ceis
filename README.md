<p align="center">
  <img src="./hero-banner.png" alt="Athena Enterprise School Management Platform Header" width="100%" />
</p>

# Athena — Enterprise School Management Platform

[![status](https://img.shields.io/badge/status-migración%20activa-orange?style=for-the-badge)](https://athena.maxstudio.lat)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.x-092e20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Oracle](https://img.shields.io/badge/Oracle-Database-red?style=for-the-badge&logo=oracle&logoColor=white)](https://oracle.com)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-4285f4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

> **Plataforma de gestión escolar centralizada.** Sistema administrativo de alto rendimiento desarrollado en Django y preparado para Google Cloud Run con base de datos Oracle Enterprise, diseñado para la administración integral de instituciones educativas.

---

## 🎯 ¿Por qué existe Athena? (La Problemática)

Las instituciones educativas manejan una carga documental y académica crítica que requiere un entorno centralizado de alta disponibilidad.

**Desafíos resueltos por la arquitectura de Athena:**
1. **Centralización de Cargas Académicas:** Eliminación de conflictos en asignaciones de docentes, grados y materias institucionales.
2. **Estructuración de Contenidos Pedagógicos:** Organización sistemática de guías de estudio, talleres y material académico clasificado por año, periodo y grado.
3. **Control Rectoral:** Visibilidad estratégica para la dirección escolar sobre la actividad académica y el flujo institucional.

---

## ⚡ ¿Para qué sirve? (Propósito del Sistema)

- **Gestión Académica Centralizada:** Control estructurado de asignaturas y cursos con jerarquía clara por áreas de conocimiento.
- **Panel de Rectoría:** Interfaz administrativa avanzada (`panel_rector`) para supervisión, métricas de avance y control de publicaciones.
- **Integración con la Nube:** Preparado para sincronización en la nube con Google Cloud Storage (GCS) y arquitectura serverless container.

---

## 🏗️ Arquitectura de Infraestructura

```mermaid
graph TD
    User([Estudiante / Docente / Rector]) -->|HTTPS / SSL| CloudRun[Google Cloud Run Container]
    
    subgraph Core de la Aplicación
        CloudRun --> WSGI[Gunicorn WSGI Server]
        WSGI --> DjangoCore[Django 5.x Framework]
        DjangoCore --> AdminPanel[Panel Rector / Django Admin Custom]
        DjangoCore --> PublicWeb[Portal Público / Visor de Guías]
    end
    
    subgraph Capa de Persistencia
        DjangoCore <--> OracleDB[(Oracle Enterprise Database)]
        DjangoCore <--> GCS[(Google Cloud Storage - Media Assets)]
    end
```

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.11+
- **Framework Web:** Django 5.x
- **Base de Datos:** Oracle Enterprise Database
- **Infraestructura:** Google Cloud Run, Docker
- **Almacenamiento:** Google Cloud Storage (GCS)
- **Frontend:** HTML5, Vanilla CSS3, JavaScript

---

## 👤 Autor

**Juan David Herrera**  
*AI Automation Engineer | Product Engineer · AI, Systems & Web3*  
Bogotá, Colombia  
- **GitHub:** [@jd5073356-max](https://github.com/jd5073356-max)  
- **LinkedIn:** [linkedin.com/in/juan-david-herrera](https://linkedin.com)
