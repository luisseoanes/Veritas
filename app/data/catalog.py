"""Catalogo semilla del dominio WEG (accionamientos industriales).

IMPORTANTE — honestidad de datos:
Estos componentes son REPRESENTATIVOS, construidos a partir de las lineas y los
rangos publicos de WEG (motores W22 y W22 Washdown, variadores CFW100/300/500/
501/700/11, guardamotores MPW, contactores CWB, conductores). NO son un volcado
del catalogo oficial ni una lista de precios real. Se reemplazan por los datos
reales de WEG cargando el mismo formato.

Lo que NUNCA es representativo es la logica: reglas de compatibilidad, solver,
nucleo insatisfacible y frontera de Pareto operan sobre estos datos exactamente
igual que sobre los reales. Los datos son semilla; el motor es real.

Corriente nominal aproximada segun  I = P / (sqrt(3) * V * fp * eta), con
fp = 0.85. A 220 V eso da ~3.5 A/kW y a 440 V ~1.7 A/kW.

TRES DECISIONES DE DATOS, DECLARADAS:

1. COBERTURA IP66. La linea Washdown (lavado a presion, industria de alimentos)
   cubre 220 V y 440 V en potencias bajas y medias, en motor y en variador.
   Antes un SOLO componente de todo el catalogo ofrecia IP66 —un variador de
   45 kW— asi que cualquier cliente con lavado a presion caia en SIN_SOLUCION
   por falta de catalogo, no por una restriccion real de ingenieria.
   Se deja a proposito un HUECO: no hay IP66 por encima de 15 kW. Un cliente de
   22 kW en zona de lavado sigue siendo una brecha de producto legitima, y es
   la que alimenta el detector de demanda no satisfecha.

2. STOCK REALISTA, INCLUIDO EL CERO. Antes todo el catalogo tenia stock >= 2,
   asi que la restriccion de disponibilidad no filtraba NADA nunca: era una
   trampa latente para cuando entraran datos reales. Ahora hay referencias
   agotadas (stock=0) y en minimos (stock=1), asi que la disponibilidad puede
   aparecer en un nucleo insatisfacible — que es justo el caso de negocio
   interesante: el producto existe, lo que falta es reponerlo.

3. ESCALERA DE 220 V CONSERVADA. Los variadores de 220 V mantienen los mismos
   escalones que antes (4 -> 7.5 -> 11 -> 15 kW) y el motor MOT-W22-5-220 no
   cambia de precio. Es deliberado: sostiene el escenario de demo ya ensayado.
   La expansion ocurre alrededor, no encima.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.graph.schema import Component, Kind

# ---------------------------------------------------------------- MOTORES ---
# Trifasicos de induccion. `tags` marca la familia comercial: los objetivos de
# negocio del tipo "impulsar linea X" operan sobre estas etiquetas.
# La linea Washdown declara la caracteristica "ip66".

MOTORS = [
    # --- W22 IE3 estandar, 220 V ---
    Component("MOT-W22-075-220", Kind.MOTOR, "Motor W22 0.75 kW 220V IE3",
              price_cop=980_000, margin_pct=0.24, stock=22,
              attrs={"power_kw": 0.75, "voltage": 220, "current_a": 2.6,
                     "rpm": 1750, "efficiency_pct": 84.0, "frame": "80",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-15-220-B", Kind.MOTOR, "Motor W22 1.5 kW 220V IE3",
              price_cop=1_320_000, margin_pct=0.24, stock=19,
              attrs={"power_kw": 1.5, "voltage": 220, "current_a": 5.2,
                     "rpm": 1750, "efficiency_pct": 86.5, "frame": "90S",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-22-220", Kind.MOTOR, "Motor W22 2.2 kW 220V IE3",
              price_cop=1_690_000, margin_pct=0.23, stock=16,
              attrs={"power_kw": 2.2, "voltage": 220, "current_a": 7.6,
                     "rpm": 1750, "efficiency_pct": 87.8, "frame": "90L",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-3-220", Kind.MOTOR, "Motor W22 3 kW 220V IE3",
              price_cop=2_150_000, margin_pct=0.22, stock=14,
              attrs={"power_kw": 3.0, "voltage": 220, "current_a": 11.0,
                     "rpm": 1750, "efficiency_pct": 89.5, "frame": "100L",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-5-220", Kind.MOTOR, "Motor W22 5.5 kW 220V IE3",
              price_cop=3_050_000, margin_pct=0.22, stock=9,
              attrs={"power_kw": 5.5, "voltage": 220, "current_a": 20.0,
                     "rpm": 1750, "efficiency_pct": 90.2, "frame": "112M",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-7-220", Kind.MOTOR, "Motor W22 7.5 kW 220V IE3",
              price_cop=4_100_000, margin_pct=0.21, stock=6,
              attrs={"power_kw": 7.5, "voltage": 220, "current_a": 27.0,
                     "rpm": 1750, "efficiency_pct": 91.0, "frame": "132S",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-11-220", Kind.MOTOR, "Motor W22 11 kW 220V IE3",
              price_cop=5_600_000, margin_pct=0.20, stock=4,
              attrs={"power_kw": 11.0, "voltage": 220, "current_a": 39.0,
                     "rpm": 1750, "efficiency_pct": 91.4, "frame": "160M",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-15-220", Kind.MOTOR, "Motor W22 15 kW 220V IE3",
              price_cop=7_200_000, margin_pct=0.19, stock=2,
              attrs={"power_kw": 15.0, "voltage": 220, "current_a": 52.0,
                     "rpm": 1750, "efficiency_pct": 92.1, "frame": "160L",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-18-220", Kind.MOTOR, "Motor W22 18.5 kW 220V IE3",
              price_cop=8_900_000, margin_pct=0.19, stock=0,   # agotado
              attrs={"power_kw": 18.5, "voltage": 220, "current_a": 64.0,
                     "rpm": 1750, "efficiency_pct": 92.4, "frame": "180M",
                     "tags": ["w22", "ie3"]}),

    # --- W22 IE3 estandar, 440 V ---
    Component("MOT-W22-3-440", Kind.MOTOR, "Motor W22 3 kW 440V IE3",
              price_cop=2_090_000, margin_pct=0.23, stock=17,
              attrs={"power_kw": 3.0, "voltage": 440, "current_a": 5.1,
                     "rpm": 1750, "efficiency_pct": 89.6, "frame": "100L",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-5-440", Kind.MOTOR, "Motor W22 5.5 kW 440V IE3",
              price_cop=2_980_000, margin_pct=0.23, stock=13,
              attrs={"power_kw": 5.5, "voltage": 440, "current_a": 9.4,
                     "rpm": 1750, "efficiency_pct": 90.4, "frame": "112M",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-7-440", Kind.MOTOR, "Motor W22 7.5 kW 440V IE3",
              price_cop=3_980_000, margin_pct=0.23, stock=11,
              attrs={"power_kw": 7.5, "voltage": 440, "current_a": 13.5,
                     "rpm": 1750, "efficiency_pct": 91.2, "frame": "132S",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-11-440", Kind.MOTOR, "Motor W22 11 kW 440V IE3",
              price_cop=5_350_000, margin_pct=0.22, stock=8,
              attrs={"power_kw": 11.0, "voltage": 440, "current_a": 18.9,
                     "rpm": 1750, "efficiency_pct": 91.6, "frame": "160M",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-15-440", Kind.MOTOR, "Motor W22 15 kW 440V IE3",
              price_cop=6_900_000, margin_pct=0.21, stock=7,
              attrs={"power_kw": 15.0, "voltage": 440, "current_a": 26.0,
                     "rpm": 1750, "efficiency_pct": 92.4, "frame": "160L",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-18-440", Kind.MOTOR, "Motor W22 18.5 kW 440V IE3",
              price_cop=8_150_000, margin_pct=0.21, stock=5,
              attrs={"power_kw": 18.5, "voltage": 440, "current_a": 31.7,
                     "rpm": 1750, "efficiency_pct": 92.8, "frame": "180M",
                     "tags": ["w22", "ie3"]}),

    # --- W22 IE4 premium, 440 V ---
    Component("MOT-W22-22-440", Kind.MOTOR, "Motor W22 22 kW 440V IE4",
              price_cop=9_400_000, margin_pct=0.24, stock=5,
              attrs={"power_kw": 22.0, "voltage": 440, "current_a": 38.0,
                     "rpm": 1750, "efficiency_pct": 93.6, "frame": "180M",
                     "tags": ["w22", "ie4", "premium"]}),
    Component("MOT-W22-30-440", Kind.MOTOR, "Motor W22 30 kW 440V IE4",
              price_cop=12_800_000, margin_pct=0.24, stock=3,
              attrs={"power_kw": 30.0, "voltage": 440, "current_a": 52.0,
                     "rpm": 1750, "efficiency_pct": 94.0, "frame": "200L",
                     "tags": ["w22", "ie4", "premium"]}),
    Component("MOT-W22-37-440", Kind.MOTOR, "Motor W22 37 kW 440V IE4",
              price_cop=15_400_000, margin_pct=0.23, stock=2,
              attrs={"power_kw": 37.0, "voltage": 440, "current_a": 63.5,
                     "rpm": 1750, "efficiency_pct": 94.3, "frame": "225S",
                     "tags": ["w22", "ie4", "premium"]}),
    Component("MOT-W22-45-440", Kind.MOTOR, "Motor W22 45 kW 440V IE4",
              price_cop=18_600_000, margin_pct=0.23, stock=1,   # ultima unidad
              attrs={"power_kw": 45.0, "voltage": 440, "current_a": 77.2,
                     "rpm": 1750, "efficiency_pct": 94.6, "frame": "225M",
                     "tags": ["w22", "ie4", "premium"]}),

    # --- W22 Washdown IP66 (lavado a presion / alimentos) ---
    # Sobreprecio ~40% frente al equivalente estandar: pintura epoxica, sellos
    # reforzados y ejecucion sanitaria.
    Component("MOT-W22W-15-220", Kind.MOTOR, "Motor W22 Washdown 1.5 kW 220V IP66",
              price_cop=1_890_000, margin_pct=0.28, stock=10,
              attrs={"power_kw": 1.5, "voltage": 220, "current_a": 5.2,
                     "rpm": 1750, "efficiency_pct": 86.0, "frame": "90S",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-3-220", Kind.MOTOR, "Motor W22 Washdown 3 kW 220V IP66",
              price_cop=3_020_000, margin_pct=0.28, stock=8,
              attrs={"power_kw": 3.0, "voltage": 220, "current_a": 11.0,
                     "rpm": 1750, "efficiency_pct": 89.0, "frame": "100L",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-5-220", Kind.MOTOR, "Motor W22 Washdown 5.5 kW 220V IP66",
              price_cop=4_280_000, margin_pct=0.27, stock=6,
              attrs={"power_kw": 5.5, "voltage": 220, "current_a": 20.0,
                     "rpm": 1750, "efficiency_pct": 89.8, "frame": "112M",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-7-220", Kind.MOTOR, "Motor W22 Washdown 7.5 kW 220V IP66",
              price_cop=5_740_000, margin_pct=0.27, stock=3,
              attrs={"power_kw": 7.5, "voltage": 220, "current_a": 27.0,
                     "rpm": 1750, "efficiency_pct": 90.6, "frame": "132S",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-7-440", Kind.MOTOR, "Motor W22 Washdown 7.5 kW 440V IP66",
              price_cop=5_570_000, margin_pct=0.28, stock=7,
              attrs={"power_kw": 7.5, "voltage": 440, "current_a": 13.5,
                     "rpm": 1750, "efficiency_pct": 90.8, "frame": "132S",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-11-440", Kind.MOTOR, "Motor W22 Washdown 11 kW 440V IP66",
              price_cop=7_490_000, margin_pct=0.27, stock=4,
              attrs={"power_kw": 11.0, "voltage": 440, "current_a": 18.9,
                     "rpm": 1750, "efficiency_pct": 91.2, "frame": "160M",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    Component("MOT-W22W-15-440", Kind.MOTOR, "Motor W22 Washdown 15 kW 440V IP66",
              price_cop=9_660_000, margin_pct=0.26, stock=2,
              attrs={"power_kw": 15.0, "voltage": 440, "current_a": 26.0,
                     "rpm": 1750, "efficiency_pct": 92.0, "frame": "160L",
                     "features": ["ip66"],
                     "tags": ["w22", "washdown", "ip66"]}),
    # NOTA: por encima de 15 kW no hay IP66. Hueco DELIBERADO — es el que
    # alimenta el detector de brecha de producto.
]

# -------------------------------------------------------------- VARIADORES ---
# `features` alimenta los FeatureRequirement del cliente (arranque suave,
# comunicacion, grado de proteccion).

DRIVES = [
    # --- CFW100 / CFW300: compactos, potencias bajas ---
    Component("DRV-CFW100-1-220", Kind.DRIVE, "Variador CFW100 1.5 kW 220V",
              price_cop=790_000, margin_pct=0.30, stock=24,
              attrs={"power_kw_max": 1.5, "current_a": 7.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start"],
                     "tags": ["cfw100", "compacto"]}),
    Component("DRV-CFW300-2-220", Kind.DRIVE, "Variador CFW300 2.2 kW 220V",
              price_cop=1_080_000, margin_pct=0.29, stock=21,
              attrs={"power_kw_max": 2.2, "current_a": 9.6,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid"],
                     "tags": ["cfw300", "compacto"]}),
    Component("DRV-CFW300-4-220", Kind.DRIVE, "Variador CFW300 4 kW 220V",
              price_cop=1_620_000, margin_pct=0.28, stock=18,
              attrs={"power_kw_max": 4.0, "current_a": 16.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid"],
                     "tags": ["cfw300", "compacto"]}),

    # --- CFW500: proposito general ---
    Component("DRV-CFW500-7-220", Kind.DRIVE, "Variador CFW500 7.5 kW 220V",
              price_cop=2_400_000, margin_pct=0.30, stock=12,
              attrs={"power_kw_max": 7.5, "current_a": 24.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
    Component("DRV-CFW500-11-220", Kind.DRIVE, "Variador CFW500 11 kW 220V",
              price_cop=3_300_000, margin_pct=0.29, stock=8,
              attrs={"power_kw_max": 11.0, "current_a": 33.6,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
    Component("DRV-CFW500-15-220", Kind.DRIVE, "Variador CFW500 15 kW 220V",
              price_cop=4_500_000, margin_pct=0.27, stock=3,
              attrs={"power_kw_max": 15.0, "current_a": 66.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
    Component("DRV-CFW500-5-440", Kind.DRIVE, "Variador CFW500 5.5 kW 440V",
              price_cop=1_980_000, margin_pct=0.31, stock=20,
              attrs={"power_kw_max": 5.5, "current_a": 10.5,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
    Component("DRV-CFW500-11-440", Kind.DRIVE, "Variador CFW500 11 kW 440V",
              price_cop=3_150_000, margin_pct=0.31, stock=15,
              attrs={"power_kw_max": 11.0, "current_a": 17.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
    Component("DRV-CFW500-15-440", Kind.DRIVE, "Variador CFW500 15 kW 440V",
              price_cop=3_980_000, margin_pct=0.30, stock=10,
              attrs={"power_kw_max": 15.0, "current_a": 24.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),

    # --- CFW501: ejecucion sanitaria IP66 para zonas de lavado ---
    Component("DRV-CFW501-5-220", Kind.DRIVE, "Variador CFW501 5.5 kW 220V IP66",
              price_cop=3_460_000, margin_pct=0.33, stock=6,
              attrs={"power_kw_max": 5.5, "current_a": 22.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid", "modbus", "ip66"],
                     "tags": ["cfw500", "washdown", "ip66"]}),
    Component("DRV-CFW501-11-440", Kind.DRIVE, "Variador CFW501 11 kW 440V IP66",
              price_cop=4_580_000, margin_pct=0.33, stock=5,
              attrs={"power_kw_max": 11.0, "current_a": 17.5,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "ip66"],
                     "tags": ["cfw500", "washdown", "ip66"]}),

    # --- CFW700 / CFW11: alto desempeno ---
    Component("DRV-CFW700-18-220", Kind.DRIVE, "Variador CFW700 18.5 kW 220V",
              price_cop=6_850_000, margin_pct=0.31, stock=2,
              attrs={"power_kw_max": 18.5, "current_a": 80.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid", "modbus", "profibus"],
                     "tags": ["cfw700", "premium"]}),
    Component("DRV-CFW700-22-440", Kind.DRIVE, "Variador CFW700 22 kW 440V",
              price_cop=6_200_000, margin_pct=0.32, stock=6,
              attrs={"power_kw_max": 22.0, "current_a": 45.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "profibus"],
                     "tags": ["cfw700", "premium"]}),
    Component("DRV-CFW700-30-440", Kind.DRIVE, "Variador CFW700 30 kW 440V",
              price_cop=8_100_000, margin_pct=0.32, stock=9,
              attrs={"power_kw_max": 30.0, "current_a": 62.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "profibus"],
                     "tags": ["cfw700", "premium"]}),
    Component("DRV-CFW11-37-440", Kind.DRIVE, "Variador CFW11 37 kW 440V",
              price_cop=9_900_000, margin_pct=0.31, stock=4,
              attrs={"power_kw_max": 37.0, "current_a": 73.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "profibus"],
                     "tags": ["cfw11", "premium"]}),
    Component("DRV-CFW11-45-440", Kind.DRIVE, "Variador CFW11 45 kW 440V",
              price_cop=11_500_000, margin_pct=0.30, stock=2,
              attrs={"power_kw_max": 45.0, "current_a": 88.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "profibus"],
                     "tags": ["cfw11", "premium"]}),
]

# -------------------------------------------------------------- PROTECCION ---

PROTECTIONS = [
    Component("PRO-MPW12", Kind.PROTECTION, "Guardamotor MPW 12A",
              price_cop=250_000, margin_pct=0.36, stock=34,
              attrs={"current_a": 12.0, "tags": ["mpw"]}),
    Component("PRO-MPW18", Kind.PROTECTION, "Guardamotor MPW 18A",
              price_cop=320_000, margin_pct=0.35, stock=30,
              attrs={"current_a": 18.0, "tags": ["mpw"]}),
    Component("PRO-MPW25", Kind.PROTECTION, "Guardamotor MPW 25A",
              price_cop=410_000, margin_pct=0.35, stock=24,
              attrs={"current_a": 25.0, "tags": ["mpw"]}),
    Component("PRO-MPW32", Kind.PROTECTION, "Guardamotor MPW 32A",
              price_cop=480_000, margin_pct=0.34, stock=20,
              attrs={"current_a": 32.0, "tags": ["mpw"]}),
    Component("PRO-MPW40", Kind.PROTECTION, "Guardamotor MPW 40A",
              price_cop=560_000, margin_pct=0.33, stock=16,
              attrs={"current_a": 40.0, "tags": ["mpw"]}),
    Component("PRO-CWB50", Kind.PROTECTION, "Contactor CWB 50A",
              price_cop=670_000, margin_pct=0.32, stock=14,
              attrs={"current_a": 50.0, "tags": ["cwb"]}),
    Component("PRO-CWB63", Kind.PROTECTION, "Contactor CWB 63A",
              price_cop=780_000, margin_pct=0.31, stock=11,
              attrs={"current_a": 63.0, "tags": ["cwb"]}),
    Component("PRO-CWB80", Kind.PROTECTION, "Contactor CWB 80A",
              price_cop=950_000, margin_pct=0.30, stock=7,
              attrs={"current_a": 80.0, "tags": ["cwb"]}),
    Component("PRO-CWB100", Kind.PROTECTION, "Contactor CWB 100A",
              price_cop=1_200_000, margin_pct=0.29, stock=4,
              attrs={"current_a": 100.0, "tags": ["cwb"]}),
    Component("PRO-CWB125", Kind.PROTECTION, "Contactor CWB 125A",
              price_cop=1_540_000, margin_pct=0.28, stock=0,   # agotado
              attrs={"current_a": 125.0, "tags": ["cwb"]}),
]

# ----------------------------------------------------------------- CABLES ---
# Ampacidad segun seccion, para instalacion en ducto a 30 C.

CABLES = [
    Component("CAB-25MM2", Kind.CABLE, "Cable de potencia 2.5 mm2",
              price_cop=130_000, margin_pct=0.19, stock=48,
              attrs={"gauge_mm2": 2.5, "ampacity_a": 24.0, "tags": ["cable"]}),
    Component("CAB-4MM", Kind.CABLE, "Cable de potencia 4 mm2",
              price_cop=180_000, margin_pct=0.18, stock=40,
              attrs={"gauge_mm2": 4, "ampacity_a": 32.0, "tags": ["cable"]}),
    Component("CAB-6MM", Kind.CABLE, "Cable de potencia 6 mm2",
              price_cop=250_000, margin_pct=0.18, stock=35,
              attrs={"gauge_mm2": 6, "ampacity_a": 41.0, "tags": ["cable"]}),
    Component("CAB-10MM", Kind.CABLE, "Cable de potencia 10 mm2",
              price_cop=380_000, margin_pct=0.17, stock=22,
              attrs={"gauge_mm2": 10, "ampacity_a": 57.0, "tags": ["cable"]}),
    Component("CAB-16MM", Kind.CABLE, "Cable de potencia 16 mm2",
              price_cop=540_000, margin_pct=0.17, stock=18,
              attrs={"gauge_mm2": 16, "ampacity_a": 76.0, "tags": ["cable"]}),
    Component("CAB-25MM", Kind.CABLE, "Cable de potencia 25 mm2",
              price_cop=790_000, margin_pct=0.16, stock=9,
              attrs={"gauge_mm2": 25, "ampacity_a": 101.0, "tags": ["cable"]}),
    Component("CAB-35MM", Kind.CABLE, "Cable de potencia 35 mm2",
              price_cop=1_060_000, margin_pct=0.16, stock=5,
              attrs={"gauge_mm2": 35, "ampacity_a": 125.0, "tags": ["cable"]}),
]


ALL_COMPONENTS: list[Component] = [*MOTORS, *DRIVES, *PROTECTIONS, *CABLES]


# ------------------------------------------------- catalogo REAL de WEG ---

# Vive en data/ y NO en data/generated/ a proposito: es dato curado que se
# versiona con el repo, no un artefacto reconstruible. Un clon limpio trae los
# productos reales sin tener que descargar 13 MB de PDF primero. Los PDF de
# origen si quedan fuera del repo (copyright de WEG).
WEG_CATALOG = Path("data/weg_catalog.json")
# Compatibilidad: si alguien acaba de correr el ingestor, su salida sigue ahi.
WEG_CATALOG_GENERATED = Path("data/generated/weg_catalog.json")


def load_real_components() -> list[Component]:
    """Carga los productos REALES extraidos de los PDF oficiales de WEG.

    Los genera `python -m scripts.ingest_weg --pdf ... --kind ...` a partir de
    las tablas de los catalogos publicados en static.weg.net: numero de parte
    real, potencia, corriente, rango de voltaje y PRECIO DE LISTA en USD, cada
    fila con la pagina de la que salio.

    Si el archivo no existe, se devuelve lista vacia y el sistema corre solo
    con la semilla. No es un fallo: es el modo por defecto en un clon limpio.

    HONESTIDAD, y hay que decirlo antes de que lo pregunten: el precio en USD
    es de WEG; la conversion a COP es un supuesto NUESTRO (la tasa viaja
    declarada en el propio JSON). Especificaciones y numeros de parte son del
    fabricante; el stock es simulado, porque WEG no publica inventario.
    """
    path = WEG_CATALOG if WEG_CATALOG.exists() else WEG_CATALOG_GENERATED
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    components: list[Component] = []

    for item in raw.get("components", []):
        attrs = dict(item.get("attrs", {}))
        attrs["tags"] = [*attrs.get("tags", []), "weg_real"]
        features = list(attrs.get("features", []))

        # Los PDF no traen una columna de "caracteristicas", asi que un
        # variador real llegaria sin ninguna y jamas podria satisfacer un
        # FeatureRequirement — quedaria fuera de toda solucion.
        #
        # Se anade UNA sola, y por una razon fisica, no comercial: todo
        # variador de frecuencia arranca el motor con rampa; el arranque suave
        # es lo que hace un VFD por definicion. NO se infieren las demas
        # (modbus, ip66, profibus): esas dependen del modelo concreto y
        # deducirlas del numero de parte seria inventar.
        if item["kind"] == Kind.DRIVE.value and "soft_start" not in features:
            features.append("soft_start")
        attrs["features"] = features
        # Procedencia por componente: el juez puede pedir la fuente de
        # cualquier fila y sale de aqui, no de la memoria del modelo.
        attrs["source"] = item.get("source")
        attrs["price_usd"] = item.get("price_usd")

        components.append(Component(
            id=item["id"],
            kind=Kind(item["kind"]),
            name=item.get("name", item["id"]),
            price_cop=int(item["price_cop"]),
            # WEG no publica margen comercial: es un supuesto declarado, igual
            # para todo el catalogo real para no fingir precision que no hay.
            margin_pct=float(item.get("margin_pct", 0.25)),
            stock=int(item.get("stock", 5)),
            attrs=attrs,
        ))

    return components


def load_graph(include_real: bool = True):
    """Construye el grafo de conocimiento.

    Combina la semilla con el catalogo real de WEG si existe. Los ids reales
    son numeros de parte (CFW500A07P3T4...), asi que no chocan con los de la
    semilla (DRV-CFW500-7-220) y ambos conviven sin ambiguedad.

    Importa aqui adentro para evitar un ciclo de importacion con app.graph.
    """
    from app.graph.store import KnowledgeGraph

    graph = KnowledgeGraph()
    graph.add_many(ALL_COMPONENTS)
    if include_real:
        graph.add_many(load_real_components())
    return graph.build()
