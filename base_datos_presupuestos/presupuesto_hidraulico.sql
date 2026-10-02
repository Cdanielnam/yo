-- =====================================================================
-- BASE DE DATOS DE PRESUPUESTOS HIDRAULICOS
-- Generado a partir de: Presupuesto_Hidraulico_Opera_Tower_v4.xlsx (hoja PRES)
-- Motor objetivo: MySQL 8 / MariaDB 10 (XAMPP). Importar desde phpMyAdmin o:
--   mysql -u root -p < presupuesto_hidraulico.sql
-- Alcance: estructura del presupuesto, catalogo de conceptos y cantidades.
-- NO incluye precios unitarios (se trabajan en un proceso aparte).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS presupuestos_hidraulicos
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE presupuestos_hidraulicos;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS presupuesto_detalle;
DROP TABLE IF EXISTS partidas;
DROP TABLE IF EXISTS capitulos;
DROP TABLE IF EXISTS proyectos;
DROP TABLE IF EXISTS conceptos;
DROP TABLE IF EXISTS sistemas;
DROP TABLE IF EXISTS unidades;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. CATALOGOS (reutilizables entre proyectos)
-- ---------------------------------------------------------------------
CREATE TABLE unidades (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  codigo    VARCHAR(10)  NOT NULL UNIQUE,   -- ml, UNIDAD, SG
  nombre    VARCHAR(50)  NOT NULL
) ENGINE=InnoDB;

CREATE TABLE sistemas (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  codigo    VARCHAR(5)   NOT NULL UNIQUE,   -- AP, AN, AL, CI
  nombre    VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- Catalogo maestro de conceptos: una fila por descripcion de partida.
-- Las columnas tipo_elemento / material / diametro / norma se derivan de la
-- descripcion para poder filtrar y agrupar; la descripcion es el texto oficial.
CREATE TABLE conceptos (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  codigo         VARCHAR(10)  NOT NULL UNIQUE,  -- ej. AP-001
  sistema_id     INT          NOT NULL,
  unidad_id      INT          NOT NULL,
  descripcion    TEXT         NOT NULL,
  tipo_elemento  VARCHAR(50)  NULL,
  material       VARCHAR(50)  NULL,
  diametro       VARCHAR(15)  NULL,
  norma          VARCHAR(20)  NULL,
  activo         TINYINT(1)   NOT NULL DEFAULT 1,
  CONSTRAINT fk_conceptos_sistema FOREIGN KEY (sistema_id) REFERENCES sistemas(id),
  CONSTRAINT fk_conceptos_unidad  FOREIGN KEY (unidad_id)  REFERENCES unidades(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. ESTRUCTURA DEL PRESUPUESTO (por proyecto)
-- ---------------------------------------------------------------------
CREATE TABLE proyectos (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  nombre       VARCHAR(150) NOT NULL,
  version      VARCHAR(20)  NULL,
  descripcion  VARCHAR(255) NULL,
  creado_en    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Capitulo = letra del presupuesto (A, B, C, D)
CREATE TABLE capitulos (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  proyecto_id  INT          NOT NULL,
  letra        VARCHAR(3)   NOT NULL,
  nombre       VARCHAR(150) NOT NULL,
  sistema_id   INT          NOT NULL,
  CONSTRAINT uq_capitulo UNIQUE (proyecto_id, letra),
  CONSTRAINT fk_capitulos_proyecto FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
  CONSTRAINT fk_capitulos_sistema  FOREIGN KEY (sistema_id)  REFERENCES sistemas(id)
) ENGINE=InnoDB;

-- Partida = nivel o bloque dentro del capitulo (1, 2, 3 ... en la hoja)
CREATE TABLE partidas (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  capitulo_id    INT          NOT NULL,
  orden          INT          NOT NULL,          -- orden dentro del capitulo (1..n)
  numero_origen  INT          NULL,              -- numero tal como aparece en la hoja
  nombre         VARCHAR(150) NOT NULL,
  npt            VARCHAR(30)  NULL,              -- nivel de piso terminado, si aplica
  CONSTRAINT uq_partida UNIQUE (capitulo_id, orden),
  CONSTRAINT fk_partidas_capitulo FOREIGN KEY (capitulo_id) REFERENCES capitulos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Subpartida = concepto del catalogo con su cantidad en una partida.
-- El precio unitario NO vive aqui; cuando se defina ese proceso se agrega una
-- tabla precios_unitarios (concepto_id, fecha, precio, fuente) y se cruza por concepto_id.
CREATE TABLE presupuesto_detalle (
  id           INT            AUTO_INCREMENT PRIMARY KEY,
  partida_id   INT            NOT NULL,
  orden        INT            NOT NULL,          -- .01, .02, ... dentro de la partida
  concepto_id  INT            NOT NULL,
  cantidad     DECIMAL(12,2)  NOT NULL DEFAULT 0,
  observacion  VARCHAR(255)   NULL,
  CONSTRAINT uq_detalle UNIQUE (partida_id, orden),
  CONSTRAINT fk_detalle_partida  FOREIGN KEY (partida_id)  REFERENCES partidas(id) ON DELETE CASCADE,
  CONSTRAINT fk_detalle_concepto FOREIGN KEY (concepto_id) REFERENCES conceptos(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. DATOS: catalogos
-- ---------------------------------------------------------------------
INSERT INTO unidades (codigo, nombre) VALUES
  ('ml', 'Metro lineal'),
  ('UNIDAD', 'Unidad'),
  ('SG', 'Suma global');

INSERT INTO sistemas (codigo, nombre) VALUES
  ('AP', 'Red de agua potable fría y caliente'),
  ('AN', 'Red de aguas negras'),
  ('AL', 'Red de aguas lluvias'),
  ('CI', 'Sistema de combate contra incendio');

-- 64 conceptos distintos (de 678 subpartidas en la hoja)
INSERT INTO conceptos (codigo, sistema_id, unidad_id, descripcion, tipo_elemento, material, diametro, norma) VALUES
  ('AP-001', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Bajada de agua potable Tubería ø1" PVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Bajada de agua potable', 'PVC', '1"', 'ASTM D2241'),
  ('AP-002', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø3/4" PVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '3/4"', 'ASTM D2241'),
  ('AP-003', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1" PVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '1"', 'ASTM D2241'),
  ('AP-004', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Grifos ø1/2" con salida roscada para manguera', 'Grifo', NULL, '1/2"', NULL),
  ('AP-005', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Válvula de Esfera con Palanca inoxidable ø3/4" incluye accesorios', 'Válvula', 'Acero inoxidable', '3/4"', NULL),
  ('AP-006', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Válvula de Esfera con Palanca inoxidable ø1" incluye accesorios', 'Válvula', 'Acero inoxidable', '1"', NULL),
  ('AP-007', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1 1/2" PVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '1 1/2"', 'ASTM D2241'),
  ('AP-008', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Válvula de Esfera con Palanca inoxidable ø1 1/2" incluye accesorios', 'Válvula', 'Acero inoxidable', '1 1/2"', NULL),
  ('AP-009', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Montante Principal tubería 8" PVC Cédula 80 SDR17', 'Montante', 'PVC', '8"', NULL),
  ('AP-010', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Kit de Válvulas de Diámetro 2" incluye Válvulas de Compuerta (2), Válvula Reguladora de Presión (1) y Válvula Check (1), incluye accesorios y soportería', 'Kit de válvulas', NULL, NULL, NULL),
  ('AP-011', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Medidores ø3/4" Plásticos incluye accesorios', 'Medidor', 'Plástico', '3/4"', NULL),
  ('AP-012', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1/2" PVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '1/2"', 'ASTM D2241'),
  ('AP-013', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1/2" CPVC junta cementante SDR 17 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'CPVC', '1/2"', 'ASTM D2241'),
  ('AP-014', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Calentador instantáneo sin tanque, Flujo de 0.50 gpm. Modelo Titán o similar', 'Calentador', NULL, NULL, NULL),
  ('AP-015', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Montante Principal tubería 6" PVC Cédula 80 SDR17', 'Montante', 'PVC', '6"', NULL),
  ('AP-016', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Montante Principal tubería 4" PVC Cédula 80 SDR17', 'Montante', 'PVC', '4"', NULL),
  ('AP-017', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='ml'), 'Montante Principal tubería 3" PVC Cédula 80 SDR17', 'Montante', 'PVC', '3"', NULL),
  ('AP-018', (SELECT id FROM sistemas WHERE codigo='AP'), (SELECT id FROM unidades WHERE codigo='SG'), 'Bombas Verticales en Línea de 40 HP cada una, Presión Constante, Flujo Variado, Succión de 4", Panel de Control Triplex, Válvulas de 3" y 6", Tanque Hidroneumatico de 220 galones, medidor de flujo 6", Línea de Prueba de 6" con retorno a cisterna, base de concreto simple para bombas (Ver detalle de plano dedicado a bombas)', 'Equipo de bombeo agua potable', 'Concreto reforzado', NULL, NULL),
  ('AN-001', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Hechura de Cajas de Registro de Block de 15x20x40cms todas las celdas llena con varilla No.3 - Altura de 0.50 - 1.0m', 'Caja de registro', 'Block', NULL, NULL),
  ('AN-002', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '4"', 'ASTM D2241'),
  ('AN-003', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Hechura de Caja Séptica para almacenaje de aguas residuales. Paredes y losas de concreto reforzado con varilla No.4 @15cms. Espesor de paredes de 15cm. Volumen de 8.0m3', 'Caja séptica', 'Concreto reforzado', NULL, NULL),
  ('AN-004', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de 2 bombas trituradoras para aguas negras tipo sumergibles de Campana con Motor de 3HP CDT de 20m Gasto de 60gpm. Válvulas de Compuerta y Check de Diámetro 2" + tubería de descarga', 'Bomba de aguas negras', NULL, NULL, NULL),
  ('AN-005', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Tapón de Registro al piso de ø4" x 4"', 'Tapón de registro', NULL, '4"', NULL),
  ('AN-006', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø2" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '2"', 'ASTM D2241'),
  ('AN-007', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø6" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '6"', 'ASTM D2241'),
  ('AN-008', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø8" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '8"', 'ASTM D2241'),
  ('AN-009', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Hechura de Caja Séptica para almacenaje de aguas residuales. Paredes y losas de concreto reforzado con varilla No.4 @15cms. Espesor de paredes de 15cm. Volumen de 4.0m3', 'Caja séptica', 'Concreto reforzado', NULL, NULL),
  ('AN-010', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø10" Novafort PVC -U de Pared lisa y pared exterior estructural de anillos paralelos, Union con Espiga - Campana con sello hidraulico con empaque de hule. Color blanca. Cumple ASTM F949', 'Tubería', 'PVC-U Novafort', '10"', 'ASTM F949'),
  ('AN-011', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø12" Novafort PVC -U de Pared lisa y pared exterior estructural de anillos paralelos, Union con Espiga - Campana con sello hidraulico con empaque de hule. Color blanca. Cumple ASTM F949', 'Tubería', 'PVC-U Novafort', '12"', 'ASTM F949'),
  ('AN-012', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø3" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241', 'Tubería', 'PVC', '3"', 'ASTM D2241'),
  ('AN-013', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de 2 bombas trituradoras para aguas negras tipo sumergibles de Campana con Motor de 2HP CDT de 1.50m Gasto de 600gpm. Válvulas de Compuerta y Check de Diámetro 2" + tubería de descarga', 'Bomba de aguas negras', NULL, NULL, NULL),
  ('AN-014', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Drenaje de aguas negras y Tramo de Venteo Vertical en nivel. Cumple ASTM D2241', 'Tubería', 'PVC', '4"', 'ASTM D2241'),
  ('AN-015', (SELECT id FROM sistemas WHERE codigo='AN'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø2" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241. Para Sistema de Venteo Tradicional', 'Tubería', 'PVC', '2"', 'ASTM D2241'),
  ('AL-001', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø6" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241. desde Canales hasta Nivel 1 Parqueo - Amenidades. Cada BALL tiene una altura de 68.85 m (15 BALL)', 'Tubería', 'PVC', '6"', 'ASTM D2241'),
  ('AL-002', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Soportería Vertical para Tubería ø6" PVC Tipo Clavis Hanger o similar de fabricacion nacional', 'Soportería', 'PVC', '6"', NULL),
  ('AL-003', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" PVC junta cementante Clase 125 Cédula 40 incluye accesorios, soportería, señalética. Cumple ASTM D2241. desde Canales hasta Nivel 1 Parqueo - Amenidades. Cada BALL tiene una altura de 68.85 m (15 BALL)', 'Tubería', 'PVC', '4"', 'ASTM D2241'),
  ('AL-004', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Soportería Vertical para Tubería ø4" PVC Tipo Clavis Hanger o similar de fabricacion nacional', 'Soportería', 'PVC', '4"', NULL),
  ('AL-005', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Coladeras para evacuacion de aguas lluvias por azote en niveles Parqueos Nivel 3, 2 y. Marca Helvex Modelo 2514, para desague de ø4" PVC', 'Coladera', 'PVC', '4"', NULL),
  ('AL-006', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Canal para Aguas Lluvias de 25 x 40 cm (Ancho x Altura) con pendiente del 1.0%. Lamina Galvanizada Calibre 24. Soportes con Ganchos de 3/4" a cada 50cms', 'Canal', 'Lámina galvanizada', NULL, NULL),
  ('AL-007', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Canal para Aguas Lluvias de 25 x 30 cm (Ancho x Altura) con pendiente del 1.0%. Lamina Galvanizada Calibre 24. Soportes con Ganchos de 3/4" a cada 50cms', 'Canal', 'Lámina galvanizada', NULL, NULL),
  ('AL-008', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø15" Novafort PVC -U de Pared lisa y pared exterior estructural de anillos paralelos, Union con Espiga - Campana con sello hidraulico con empaque de hule. Color blanca. Cumple ASTM F949', 'Tubería', 'PVC-U Novafort', '15"', 'ASTM F949'),
  ('AL-009', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø18" Novafort PVC -U de Pared lisa y pared exterior estructural de anillos paralelos, Union con Espiga - Campana con sello hidraulico con empaque de hule. Color blanca. Cumple ASTM F949', 'Tubería', 'PVC-U Novafort', '18"', 'ASTM F949'),
  ('AL-010', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Hechura de Sistema de Retención Pluvial de Paredes de concreto reforzado (a diseñar por area de estructuras). Volumen de 80.0m3. Profundidad 3.0m', 'Retención pluvial', 'Concreto reforzado', NULL, NULL),
  ('AL-011', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Pozo de Visita de paredes de ladrillo de obra, base de mamposteria de piedra, tapadera metalica, Peldaños para inspeccion. Profundidad de 1.40 - 4.00m', 'Pozo de visita', 'Ladrillo', NULL, NULL),
  ('AL-012', (SELECT id FROM sistemas WHERE codigo='AL'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Hechura de Cajas de Registro y captacion con tapadera metalica de angulo de 2" x 2" x 3/16" y celosia de varilla No.4 @10cms', 'Caja de registro', NULL, NULL, NULL),
  ('CI-001', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" acero al carbón Cédula 40 que conforma la Bajada desde Nivel 1 Parqueo y Amenidades', 'Tubería', 'Acero al carbón', '4"', NULL),
  ('CI-002', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" acero al carbón Cédula 40 que conforma el Desague Vertical del sistema', 'Tubería', 'Acero al carbón', '4"', NULL),
  ('CI-003', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø2" acero al carbón Cédula 40 proveniente de válvula de descarga de Módulo de Control de Zona', 'Control de zona', 'Acero al carbón', '2"', NULL),
  ('CI-004', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Kit de válvula para regulación de presión para ø4", incluye 2 válvulas de compuerta, 1 válvula reguladora de presión y 1 válvula check, accesorios y soportería horizontal (3 como mínimo)', 'Kit de válvulas', NULL, '4"', NULL),
  ('CI-005', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Control de Zona para Rociadores para ø4" con linea de drenaje para ø2"', 'Control de zona', NULL, '4"', NULL),
  ('CI-006', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de válvula de esfera con palanca de 2" de bronce extremos roscados para drenaje por nivel', 'Válvula', 'Bronce', NULL, NULL),
  ('CI-007', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø4" acero al carbón Cédula 40 Tramo principal de red. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '4"', 'ASTM A-53'),
  ('CI-008', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø3" acero al carbón Cédula 40, pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '3"', 'ASTM A-53'),
  ('CI-009', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø2 1/2" acero al carbón Cédula 40, pintada color rojo Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '2 1/2"', 'ASTM A-53'),
  ('CI-010', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø2" acero al carbón Cédula 40 pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '2"', 'ASTM A-53'),
  ('CI-011', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1" acero al carbón Cédula 40 pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '1"', 'ASTM A-53'),
  ('CI-012', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Gabinete Contra Incendio Tipo I que incluye, Válvula angular de ø1 1/2" x 1 1/2" NST, rack para manguera, manguera de 1/2" x 30m, Pitón de descarga 1 1/2", Extintor de Polvo Químico Seco de 10 lbs, Dimensiones estandar de 77 x 77 x 2 cm, Tipo de Sobreponer, Vidrio transparente templado', 'Válvula', NULL, '1 1/2"', NULL),
  ('CI-013', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Suministro e instalación de Rociadores automáticos conexión directa con reductor 1" x 1/2" factor K5.6. Colocación Tipo Pendent. Temperatura de accionamiento 68°C', 'Rociador', NULL, NULL, NULL),
  ('CI-014', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='UNIDAD'), 'Válvula para conexión de Cuerpo de Bomberos del Tipo Angular 2 1/2" NST con tapadera', 'Conexión de bomberos', NULL, NULL, NULL),
  ('CI-015', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø6" acero al carbón Cédula 40 que conforma la subida de Riser', 'Tubería', 'Acero al carbón', '6"', NULL),
  ('CI-016', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1 1/2" acero al carbón Cédula 40 pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '1 1/2"', 'ASTM A-53'),
  ('CI-017', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø6" acero al carbón Cédula 40 pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '6"', 'ASTM A-53'),
  ('CI-018', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='ml'), 'Suministro e instalación de Tubería ø1 1/4" acero al carbón Cédula 40 pintada color rojo. Incluye accesorios y soportería horizontal, ranurado. ASTM A-53', 'Tubería', 'Acero al carbón', '1 1/4"', 'ASTM A-53'),
  ('CI-019', (SELECT id FROM sistemas WHERE codigo='CI'), (SELECT id FROM unidades WHERE codigo='SG'), 'Bomba estacionaria para incendio conformada por Bomba de Turbina Vertical de Gasto de Diseño 1,000 gpm @185psi, Motor Diesel de 180BHP, Bomba Jockey de 2HP, Gasto de 10 gpm @200 psi, 2 Baterias de 12V, Panel de Control para Motor y Bomba Ppal y Bomba Jockey, Válvula de alivio de aire de 2", Válvula de Alivio de Presión de 4" + Cono Visor de 8"x4", Válvulas Mariposas de 6", Válvula Check de 6", Medidor de Flujo de 6", Manometros de 3" (0 - 300 psi), Cabezal de Prueba de 6" con 4 Válvulas de 2 1/2" roscadas con tapon, Tanque Diesel de 220 galones, tanque de inundacion de 260 galones (Ver detalle de plano dedicado a bombas)', 'Equipo de bombeo contra incendio', NULL, NULL, NULL);

-- ---------------------------------------------------------------------
-- 4. DATOS: proyecto OPERA TOWER
-- ---------------------------------------------------------------------
INSERT INTO proyectos (nombre, version, descripcion) VALUES
  ('OPERA TOWER', 'v4', 'Presupuesto de obras hidráulicas - obras internas a torre de apartamentos');
SET @proy = LAST_INSERT_ID();

-- Capitulo A: RED DE AGUA POTABLE FRIA Y CALIENTE
INSERT INTO capitulos (proyecto_id, letra, nombre, sistema_id) VALUES
  (@proy, 'A', 'RED DE AGUA POTABLE FRIA Y CALIENTE', (SELECT id FROM sistemas WHERE codigo='AP'));
SET @cap_A = LAST_INSERT_ID();
INSERT INTO partidas (capitulo_id, orden, numero_origen, nombre, npt) VALUES
  (@cap_A, 1, 1, 'PARQUEO SOTANO 2', '0-10.50m'),
  (@cap_A, 2, 2, 'PARQUEO SOTANO 1', '0-7.00m'),
  (@cap_A, 3, 3, 'PARQUEO PLANTA BAJA', '0-3.50m'),
  (@cap_A, 4, 4, 'PARQUEO NIVEL 1 PARQUEO AMENIDADES', '0+0.00m'),
  (@cap_A, 5, 5, 'PARQUEO NIVEL 2 PARQUEOS', '0+3.50m'),
  (@cap_A, 6, 6, 'PARQUEO NIVEL 3 PARQUEOS', '0+7.00m'),
  (@cap_A, 7, 7, 'PARQUEO NIVEL 4 PARQUEOS', '0+10.50m'),
  (@cap_A, 8, 8, 'PARQUEO NIVEL 5 Y APARTAMENTOS', '0+14.00m'),
  (@cap_A, 9, 9, 'APARTAMENTOS NIVEL 6', NULL),
  (@cap_A, 10, 10, 'APARTAMENTOS NIVEL 7', NULL),
  (@cap_A, 11, 11, 'APARTAMENTOS NIVEL 8', NULL),
  (@cap_A, 12, 12, 'APARTAMENTOS NIVEL 9', NULL),
  (@cap_A, 13, 13, 'APARTAMENTOS NIVEL 10', NULL),
  (@cap_A, 14, 14, 'APARTAMENTOS NIVEL 11', NULL),
  (@cap_A, 15, 15, 'APARTAMENTOS NIVEL 12', NULL),
  (@cap_A, 16, 16, 'APARTAMENTOS NIVEL 14', NULL),
  (@cap_A, 17, 17, 'APARTAMENTOS NIVEL 15', NULL),
  (@cap_A, 18, 18, 'APARTAMENTOS NIVEL 16', NULL),
  (@cap_A, 19, 19, 'APARTAMENTOS NIVEL 17', NULL),
  (@cap_A, 20, 20, 'APARTAMENTOS NIVEL 18', NULL),
  (@cap_A, 21, 21, 'APARTAMENTOS NIVEL 19', NULL),
  (@cap_A, 22, 22, 'APARTAMENTOS NIVEL 20', NULL),
  (@cap_A, 23, 23, 'APARTAMENTOS NIVEL 21', NULL),
  (@cap_A, 24, 24, 'APARTAMENTOS NIVEL 22', NULL);

-- Capitulo B: RED DE AGUAS NEGRAS
INSERT INTO capitulos (proyecto_id, letra, nombre, sistema_id) VALUES
  (@proy, 'B', 'RED DE AGUAS NEGRAS', (SELECT id FROM sistemas WHERE codigo='AN'));
SET @cap_B = LAST_INSERT_ID();
INSERT INTO partidas (capitulo_id, orden, numero_origen, nombre, npt) VALUES
  (@cap_B, 1, 25, 'PARQUEO SOTANO 2', '0-10.50m'),
  (@cap_B, 2, 26, 'PARQUEO SOTANO 1', '0-7.00m'),
  (@cap_B, 3, 27, 'PARQUEO PLANTA BAJA', '0-3.50m'),
  (@cap_B, 4, 28, 'PARQUEO NIVEL 1 PARQUEO AMENIDADES', '0+0.00m'),
  (@cap_B, 5, 29, 'PARQUEO NIVEL 2 PARQUEOS', '0+3.50m'),
  (@cap_B, 6, 30, 'PARQUEO NIVEL 3 PARQUEOS', '0+7.00m'),
  (@cap_B, 7, 31, 'PARQUEO NIVEL 4 PARQUEOS', '0+10.50m'),
  (@cap_B, 8, 32, 'PARQUEO NIVEL 5 Y APARTAMENTOS', '0+14.00m'),
  (@cap_B, 9, 33, 'APARTAMENTOS NIVEL 6', NULL),
  (@cap_B, 10, 34, 'APARTAMENTOS NIVEL 7', NULL),
  (@cap_B, 11, 35, 'APARTAMENTOS NIVEL 8', NULL),
  (@cap_B, 12, 36, 'APARTAMENTOS NIVEL 9', NULL),
  (@cap_B, 13, 37, 'APARTAMENTOS NIVEL 10', NULL),
  (@cap_B, 14, 38, 'APARTAMENTOS NIVEL 11', NULL),
  (@cap_B, 15, 39, 'APARTAMENTOS NIVEL 12', NULL),
  (@cap_B, 16, 40, 'APARTAMENTOS NIVEL 14', NULL),
  (@cap_B, 17, 41, 'APARTAMENTOS NIVEL 15', NULL),
  (@cap_B, 18, 42, 'APARTAMENTOS NIVEL 16', NULL),
  (@cap_B, 19, 43, 'APARTAMENTOS NIVEL 17', NULL),
  (@cap_B, 20, 44, 'APARTAMENTOS NIVEL 18', NULL),
  (@cap_B, 21, 45, 'APARTAMENTOS NIVEL 19', NULL),
  (@cap_B, 22, 46, 'APARTAMENTOS NIVEL 20', NULL),
  (@cap_B, 23, 47, 'APARTAMENTOS NIVEL 21', NULL),
  (@cap_B, 24, 48, 'APARTAMENTOS NIVEL 22', NULL);

-- Capitulo C: RED DE AGUAS LLUVIAS
INSERT INTO capitulos (proyecto_id, letra, nombre, sistema_id) VALUES
  (@proy, 'C', 'RED DE AGUAS LLUVIAS', (SELECT id FROM sistemas WHERE codigo='AL'));
SET @cap_C = LAST_INSERT_ID();
INSERT INTO partidas (capitulo_id, orden, numero_origen, nombre, npt) VALUES
  (@cap_C, 1, 49, 'SISTEMA DE AGUAS LLUVIAS', NULL);

-- Capitulo D: SISTEMA DE COMBATE CONTRA INCENDIO
INSERT INTO capitulos (proyecto_id, letra, nombre, sistema_id) VALUES
  (@proy, 'D', 'SISTEMA DE COMBATE CONTRA INCENDIO', (SELECT id FROM sistemas WHERE codigo='CI'));
SET @cap_D = LAST_INSERT_ID();
INSERT INTO partidas (capitulo_id, orden, numero_origen, nombre, npt) VALUES
  (@cap_D, 1, 50, 'PARQUEO SOTANO 2', '0-10.50m'),
  (@cap_D, 2, 51, 'PARQUEO SOTANO 1', '0-7.00m'),
  (@cap_D, 3, 52, 'PARQUEO PLANTA BAJA', '0-3.50m'),
  (@cap_D, 4, 53, 'PARQUEO NIVEL 1 PARQUEO AMENIDADES', '0+0.00m'),
  (@cap_D, 5, 53, 'PARQUEO NIVEL 2 PARQUEOS', '0+3.50m'),
  (@cap_D, 6, 54, 'PARQUEO NIVEL 3 PARQUEOS', '0+7.00m'),
  (@cap_D, 7, 55, 'PARQUEO NIVEL 4 PARQUEOS', '0+10.50m'),
  (@cap_D, 8, 56, 'PARQUEO NIVEL 5 Y APARTAMENTOS', '0+14.00m'),
  (@cap_D, 9, 57, 'APARTAMENTOS NIVEL 6', NULL),
  (@cap_D, 10, 58, 'APARTAMENTOS NIVEL 7', NULL),
  (@cap_D, 11, 59, 'APARTAMENTOS NIVEL 8', NULL),
  (@cap_D, 12, 60, 'APARTAMENTOS NIVEL 9', NULL),
  (@cap_D, 13, 61, 'APARTAMENTOS NIVEL 10', NULL),
  (@cap_D, 14, 62, 'APARTAMENTOS NIVEL 11', NULL),
  (@cap_D, 15, 63, 'APARTAMENTOS NIVEL 12', NULL),
  (@cap_D, 16, 64, 'APARTAMENTOS NIVEL 14', NULL),
  (@cap_D, 17, 65, 'APARTAMENTOS NIVEL 15', NULL),
  (@cap_D, 18, 66, 'APARTAMENTOS NIVEL 16', NULL),
  (@cap_D, 19, 67, 'APARTAMENTOS NIVEL 17', NULL),
  (@cap_D, 20, 68, 'APARTAMENTOS NIVEL 18', NULL),
  (@cap_D, 21, 69, 'APARTAMENTOS NIVEL 19', NULL),
  (@cap_D, 22, 70, 'APARTAMENTOS NIVEL 20', NULL),
  (@cap_D, 23, 71, 'APARTAMENTOS NIVEL 21', NULL),
  (@cap_D, 24, 72, 'APARTAMENTOS NIVEL 22', NULL),
  (@cap_D, 25, 73, 'EQUIPOS DE BOMBAS', NULL);

-- Subpartidas (cantidad por concepto y partida)
-- A.1 PARQUEO SOTANO 2 (NPT = 0 - 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=1), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00);
-- A.2 PARQUEO SOTANO 1 (NPT = 0 - 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=2), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00);
-- A.3 PARQUEO PLANTA BAJA (NPT = 0 -3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=3), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00);
-- A.4 PARQUEO NIVEL 1 PARQUEO AMENIDADES (NPT = 0+0.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 259.74),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 43.30),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 4, (SELECT id FROM conceptos WHERE codigo='AP-007'), 33.03),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 5, (SELECT id FROM conceptos WHERE codigo='AP-004'), 13.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 6, (SELECT id FROM conceptos WHERE codigo='AP-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 7, (SELECT id FROM conceptos WHERE codigo='AP-006'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 8, (SELECT id FROM conceptos WHERE codigo='AP-008'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=4), 9, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.50);
-- A.5 PARQUEO NIVEL 2 PARQUEOS (NPT = 0 + 3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=5), 7, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.50);
-- A.6 PARQUEO NIVEL 3 PARQUEOS (NPT = 0 + 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=6), 7, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.50);
-- A.7 PARQUEO NIVEL 4 PARQUEOS (NPT = 0 + 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 2, (SELECT id FROM conceptos WHERE codigo='AP-002'), 67.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 3, (SELECT id FROM conceptos WHERE codigo='AP-003'), 52.52),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 4, (SELECT id FROM conceptos WHERE codigo='AP-004'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 5, (SELECT id FROM conceptos WHERE codigo='AP-005'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 6, (SELECT id FROM conceptos WHERE codigo='AP-006'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=7), 7, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.50);
-- A.8 PARQUEO NIVEL 5 Y APARTAMENTOS (NPT = 0 + 14.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 8.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 8.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 240.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 373.29),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 265.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 8.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 9, (SELECT id FROM conceptos WHERE codigo='AP-003'), 26.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 10, (SELECT id FROM conceptos WHERE codigo='AP-004'), 3.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 11, (SELECT id FROM conceptos WHERE codigo='AP-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=8), 12, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.50);
-- A.9 APARTAMENTOS NIVEL 6
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=9), 9, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.20);
-- A.10 APARTAMENTOS NIVEL 7
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=10), 9, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.20);
-- A.11 APARTAMENTOS NIVEL 8
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=11), 9, (SELECT id FROM conceptos WHERE codigo='AP-009'), 3.20);
-- A.12 APARTAMENTOS NIVEL 9
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=12), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.13 APARTAMENTOS NIVEL 10
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=13), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.14 APARTAMENTOS NIVEL 11
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=14), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.15 APARTAMENTOS NIVEL 12
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=15), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.16 APARTAMENTOS NIVEL 14
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=16), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.17 APARTAMENTOS NIVEL 15
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=17), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.18 APARTAMENTOS NIVEL 16
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=18), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.19 APARTAMENTOS NIVEL 17
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=19), 9, (SELECT id FROM conceptos WHERE codigo='AP-015'), 3.20);
-- A.20 APARTAMENTOS NIVEL 18
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=20), 9, (SELECT id FROM conceptos WHERE codigo='AP-016'), 3.20);
-- A.21 APARTAMENTOS NIVEL 19
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=21), 9, (SELECT id FROM conceptos WHERE codigo='AP-016'), 3.20);
-- A.22 APARTAMENTOS NIVEL 20
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=22), 9, (SELECT id FROM conceptos WHERE codigo='AP-017'), 3.20);
-- A.23 APARTAMENTOS NIVEL 21
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=23), 9, (SELECT id FROM conceptos WHERE codigo='AP-017'), 3.20);
-- A.24 APARTAMENTOS NIVEL 22
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 1, (SELECT id FROM conceptos WHERE codigo='AP-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 2, (SELECT id FROM conceptos WHERE codigo='AP-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 3, (SELECT id FROM conceptos WHERE codigo='AP-011'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 4, (SELECT id FROM conceptos WHERE codigo='AP-005'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 5, (SELECT id FROM conceptos WHERE codigo='AP-012'), 450.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 6, (SELECT id FROM conceptos WHERE codigo='AP-002'), 632.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 7, (SELECT id FROM conceptos WHERE codigo='AP-013'), 497.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 8, (SELECT id FROM conceptos WHERE codigo='AP-014'), 15.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_A AND orden=24), 9, (SELECT id FROM conceptos WHERE codigo='AP-017'), 3.20);
-- B.1 PARQUEO SOTANO 2 (NPT = 0 - 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=1), 1, (SELECT id FROM conceptos WHERE codigo='AN-001'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=1), 2, (SELECT id FROM conceptos WHERE codigo='AN-002'), 100.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=1), 3, (SELECT id FROM conceptos WHERE codigo='AN-003'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=1), 4, (SELECT id FROM conceptos WHERE codigo='AN-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=1), 5, (SELECT id FROM conceptos WHERE codigo='AN-005'), 4.00);
-- B.2 PARQUEO SOTANO 1 (NPT = 0 - 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=2), 1, (SELECT id FROM conceptos WHERE codigo='AN-002'), 29.90),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=2), 2, (SELECT id FROM conceptos WHERE codigo='AN-005'), 3.00);
-- B.3 PARQUEO PLANTA BAJA (NPT = 0 -3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=3), 1, (SELECT id FROM conceptos WHERE codigo='AN-002'), 29.90),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=3), 2, (SELECT id FROM conceptos WHERE codigo='AN-005'), 3.00);
-- B.4 PARQUEO NIVEL 1 PARQUEO AMENIDADES (NPT = 0+0.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 23.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 2, (SELECT id FROM conceptos WHERE codigo='AN-002'), 64.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 3, (SELECT id FROM conceptos WHERE codigo='AN-007'), 63.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 4, (SELECT id FROM conceptos WHERE codigo='AN-008'), 82.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 5, (SELECT id FROM conceptos WHERE codigo='AN-009'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 6, (SELECT id FROM conceptos WHERE codigo='AN-010'), 17.70),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 7, (SELECT id FROM conceptos WHERE codigo='AN-011'), 33.30),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 8, (SELECT id FROM conceptos WHERE codigo='AN-001'), 8.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 9, (SELECT id FROM conceptos WHERE codigo='AN-012'), 38.30),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=4), 10, (SELECT id FROM conceptos WHERE codigo='AN-013'), 1.00);
-- B.5 PARQUEO NIVEL 2 PARQUEOS (NPT = 0 + 3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=5), 1, (SELECT id FROM conceptos WHERE codigo='AN-002'), 50.90),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=5), 2, (SELECT id FROM conceptos WHERE codigo='AN-005'), 3.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=5), 3, (SELECT id FROM conceptos WHERE codigo='AN-007'), 42.00);
-- B.6 PARQUEO NIVEL 3 PARQUEOS (NPT = 0 + 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=6), 1, (SELECT id FROM conceptos WHERE codigo='AN-002'), 50.90),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=6), 2, (SELECT id FROM conceptos WHERE codigo='AN-005'), 3.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=6), 3, (SELECT id FROM conceptos WHERE codigo='AN-007'), 42.00);
-- B.7 PARQUEO NIVEL 4 PARQUEOS (NPT = 0 + 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=7), 1, (SELECT id FROM conceptos WHERE codigo='AN-002'), 153.70),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=7), 2, (SELECT id FROM conceptos WHERE codigo='AN-005'), 4.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=7), 3, (SELECT id FROM conceptos WHERE codigo='AN-007'), 17.50);
-- B.8 PARQUEO NIVEL 5 Y APARTAMENTOS (NPT = 0 + 14.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=8), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 102.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=8), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 147.70),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=8), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 50.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=8), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 81.60),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=8), 5, (SELECT id FROM conceptos WHERE codigo='AN-007'), 0.00);
-- B.9 APARTAMENTOS NIVEL 6
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=9), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=9), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 186.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=9), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=9), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=9), 5, (SELECT id FROM conceptos WHERE codigo='AN-007'), 0.00);
-- B.10 APARTAMENTOS NIVEL 7
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=10), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=10), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 186.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=10), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=10), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=10), 5, (SELECT id FROM conceptos WHERE codigo='AN-007'), 0.00);
-- B.11 APARTAMENTOS NIVEL 8
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=11), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=11), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=11), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=11), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.12 APARTAMENTOS NIVEL 9
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=12), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=12), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=12), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=12), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.13 APARTAMENTOS NIVEL 10
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=13), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=13), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=13), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=13), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.14 APARTAMENTOS NIVEL 11
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=14), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=14), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=14), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=14), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.15 APARTAMENTOS NIVEL 12
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=15), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=15), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=15), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=15), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.16 APARTAMENTOS NIVEL 14
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=16), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=16), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=16), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=16), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.17 APARTAMENTOS NIVEL 15
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=17), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=17), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=17), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=17), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.18 APARTAMENTOS NIVEL 16
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=18), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=18), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=18), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=18), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.19 APARTAMENTOS NIVEL 17
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=19), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=19), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=19), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=19), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.20 APARTAMENTOS NIVEL 18
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=20), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=20), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=20), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=20), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.21 APARTAMENTOS NIVEL 19
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=21), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=21), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=21), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=21), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.22 APARTAMENTOS NIVEL 20
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=22), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=22), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=22), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=22), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.23 APARTAMENTOS NIVEL 21
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=23), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=23), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=23), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=23), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- B.24 APARTAMENTOS NIVEL 22
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=24), 1, (SELECT id FROM conceptos WHERE codigo='AN-006'), 92.35),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=24), 2, (SELECT id FROM conceptos WHERE codigo='AN-014'), 234.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=24), 3, (SELECT id FROM conceptos WHERE codigo='AN-005'), 90.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_B AND orden=24), 4, (SELECT id FROM conceptos WHERE codigo='AN-015'), 153.00);
-- C.1 SISTEMA DE AGUAS LLUVIAS
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 1, (SELECT id FROM conceptos WHERE codigo='AL-001'), 1032.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 2, (SELECT id FROM conceptos WHERE codigo='AL-002'), 345.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 3, (SELECT id FROM conceptos WHERE codigo='AL-003'), 360.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 4, (SELECT id FROM conceptos WHERE codigo='AL-004'), 120.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 5, (SELECT id FROM conceptos WHERE codigo='AL-005'), 82.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 6, (SELECT id FROM conceptos WHERE codigo='AL-006'), 122.60),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 7, (SELECT id FROM conceptos WHERE codigo='AL-007'), 131.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 8, (SELECT id FROM conceptos WHERE codigo='AN-002'), 11.30),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 9, (SELECT id FROM conceptos WHERE codigo='AN-007'), 34.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 10, (SELECT id FROM conceptos WHERE codigo='AN-010'), 47.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 11, (SELECT id FROM conceptos WHERE codigo='AN-011'), 31.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 12, (SELECT id FROM conceptos WHERE codigo='AL-008'), 38.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 13, (SELECT id FROM conceptos WHERE codigo='AL-009'), 39.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 14, (SELECT id FROM conceptos WHERE codigo='AL-010'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 15, (SELECT id FROM conceptos WHERE codigo='AL-011'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_C AND orden=1), 16, (SELECT id FROM conceptos WHERE codigo='AL-012'), 20.00);
-- D.1 PARQUEO SOTANO 2 (NPT = 0 - 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 1, (SELECT id FROM conceptos WHERE codigo='CI-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 11, (SELECT id FROM conceptos WHERE codigo='CI-011'), 275.60),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 12, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 13, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=1), 14, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.2 PARQUEO SOTANO 1 (NPT = 0 - 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 1, (SELECT id FROM conceptos WHERE codigo='CI-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 11, (SELECT id FROM conceptos WHERE codigo='CI-011'), 264.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 12, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 13, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=2), 14, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.3 PARQUEO PLANTA BAJA (NPT = 0 -3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 1, (SELECT id FROM conceptos WHERE codigo='CI-001'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 11, (SELECT id FROM conceptos WHERE codigo='CI-011'), 264.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 12, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 13, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=3), 14, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.4 PARQUEO NIVEL 1 PARQUEO AMENIDADES (NPT = 0+0.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 15.70),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 39.84),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 11, (SELECT id FROM conceptos WHERE codigo='CI-011'), 256.85),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 12, (SELECT id FROM conceptos WHERE codigo='CI-016'), 8.27),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 13, (SELECT id FROM conceptos WHERE codigo='CI-017'), 11.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 14, (SELECT id FROM conceptos WHERE codigo='CI-012'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 15, (SELECT id FROM conceptos WHERE codigo='CI-013'), 54.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=4), 16, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.5 PARQUEO NIVEL 2 PARQUEOS (NPT = 0 + 3.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 11, (SELECT id FROM conceptos WHERE codigo='CI-011'), 264.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 12, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 13, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=5), 14, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.6 PARQUEO NIVEL 3 PARQUEOS (NPT = 0 + 7.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 264.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=6), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.7 PARQUEO NIVEL 4 PARQUEOS (NPT = 0 + 10.50m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 12.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 16.42),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 28.82),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 25.10),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 0.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 264.40),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 58.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=7), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.8 PARQUEO NIVEL 5 Y APARTAMENTOS (NPT = 0 + 14.00m)
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 34.30),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 27.51),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 43.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 180.83),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 50.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=8), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.9 APARTAMENTOS NIVEL 6
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=9), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.10 APARTAMENTOS NIVEL 7
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=10), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.11 APARTAMENTOS NIVEL 8
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=11), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.12 APARTAMENTOS NIVEL 9
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=12), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.13 APARTAMENTOS NIVEL 10
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=13), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.14 APARTAMENTOS NIVEL 11
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=14), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.15 APARTAMENTOS NIVEL 12
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=15), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.16 APARTAMENTOS NIVEL 14
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=16), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.17 APARTAMENTOS NIVEL 15
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=17), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.18 APARTAMENTOS NIVEL 16
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=18), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.19 APARTAMENTOS NIVEL 17
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=19), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.20 APARTAMENTOS NIVEL 18
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=20), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.21 APARTAMENTOS NIVEL 19
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=21), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.22 APARTAMENTOS NIVEL 20
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=22), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.23 APARTAMENTOS NIVEL 21
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=23), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.24 APARTAMENTOS NIVEL 22
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 1, (SELECT id FROM conceptos WHERE codigo='CI-015'), 3.20),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 2, (SELECT id FROM conceptos WHERE codigo='CI-002'), 3.50),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 3, (SELECT id FROM conceptos WHERE codigo='CI-003'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 4, (SELECT id FROM conceptos WHERE codigo='CI-004'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 5, (SELECT id FROM conceptos WHERE codigo='CI-005'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 6, (SELECT id FROM conceptos WHERE codigo='CI-006'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 7, (SELECT id FROM conceptos WHERE codigo='CI-007'), 14.25),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 8, (SELECT id FROM conceptos WHERE codigo='CI-008'), 6.75),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 9, (SELECT id FROM conceptos WHERE codigo='CI-009'), 32.05),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 10, (SELECT id FROM conceptos WHERE codigo='CI-010'), 21.91),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 11, (SELECT id FROM conceptos WHERE codigo='CI-018'), 46.45),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 12, (SELECT id FROM conceptos WHERE codigo='CI-011'), 181.65),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 13, (SELECT id FROM conceptos WHERE codigo='CI-012'), 2.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 14, (SELECT id FROM conceptos WHERE codigo='CI-013'), 47.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=24), 15, (SELECT id FROM conceptos WHERE codigo='CI-014'), 1.00);
-- D.25 EQUIPOS DE BOMBAS
INSERT INTO presupuesto_detalle (partida_id, orden, concepto_id, cantidad) VALUES
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=25), 1, (SELECT id FROM conceptos WHERE codigo='AP-018'), 1.00),
  ((SELECT id FROM partidas WHERE capitulo_id=@cap_D AND orden=25), 2, (SELECT id FROM conceptos WHERE codigo='CI-019'), 1.00);

-- ---------------------------------------------------------------------
-- 5. VISTA DE CONSULTA: presupuesto desglosado tal como se lee en la hoja
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_presupuesto AS
SELECT
  pr.nombre                                   AS proyecto,
  ca.letra                                    AS capitulo,
  ca.nombre                                   AS capitulo_nombre,
  pa.orden                                    AS partida,
  pa.nombre                                   AS partida_nombre,
  pa.npt,
  CONCAT(pa.orden, '.', LPAD(de.orden, 2, '0')) AS subpartida,
  co.codigo                                   AS concepto,
  co.descripcion,
  un.codigo                                   AS unidad,
  de.cantidad
FROM presupuesto_detalle de
JOIN partidas  pa ON pa.id = de.partida_id
JOIN capitulos ca ON ca.id = pa.capitulo_id
JOIN proyectos pr ON pr.id = ca.proyecto_id
JOIN conceptos co ON co.id = de.concepto_id
JOIN unidades  un ON un.id = co.unidad_id;

-- Ejemplos de consulta:
-- SELECT * FROM v_presupuesto WHERE capitulo = 'A' AND partida = 1;
-- SELECT concepto, descripcion, unidad, SUM(cantidad) total FROM v_presupuesto GROUP BY concepto, descripcion, unidad ORDER BY concepto;
-- SELECT * FROM conceptos WHERE tipo_elemento = 'Tubería' AND material = 'PVC';
