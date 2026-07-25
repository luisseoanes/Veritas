"""Catalogo semilla del dominio WEG (accionamientos industriales).

IMPORTANTE — honestidad de datos:
Estos componentes son REPRESENTATIVOS, construidos a partir de rangos tipicos
de lineas WEG (motores W22, variadores CFW, contactores CWB / guardamotores
MPW, conductores). NO son un volcado del catalogo oficial. Se reemplazan por
los datos reales de WEG cargando el mismo formato.

Lo que NUNCA es representativo es la logica: reglas de compatibilidad, solver,
nucleo insatisfacible y frontera de Pareto operan sobre estos datos exactamente
igual que sobre los reales. Los datos son semilla; el motor es real.

Corriente nominal aproximada segun  I = P / (sqrt(3) * V * fp * eta).
"""
from __future__ import annotations

from app.graph.schema import Component, Kind

# ---------------------------------------------------------------- MOTORES ---
# Trifasicos de induccion. `tags` marca la familia comercial: los objetivos de
# negocio del tipo "impulsar linea X" operan sobre estas etiquetas.

MOTORS = [
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
    Component("MOT-W22-7-440", Kind.MOTOR, "Motor W22 7.5 kW 440V IE3",
              price_cop=3_980_000, margin_pct=0.23, stock=11,
              attrs={"power_kw": 7.5, "voltage": 440, "current_a": 13.5,
                     "rpm": 1750, "efficiency_pct": 91.2, "frame": "132S",
                     "tags": ["w22", "ie3"]}),
    Component("MOT-W22-15-440", Kind.MOTOR, "Motor W22 15 kW 440V IE3",
              price_cop=6_900_000, margin_pct=0.21, stock=7,
              attrs={"power_kw": 15.0, "voltage": 440, "current_a": 26.0,
                     "rpm": 1750, "efficiency_pct": 92.4, "frame": "160L",
                     "tags": ["w22", "ie3"]}),
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
]

# -------------------------------------------------------------- VARIADORES ---
# `features` alimenta los FeatureRequirement del cliente (arranque suave,
# comunicacion, grado de proteccion).

DRIVES = [
    Component("DRV-CFW300-4-220", Kind.DRIVE, "Variador CFW300 4 kW 220V",
              price_cop=1_620_000, margin_pct=0.28, stock=18,
              attrs={"power_kw_max": 4.0, "current_a": 16.0,
                     "voltage_min": 200, "voltage_max": 240,
                     "features": ["soft_start", "pid"],
                     "tags": ["cfw300", "compacto"]}),
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
    Component("DRV-CFW500-11-440", Kind.DRIVE, "Variador CFW500 11 kW 440V",
              price_cop=3_150_000, margin_pct=0.31, stock=15,
              attrs={"power_kw_max": 11.0, "current_a": 17.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus"],
                     "tags": ["cfw500"]}),
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
    Component("DRV-CFW11-45-440", Kind.DRIVE, "Variador CFW11 45 kW 440V",
              price_cop=11_500_000, margin_pct=0.30, stock=2,
              attrs={"power_kw_max": 45.0, "current_a": 88.0,
                     "voltage_min": 380, "voltage_max": 480,
                     "features": ["soft_start", "pid", "modbus", "profibus", "ip66"],
                     "tags": ["cfw11", "premium"]}),
]

# -------------------------------------------------------------- PROTECCION ---

PROTECTIONS = [
    Component("PRO-MPW18", Kind.PROTECTION, "Guardamotor MPW 18A",
              price_cop=320_000, margin_pct=0.35, stock=30,
              attrs={"current_a": 18.0, "tags": ["mpw"]}),
    Component("PRO-MPW25", Kind.PROTECTION, "Guardamotor MPW 25A",
              price_cop=410_000, margin_pct=0.35, stock=24,
              attrs={"current_a": 25.0, "tags": ["mpw"]}),
    Component("PRO-MPW40", Kind.PROTECTION, "Guardamotor MPW 40A",
              price_cop=560_000, margin_pct=0.33, stock=16,
              attrs={"current_a": 40.0, "tags": ["mpw"]}),
    Component("PRO-CWB63", Kind.PROTECTION, "Contactor CWB 63A",
              price_cop=780_000, margin_pct=0.31, stock=11,
              attrs={"current_a": 63.0, "tags": ["cwb"]}),
    Component("PRO-CWB80", Kind.PROTECTION, "Contactor CWB 80A",
              price_cop=950_000, margin_pct=0.30, stock=7,
              attrs={"current_a": 80.0, "tags": ["cwb"]}),
    Component("PRO-CWB100", Kind.PROTECTION, "Contactor CWB 100A",
              price_cop=1_200_000, margin_pct=0.29, stock=4,
              attrs={"current_a": 100.0, "tags": ["cwb"]}),
]

# ----------------------------------------------------------------- CABLES ---
# Ampacidad segun seccion, para instalacion en ducto a 30 C.

CABLES = [
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
]


ALL_COMPONENTS: list[Component] = [*MOTORS, *DRIVES, *PROTECTIONS, *CABLES]


def load_graph():
    """Construye el grafo de conocimiento a partir del catalogo semilla.

    Importa aqui adentro para evitar un ciclo de importacion con app.graph.
    """
    from app.graph.store import KnowledgeGraph

    graph = KnowledgeGraph()
    graph.add_many(ALL_COMPONENTS)
    return graph.build()
