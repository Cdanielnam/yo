# Base de datos de presupuestos hidráulicos (MySQL / MariaDB)

Conversión del presupuesto **Opera Tower v4** (hoja `PRES`) a una base de datos SQL.
Incluye la estructura del presupuesto, el catálogo de descripciones de partidas y las
cantidades. **No incluye precios unitarios**: ese es un proceso aparte y se agrega después.

## Archivos

| Archivo | Qué es |
|---|---|
| `presupuesto_hidraulico.sql` | Script completo: crea la base, las tablas, la vista y carga los datos. |
| `generar_sql.py` | Script que lee el Excel y regenera el `.sql`. Sirve para cargar otros presupuestos con el mismo formato. |

## Cómo cargarlo en XAMPP (MySQL / MariaDB)

1. Abre el panel de XAMPP y arranca **Apache** y **MySQL**.
2. Entra a `http://localhost/phpmyadmin`.
3. Pestaña **Importar**, botón **Seleccionar archivo**, elige `presupuesto_hidraulico.sql` y pulsa **Continuar**.
   No hace falta crear la base antes: el script la crea con el nombre `presupuestos_hidraulicos`.

Desde consola también funciona:

```
mysql -u root -p < presupuesto_hidraulico.sql
```

## Estructura

```
unidades        ml, UNIDAD, SG
sistemas        AP agua potable, AN aguas negras, AL aguas lluvias, CI contra incendio
conceptos       catálogo maestro: 1 fila por descripción de partida (64 conceptos)
proyectos       Opera Tower v4
capitulos       A, B, C, D del proyecto  -> sistema
partidas        niveles o bloques dentro de cada capítulo (1..24) con su NPT
presupuesto_detalle   subpartidas: partida + concepto + cantidad
v_presupuesto   vista que reproduce la hoja: capítulo, partida, subpartida, concepto, unidad, cantidad
```

La idea central es que **la descripción vive una sola vez en `conceptos`** y cada presupuesto
solo la referencia por su código (`AP-001`, `CI-013`...). Así se corrige una descripción en un
solo lugar y se reutiliza en el siguiente proyecto.

Cada concepto trae además columnas derivadas de la descripción para filtrar:
`tipo_elemento` (Tubería, Válvula, Rociador...), `material` (PVC, CPVC, Acero al carbón...),
`diametro` y `norma` (ASTM D2241, ASTM A-53...).

## Consultas de ejemplo

```sql
-- Presupuesto de un nivel tal como se lee en la hoja
SELECT * FROM v_presupuesto WHERE capitulo = 'A' AND partida = 1;

-- Cantidad total por concepto en todo el proyecto
SELECT concepto, descripcion, unidad, SUM(cantidad) AS total
FROM v_presupuesto GROUP BY concepto, descripcion, unidad ORDER BY concepto;

-- Catálogo de tuberías PVC
SELECT codigo, diametro, norma, descripcion FROM conceptos
WHERE tipo_elemento = 'Tubería' AND material = 'PVC';
```

## Cómo se agregan los precios después

Cuando se defina ese proceso, basta una tabla nueva que cuelgue del concepto, por ejemplo:

```sql
CREATE TABLE precios_unitarios (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  concepto_id INT NOT NULL,
  fecha       DATE NOT NULL,
  precio      DECIMAL(12,2) NOT NULL,
  fuente      VARCHAR(100) NULL,
  FOREIGN KEY (concepto_id) REFERENCES conceptos(id)
);
```

El subtotal sale entonces de `cantidad * precio` cruzando por `concepto_id`, sin tocar lo ya cargado.

## Correcciones aplicadas a las descripciones

Al pasar de 678 filas a 64 conceptos se normalizó el texto. Cambios hechos:

- Tipeos corregidos: instalaicon, instalacioón, Regitro, Hchura, Parquoe, transpaente,
  Dimeniones, Temperatua, Profunidad, minino.
- Acentos unificados: Tubería, Válvula, Cédula, presión, soportería, señalética, Diámetro.
- Normas corregidas por arrastre: `ASTM D2242` pasa a `ASTM D2241`, `ASTM A-54` pasa a `ASTM A-53`.
- Descripciones que solo diferían por un punto final o espacios dobles se unificaron en un solo concepto.
- La unidad `UNIDAD ` con espacio se unificó con `UNIDAD`.
- La tubería ø4" PVC de aguas lluvias (desde canales hasta Nivel 1) estaba en UNIDAD; se cargó en `ml`
  como el resto de tuberías. Revisar si debía ser otra cosa.
- El equipo de bombas verticales de 40 HP estaba bajo el capítulo D (incendio); en el catálogo se
  clasificó como agua potable (`AP-018`) porque es el sistema hidroneumático doméstico.

Pendientes que conviene revisar en el origen, no se tocaron:

- Las dos bombas trituradoras de aguas negras tienen datos cruzados entre sí
  (2HP, 600 gpm, CDT 1.50 m frente a 3HP, 60 gpm, CDT 20 m).
- La descripción de coladeras dice "niveles Parqueos Nivel 3, 2 y ." y le falta el último nivel.
- En el capítulo D la hoja repite el número 53 en dos niveles; en la base cada partida tiene su
  propio orden y el número original queda en `numero_origen`.

## Regenerar el SQL desde otro Excel

```
pip install openpyxl
python3 generar_sql.py Mi_Presupuesto.xlsx salida.sql
```

El Excel debe tener la misma forma que la hoja `PRES`: letra de capítulo en la columna D,
número de nivel en D, subpartidas con fórmula `=D+0.01`, descripción en E, cantidad en I y unidad en J.
