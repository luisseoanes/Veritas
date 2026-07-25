"""Generador de historico de conversaciones.

QUE ES SINTETICO Y QUE NO — leelo antes de presentarlo:

  Sintetico: los PERFILES de cliente (que potencia, que voltaje, que
  presupuesto pide cada uno). Son muestras aleatorias con semilla fija.

  Real: TODO lo demas. Cada perfil se resuelve con el solver de verdad, sobre
  el grafo de verdad. Los eventos SOLVED y UNMET que quedan registrados son
  salidas autenticas del motor — incluidos los nucleos insatisfacibles y los
  minimos viables.

Sin este historico los detectores no tienen de que detectar: un dashboard de
inteligencia de negocio con cuatro conversaciones de demo no muestra nada. Con
el, el motor corre sobre volumen realista y la demo en vivo AGREGA eventos
encima, que es exactamente lo que se muestra al jurado.

Uso:  python -m scripts.generate_history --sessions 400
"""
from __future__ import annotations

import argparse
import random

from app.agent.tools import set_session, solve_configuration
from app.intelligence.events import event_log
from app.state import state

# Perfiles de demanda del mercado industrial, con su peso relativo.
POWER_PROFILE = [
    (3.0, 0.14), (5.5, 0.20), (7.5, 0.22), (11.0, 0.16),
    (15.0, 0.15), (22.0, 0.08), (30.0, 0.05),
]
VOLTAGE_PROFILE = [(220, 0.55), (440, 0.45)]

# Frecuencia con que el mercado pide cada caracteristica. Arranque suave y PID
# son casi universales; Profibus e IP66 son de nicho. Modelar esto importa: si
# todos los clientes sinteticos pidieran Profibus, el historico mostraria una
# tasa de fracaso irreal y el detector aprenderia de un mercado que no existe.
FEATURE_PROFILE = [
    ("soft_start", 0.38), ("pid", 0.28), ("modbus", 0.22),
    ("profibus", 0.08), ("ip66", 0.04),
]

# Presupuesto como multiplo del costo tipico del perfil. Deliberadamente
# incluye clientes con presupuesto insuficiente: esos generan los eventos UNMET
# que son la materia prima del detector de demanda no satisfecha.
BUDGET_MULTIPLIER = [(0.70, 0.15), (0.95, 0.20), (1.20, 0.35), (1.60, 0.30)]

# Costo real por kW observado en el catalogo: la solucion mas barata de 5.5 kW
# cuesta ~$6.0M y la de 15 kW ~$13.2M, es decir ~$1.1M por kW. Calibrar esta
# constante contra el solver evita generar un historico donde casi nadie tiene
# presupuesto — un catalogo se veria artificialmente incapaz de vender.
BASE_COST_PER_KW = 1_100_000


def _weighted(options: list[tuple]) -> object:
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def generate(sessions: int, seed: int = 42, reset: bool = True) -> dict:
    random.seed(seed)
    if reset:
        event_log.clear()

    stats = {"sessions": sessions, "solved": 0, "unmet": 0}

    for i in range(sessions):
        set_session(f"hist-{i:04d}")

        power_kw = _weighted(POWER_PROFILE)
        voltage = _weighted(VOLTAGE_PROFILE)
        multiplier = _weighted(BUDGET_MULTIPLIER)
        budget = int(power_kw * BASE_COST_PER_KW * multiplier)

        # La mayoria de compradores no exige caracteristicas especiales.
        n_features = random.choices([0, 1, 2], weights=[0.45, 0.42, 0.13], k=1)[0]
        names, weights = zip(*FEATURE_PROFILE)
        features = list(dict.fromkeys(random.choices(names, weights=weights, k=n_features)))

        # Se llama a la MISMA tool que usa el agente: mismo solver, mismo
        # registro de eventos. Nada aqui es un atajo.
        result = solve_configuration(
            power_kw=power_kw,
            voltage=voltage,
            budget_cop=budget,
            features=features or None,
            require_stock=True,
        )
        if '"SIN_SOLUCION"' in result:
            stats["unmet"] += 1
        else:
            stats["solved"] += 1

    set_session("default")
    stats["events"] = len(event_log)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera historico de conversaciones")
    parser.add_argument("--sessions", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--keep", action="store_true", help="No borrar el historico existente")
    args = parser.parse_args()

    print(f"Grafo: {state.graph.stats()}")
    print(f"Generando {args.sessions} sesiones (semilla {args.seed})...\n")

    stats = generate(args.sessions, seed=args.seed, reset=not args.keep)

    solved, unmet = stats["solved"], stats["unmet"]
    print(f"  Resueltas       : {solved:>4}  ({solved / stats['sessions']:.0%})")
    print(f"  Sin solucion    : {unmet:>4}  ({unmet / stats['sessions']:.0%})")
    print(f"  Eventos totales : {stats['events']:>4}")
    print("\nHistorico escrito en data/generated/events.jsonl")


if __name__ == "__main__":
    main()
