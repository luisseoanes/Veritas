"""Ingesta del catalogo real de WEG desde sus PDF oficiales.

POR QUE PDF Y NO API:
  - WEG no publica API de catalogo. Sus APIs (IoT Platform, Motor Fleet
    Management) son de monitoreo de activos, no de productos.
  - www.weg.net responde 403 a peticiones automatizadas (WAF anti-bot).
  - static.weg.net —el CDN del Download Center— si sirve los PDF oficiales
    libremente, y sus tablas de seleccion traen numero de parte, corriente,
    voltaje, tamano de carcasa y precio de lista.

Uso:
    python -m scripts.ingest_weg --pdf data/raw/weg-drives.pdf --kind drive
    python -m scripts.ingest_weg --url https://static.weg.net/... --kind drive

Salida: data/generated/weg_catalog.json, que app/data/catalog.py carga si existe.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/generated/weg_catalog.json")

# WEG publica precios de lista en USD. La conversion a COP es un supuesto
# declarado, no un dato: se expone en el JSON para que sea auditable.
USD_TO_COP = 4100


# --------------------------------------------------------------- extraccion

# Encabezados de seccion que fijan el voltaje de las filas siguientes.
# Ej: "Input Power Supply: Three-Phase 200-240 VAC"  |  "460 VAC / Three-Phase"
_VOLTAGE_SECTION = re.compile(
    r"(?:Input Power Supply:\s*)?(?P<phase>Single-Phase|Three-Phase)?\s*"
    r"(?P<v1>\d{3})(?:\s*[-–]\s*(?P<v2>\d{3}))?\s*VAC",
    re.IGNORECASE,
)

# Fila de tabla de seleccion de variador:
#   <HP> <Amps> <CatalogNumber> ... $<Price>
# El HP puede venir como "1/4 or 1/3", "3/4", "1", "7 1/2" — se normaliza aparte.
_DRIVE_ROW = re.compile(
    r"^(?P<hp>[\d][\d\s/.or–-]*?)\s+"
    r"(?P<amps>\d+\.?\d*)\s+"
    r"(?P<code>(?:CFW|SSW)[A-Z0-9]+)\b"
    r"(?P<rest>.*?)"
    r"\$(?P<price>[\d,]+)",
    re.IGNORECASE,
)

_HP_TO_KW = 0.7457


@dataclass
class ParsedRow:
    code: str
    kind: str
    hp: float
    power_kw: float
    current_a: float
    voltage_min: int
    voltage_max: int
    phase: str
    price_usd: int
    source_page: int
    raw: str = field(repr=False, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.code,
            "kind": self.kind,
            "name": f"WEG {self.code}",
            "price_usd": self.price_usd,
            "price_cop": int(self.price_usd * USD_TO_COP),
            "attrs": {
                "power_kw_max": round(self.power_kw, 2),
                "hp": self.hp,
                "current_a": self.current_a,
                "voltage_min": self.voltage_min,
                "voltage_max": self.voltage_max,
                "phase": self.phase,
            },
            "source": {"page": self.source_page, "raw_row": self.raw.strip()[:200]},
        }


def _parse_hp(raw: str) -> float | None:
    """Normaliza '1/4 or 1/3', '7 1/2', '3/4', '25' a un float en HP.

    Cuando la fila da un rango ("1/4 or 1/3") se toma el MENOR: es el valor
    conservador para dimensionar, y evita sobrestimar la capacidad del equipo.
    """
    raw = raw.strip().lower().replace("–", "-")
    candidates = re.split(r"\s+or\s+|-", raw)

    values = []
    for chunk in candidates:
        chunk = chunk.strip()
        if not chunk:
            continue
        # "7 1/2" -> 7.5
        if m := re.fullmatch(r"(\d+)\s+(\d+)/(\d+)", chunk):
            values.append(int(m.group(1)) + int(m.group(2)) / int(m.group(3)))
        elif m := re.fullmatch(r"(\d+)/(\d+)", chunk):
            values.append(int(m.group(1)) / int(m.group(2)))
        elif re.fullmatch(r"\d+\.?\d*", chunk):
            values.append(float(chunk))

    return min(values) if values else None


def _voltage_from_header(line: str) -> tuple[int, int, str] | None:
    m = _VOLTAGE_SECTION.search(line)
    if not m:
        return None
    v1 = int(m.group("v1"))
    v2 = int(m.group("v2")) if m.group("v2") else v1
    phase = (m.group("phase") or "").strip() or "unknown"
    return v1, v2, phase


def parse_drives(reader: PdfReader) -> list[ParsedRow]:
    """Recorre el PDF manteniendo el voltaje de la seccion vigente.

    Las tablas de WEG no repiten el voltaje en cada fila: lo declaran en un
    encabezado y las filas siguientes lo heredan. Por eso el parseo es con
    estado, no linea a linea de forma independiente.
    """
    rows: list[ParsedRow] = []
    seen: set[str] = set()

    for page_no, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        voltage: tuple[int, int, str] | None = None

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            if (found := _voltage_from_header(line)) and not _DRIVE_ROW.match(line):
                voltage = found
                continue

            match = _DRIVE_ROW.match(line)
            if not match or voltage is None:
                continue

            hp = _parse_hp(match.group("hp"))
            if hp is None:
                continue

            code = match.group("code").upper()
            if code in seen:
                continue  # Los PDF repiten filas en indices y resumenes.
            seen.add(code)

            v_min, v_max, phase = voltage
            rows.append(ParsedRow(
                code=code,
                kind="drive",
                hp=hp,
                power_kw=hp * _HP_TO_KW,
                current_a=float(match.group("amps")),
                voltage_min=v_min,
                voltage_max=v_max,
                phase=phase,
                price_usd=int(match.group("price").replace(",", "")),
                source_page=page_no,
                raw=line,
            ))

    return rows


# ------------------------------------------------------------------- entrada


def fetch(url: str, dest: Path) -> Path:
    """Descarga un PDF del Download Center. static.weg.net no bloquea bots."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Descargando {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response, dest.open("wb") as fh:
        fh.write(response.read())
    print(f"  -> {dest} ({dest.stat().st_size / 1_000_000:.1f} MB)")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta el catalogo real de WEG")
    parser.add_argument("--pdf", type=Path, help="Ruta a un PDF ya descargado")
    parser.add_argument("--url", help="URL de static.weg.net a descargar")
    parser.add_argument("--kind", default="drive", choices=["drive"],
                        help="Familia a extraer (por ahora variadores)")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()

    if not args.pdf and not args.url:
        parser.error("Indica --pdf o --url")

    path = args.pdf or fetch(args.url, RAW_DIR / "weg-download.pdf")
    if not path.exists():
        parser.error(f"No existe el archivo {path}")

    reader = PdfReader(str(path))
    print(f"Leyendo {path.name}: {len(reader.pages)} paginas")

    rows = parse_drives(reader)
    print(f"Filas extraidas: {len(rows)}")

    if not rows:
        print("\nNinguna fila reconocida. Revisa que el PDF sea un catalogo con "
              "tablas de seleccion (no un manual de usuario).")
        return

    by_voltage: dict[str, int] = {}
    for row in rows:
        key = f"{row.voltage_min}-{row.voltage_max}V {row.phase}"
        by_voltage[key] = by_voltage.get(key, 0) + 1

    print("\nDistribucion por seccion de voltaje:")
    for key, count in sorted(by_voltage.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>4}  {key}")

    powers = sorted({round(r.power_kw, 1) for r in rows})
    print(f"\nRango de potencia: {powers[0]} - {powers[-1]} kW  ({len(powers)} valores)")
    print(f"Rango de precio  : ${min(r.price_usd for r in rows):,} - "
          f"${max(r.price_usd for r in rows):,} USD")

    payload = {
        "source": str(path.name),
        "supuestos": {
            "usd_to_cop": USD_TO_COP,
            "nota": (
                "WEG publica precios de lista en USD. La conversion a COP es un "
                "supuesto declarado, no un dato del fabricante."
            ),
        },
        "components": [r.to_dict() for r in rows],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nEscrito: {args.out}")

    print("\nMuestra:")
    for row in rows[:5]:
        print(f"  {row.code:<24} {row.power_kw:>6.2f} kW  {row.current_a:>6.1f} A  "
              f"{row.voltage_min}-{row.voltage_max}V  ${row.price_usd:,}")


if __name__ == "__main__":
    main()
