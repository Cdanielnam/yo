# Casa Punta Mango — Renders para propuesta

Renders generados a partir de los planos de Casa Punta Mango (planta de conjunto, primer y segundo nivel),
el croquis del lote (18 × 80 m, mar al sur, acceso por Calle Punta Mango) y la ficha catastral
de la parcela 1110R31/688 (Cantón El Zapote, Jucuarán, Usulután).

## v2 (diseño vigente: techo de teja, terraza perimetral, piscina en L)

| Archivo | Vista |
|---|---|
| v2/01_vista_principal.png | Fachada hacia el mar desde el deck de la piscina, luz de día |
| v2/02_vista_balcon_mar.png | Desde la terraza del segundo nivel hacia la piscina, el bar y la playa |
| v2/03_vista_aerea.png | Lote completo desde el mar |
| v2/04_vista_atardecer.png | Fachada hacia el mar al atardecer con iluminación interior |
| v2/05_vista_acceso.png | Desde el acceso principal: calzada, estacionamiento, patio-jardín y fachada de entrada |
| v2/06_nivel1_interior.png | Maqueta seccionada del nivel 1 con espacios etiquetados |
| v2/07_nivel2_interior.png | Maqueta seccionada del nivel 2 (sin techo) con espacios etiquetados |

Propuesta en PDF: `Propuesta_Casa_Punta_Mango_v3.pdf` (12 páginas). Las versiones anteriores (v1, v2) se conservan.

Resolución: 2560 × 1440 px. Motor: Blender Cycles (path tracing), reducción de ruido OpenImageDenoise.
Escena: `v2/escena_blender_v2.py` + `v2/lib2.py` + `v2/tail2.py` (ejecutar con `python3 escena_blender_v2.py <vista> final`).
