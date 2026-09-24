# 006 — Sistema de diseño (estilo macOS)

- Estado: Implementada
- Relacionadas: 002

## Principios
1. **Colores sólidos.** Nada de transparencias, blur, vibrancy ni glassmorphism.
2. **Bordes finos (1 px) y esquinas redondeadas consistentes**, como los controles de AppKit.
3. **Cero emojis** en la interfaz. Todo símbolo es un icono de la familia Phosphor (regular),
   cuyo trazo fino es el más cercano a SF Symbols con licencia libre (MIT, vía `qtawesome`).
   SF Symbols no puede redistribuirse fuera de plataformas Apple.
4. Jerarquía por **tipografía y espacio**, no por color. El acento se reserva para la acción
   principal, la selección y el foco.
5. Tema claro y oscuro con la misma estructura; por defecto sigue al sistema.

## Tokens (`ui/theme/tokens.py`)

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `window` | `#ECECEC` | `#1E1E1E` | Fondo base |
| `sidebar` | `#E3E3E3` | `#262626` | Sidebar (sólido) |
| `content` | `#F5F5F7` | `#232323` | Área de páginas |
| `card` | `#FFFFFF` | `#2C2C2E` | Tarjetas, campos, botones secundarios |
| `separator` | `#D1D1D6` | `#3A3A3C` | Bordes y separadores |
| `border_strong` | `#C1C1C6` | `#48484A` | Borde de controles |
| `text_primary` | `#1D1D1F` | `#F5F5F7` | Texto |
| `text_secondary` | `#626267` | `#98989D` | Subtítulos, ayudas |
| `accent` | `#0071E3` | `#0071E3` | Relleno de acción principal, selección, foco |
| `accent_pressed` | `#005BBF` | `#005BBF` | Pulsado |
| `accent_text` | `#0066CC` | `#409CFF` | Acento usado como texto o icono |
| `on_accent` | `#FFFFFF` | `#FFFFFF` | Texto sobre acento |
| `sidebar_selected` | `#D0D0D5` | `#3A3A3C` | Ítem activo del sidebar |
| `success` | `#1E7B34` | `#30D158` | Estados |
| `danger` | `#D70015` | `#FF6961` | Errores |
| `success_bg` / `info_bg` / `danger_bg` | `#E6F4EA` / `#E5F0FF` / `#FDECEC` | `#1E3324` / `#1B2B40` / `#3A1F1F` | Fondos de banners |
| `control_hover` / `control_pressed` | `#F7F7F9` / `#E5E5EA` | `#333336` / `#3F3F42` | Botones secundarios |
| `track` / `thumb` | `#E3E3E8` / `#FFFFFF` | `#3A3A3C` / `#636366` | Control segmentado, barra de progreso |

### Contraste (WCAG AA ≥ 4.5:1)
Se parte de los colores de sistema de macOS y se ajustan solo donde no alcanzan 4.5:1; un test
unitario (`tests/unit/ui/test_theme.py`) lo verifica para cada par texto/fondo.
- El azul de sistema `#007AFF` da 4.0:1 con texto blanco: los rellenos usan `#0071E3`, el azul de
  los botones de apple.com (4.7:1).
- El acento como **texto o icono** necesita tonos distintos en claro y oscuro, por eso existe
  `accent_text` separado de `accent`.
- Texto secundario y estados usan las variantes de mayor contraste de la paleta de Apple.

**Radios:** control 6 px · tarjeta 10 px · ventana/hoja 12 px.
**Espaciado:** rejilla de 4 px (4, 8, 12, 16, 20, 24, 32).
**Tipografía:** Inter (si está en `ui/theme/fonts/`), si no la fuente del sistema. Cuerpo 13 px,
título de página 22 px semibold, título de sección 13 px semibold en `text_secondary`.
Monoespaciada: JetBrains Mono → fuente monoespaciada del sistema.

## Cómo se aplica
- Estilo base **Fusion** + `QPalette` generada desde los tokens + **QSS** generado desde una única
  plantilla (`qss_template.qss`, `string.Template`).
  La paleta hace falta porque QSS no alcanza a menús contextuales, diálogos y tooltips nativos.
- `QStyleHints.colorScheme()` + señal `colorSchemeChanged` para seguir al sistema.

## Componentes

| Componente | Archivo | Detalle |
|---|---|---|
| Sidebar | `widgets/sidebar.py` | Fondo `sidebar`, ítems icono+texto, selección como píldora de 6 px, borde derecho 1 px |
| Botón primario | QSS `QPushButton[variant="primary"]` | Fondo `accent`, texto `on_accent` |
| Botón secundario | QSS por defecto | Fondo `card`, borde 1 px `border_strong` |
| Control segmentado | `widgets/segmented_control.py` | Pintado con `QPainter`: contenedor con borde, segmento activo sólido |
| Switch | `widgets/switch.py` | Pintado con `QPainter`, animado con `QPropertyAnimation` |
| Lista agrupada | `widgets/grouped_list.py` | Filas dentro de una tarjeta con separadores internos de 1 px (Ajustes del Sistema) |
| Campo de contraseña | `widgets/password_field.py` | Acción ojo/ojo tachado dentro del campo |
| Zona de arrastre | `widgets/drop_zone.py` | Borde discontinuo, se resalta en `accent` al arrastrar |
| Banner | `widgets/banner.py` | Mensajes inline (error/éxito/info) en lugar de `QMessageBox` |
| Tarjeta de capa | `widgets/layer_card.py` | Modo Proceso: título, descripción y valores monoespaciados |

Foco: borde de 2 px en `accent` (QSS no permite anillos exteriores; así se imita sin blur).

## Iconos lógicos (`ui/theme/icons.py`)
`encrypt, decrypt, text, files, process, history, settings, eye, eye_off, copy, trash, upload,
folder, close, success, error, info, key, export`. Las páginas usan estos nombres, nunca los de
Phosphor.
