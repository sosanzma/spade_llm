# Guía de Estilo para Documentación SpadeLLM

## Objetivo
Aplicar el tema púrpura/violeta consistente con el diseño del sitio web principal de SPADE a la documentación de SpadeLLM para crear una experiencia visual cohesiva.

## Colores del Tema SpadeLLM

### Colores Principales
- **Púrpura Principal**: `#8e44ad`
- **Púrpura Secundario**: `#9b59b6`
- **Púrpura Oscuro**: `#7d3c98` (para hover)
- **Púrpura Acento**: `#a569bd` (modo oscuro)
- **Púrpura Claro**: `#bb8fce` (modo oscuro)

### Gradientes Estándar
```css
/* Gradiente principal */
background: linear-gradient(135deg, #8e44ad, #9b59b6);

/* Gradiente hover */
background: linear-gradient(135deg, #7d3c98, #8e44ad);

/* Gradiente modo oscuro */
background: linear-gradient(135deg, #a569bd, #bb8fce);
```

## Modificaciones Requeridas

### 1. Configuración MkDocs (`mkdocs.yml`)

**Localizar** el archivo `mkdocs.yml` en la raíz del proyecto y **modificar** la sección `theme`:

```yaml
theme:
  name: material
  palette:
    # Modo claro
    - scheme: default
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Modo oscuro
    - scheme: slate
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.highlight
    - search.share
    - toc.integrate

# Agregar referencia al CSS personalizado
extra_css:
  - stylesheets/custom.css
```

### 2. CSS Personalizado

**Crear** el directorio `docs/stylesheets/` si no existe.

**Crear** el archivo `docs/stylesheets/custom.css` con el siguiente contenido:

```css
/* Variables CSS para tema SpadeLLM */
:root {
  --md-primary-fg-color: #8e44ad;
  --md-primary-fg-color--light: #9b59b6;
  --md-primary-fg-color--dark: #7d3c98;
  --md-accent-fg-color: #9b59b6;
  --spade-gradient: linear-gradient(135deg, #8e44ad, #9b59b6);
  --spade-gradient-hover: linear-gradient(135deg, #7d3c98, #8e44ad);
}

/* Header con gradiente púrpura */
.md-header {
  background: var(--spade-gradient) !important;
}

/* Botones con estilo SpadeLLM */
.md-button {
  background: var(--spade-gradient);
  border: none;
  color: white;
  transition: all 0.3s ease;
  border-radius: 8px;
  padding: 0.5rem 1.5rem;
  font-weight: 500;
}

.md-button:hover {
  background: var(--spade-gradient-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(142, 68, 173, 0.3);
}

/* Enlaces con color púrpura */
.md-content a {
  color: #8e44ad;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.3s ease;
}

.md-content a:hover {
  color: #7d3c98;
  border-bottom-color: #9b59b6;
}

/* Bloques de código con acento púrpura */
.md-typeset .highlight {
  border-left: 4px solid #9b59b6;
  background: rgba(142, 68, 173, 0.05);
}

.md-typeset .highlight:hover {
  border-left-color: #8e44ad;
}

/* Navegación lateral activa */
.md-nav__item--active > .md-nav__link {
  color: #8e44ad;
  font-weight: 600;
}

.md-nav__link:hover {
  color: #7d3c98;
}

/* Pestañas de navegación */
.md-tabs__item--active {
  color: #8e44ad;
}

/* Badges y etiquetas */
.md-typeset .admonition.info {
  border-left-color: #9b59b6;
}

.md-typeset .admonition.info > .admonition-title {
  background: rgba(142, 68, 173, 0.1);
  color: #8e44ad;
}

/* Tabla de contenidos */
.md-nav__item .md-nav__link--active {
  color: #8e44ad;
}

/* Elementos de búsqueda */
.md-search__input {
  border-bottom: 2px solid #9b59b6;
}

.md-search__input:focus {
  border-bottom-color: #8e44ad;
}

/* Modo oscuro */
[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #a569bd;
  --md-primary-fg-color--light: #bb8fce;
  --md-primary-fg-color--dark: #8e44ad;
  --md-accent-fg-color: #bb8fce;
  --spade-gradient: linear-gradient(135deg, #a569bd, #bb8fce);
  --spade-gradient-hover: linear-gradient(135deg, #8e44ad, #a569bd);
}

[data-md-color-scheme="slate"] .md-content a {
  color: #bb8fce;
}

[data-md-color-scheme="slate"] .md-content a:hover {
  color: #d2b4de;
}

[data-md-color-scheme="slate"] .md-typeset .highlight {
  border-left-color: #bb8fce;
  background: rgba(165, 105, 189, 0.1);
}

/* Animaciones suaves */
.md-nav__link,
.md-button,
.md-content a {
  transition: all 0.3s ease;
}

/* Sombras púrpuras para elementos interactivos */
.md-button:focus,
.md-button:hover {
  box-shadow: 0 4px 12px rgba(142, 68, 173, 0.3);
}

/* Personalización adicional para elementos específicos */
.md-typeset h1,
.md-typeset h2 {
  color: #8e44ad;
}

[data-md-color-scheme="slate"] .md-typeset h1,
[data-md-color-scheme="slate"] .md-typeset h2 {
  color: #bb8fce;
}

/* Mejoras para elementos de código inline */
.md-typeset code {
  background: rgba(142, 68, 173, 0.1);
  border: 1px solid rgba(142, 68, 173, 0.2);
  color: #8e44ad;
}

[data-md-color-scheme="slate"] .md-typeset code {
  background: rgba(165, 105, 189, 0.15);
  border-color: rgba(165, 105, 189, 0.3);
  color: #bb8fce;
}
```

### 3. Verificación de Estructura

**Asegurar** que la estructura final sea:
```
docs/
├── index.md
├── stylesheets/
│   └── custom.css
├── [otras carpetas de documentación]
└── [otros archivos .md]
```

### 4. Elementos Adicionales (Opcional)

Si existe un archivo `docs/index.md`, **considerar agregar** badges o elementos visuales que coincidan con el estilo:

```markdown
<div style="text-align: center; margin: 2rem 0;">
  <span style="background: linear-gradient(135deg, #8e44ad, #9b59b6); color: white; padding: 0.5rem 1.5rem; border-radius: 25px; font-weight: 500;">
    🚀 SpadeLLM Extension
  </span>
</div>
```

## Instrucciones de Implementación

1. **Localizar** el repositorio de spade_llm
2. **Verificar** que utiliza MkDocs Material como framework de documentación
3. **Aplicar** las modificaciones en el orden indicado
4. **Probar** la documentación localmente con `mkdocs serve`
5. **Verificar** que el tema púrpura se aplica correctamente en ambos modos (claro y oscuro)
6. **Confirmar** que todos los elementos interactivos mantienen consistencia visual

## Resultado Esperado

La documentación debe lucir con el mismo esquema de colores púrpura/violeta que la sección SpadeLLM del sitio web principal, creando una experiencia visual cohesiva y profesional que refuerza la identidad de marca de SpadeLLM dentro del ecosistema SPADE.