"""Perfiles de aplicacion industrial -> restricciones candidatas.

EL PROBLEMA QUE RESUELVE:
El solver necesita "22 kW, 440 V, ip66". El cliente dice "necesito mover una
banda en la zona de lavado". Sin este puente, el agente solo sirve a quien ya
sabe la respuesta. Con el, sirve a quien tiene el problema.

HONESTIDAD DE DATOS — declararlo antes de que lo pregunten:
Este corpus es CURADO A MANO. No sale de documentacion de WEG ni de datos
historicos: es conocimiento de aplicacion escrito por el equipo. Por eso su
salida son SUGERENCIAS que el cliente confirma, nunca restricciones aplicadas
en silencio.

POR QUE NO ROMPE LA GARANTIA DEL SISTEMA:
Lo que sale de aqui son RESTRICCIONES, no productos. Entran al solver por el
mismo embudo que todo lo demas: si son imposibles de satisfacer, sale el nucleo
insatisfacible como con cualquier otra restriccion. El embedding puede
equivocarse de perfil; no puede producir una configuracion invalida.

Potencia y voltaje NUNCA se infieren: dependen de la carga real y de la
acometida del sitio. El agente los pregunta siempre.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationProfile:
    key: str
    # Redactado con el VOCABULARIO DEL CLIENTE, no con el del catalogo. Es lo
    # que se embebe, asi que debe parecerse a lo que el cliente escribiria.
    text: str
    # Restricciones candidatas, en el formato que acepta solve_configuration.
    suggests: dict
    # Se le muestra al cliente: una sugerencia sin justificacion no es
    # confirmable, es una imposicion.
    rationale: str


PROFILES: list[ApplicationProfile] = [
    ApplicationProfile(
        key="banda_transportadora",
        text=(
            "banda transportadora cinta transportadora transportador de rodillos "
            "mover cajas producto a lo largo de la linea carga constante arranque "
            "progresivo sin tirones velocidad ajustable"
        ),
        suggests={"features": ["soft_start"]},
        rationale=(
            "El arranque directo aplica todo el par de golpe: desalinea la banda, "
            "tumba el producto y castiga la transmision."
        ),
    ),
    ApplicationProfile(
        text=(
            "zona de lavado lavado a presion hidrolavadora limpieza con manguera "
            "planta de alimentos frigorifico ambiente humedo saneamiento diario "
            "agua directa sobre el equipo"
        ),
        key="lavado_alta_presion",
        suggests={"features": ["ip66"]},
        rationale=(
            "El lavado a presion exige sello IP66. Un IP55 resiste salpicadura, "
            "no chorro dirigido: entra agua y se pierde la garantia."
        ),
    ),
    ApplicationProfile(
        key="intemperie_polvo",
        text=(
            "a la intemperie exterior sin techo mucho polvo ambiente abrasivo "
            "cantera cementera mina patio de acopio arena cemento suspendido"
        ),
        suggests={"features": ["ip66"]},
        rationale=(
            "Polvo abrasivo en suspension penetra sellos bajos y desgasta "
            "rodamientos. IP66 es el grado que lo detiene."
        ),
    ),
    ApplicationProfile(
        key="bomba_presion_constante",
        text=(
            "bomba centrifuga bombeo de agua mantener la presion constante "
            "presion estable en la red caudal variable segun demanda "
            "sistema hidroneumatico riego acueducto"
        ),
        suggests={"features": ["pid", "soft_start"]},
        rationale=(
            "Mantener presion constante con demanda variable es un lazo cerrado: "
            "requiere PID. El arranque suave evita el golpe de ariete."
        ),
    ),
    ApplicationProfile(
        key="ventilador_extraccion",
        text=(
            "ventilador extractor ventilacion de nave extraccion de humos "
            "torre de enfriamiento regular el caudal de aire segun temperatura "
            "soplador aire acondicionado industrial"
        ),
        suggests={"features": ["pid"]},
        rationale=(
            "Regular caudal contra una variable medida (temperatura, presion) "
            "es control en lazo cerrado: requiere PID."
        ),
    ),
    ApplicationProfile(
        key="carga_alta_inercia",
        text=(
            "compresor de tornillo molino triturador chancadora centrifuga "
            "volante de inercia arranca con mucha carga cuesta arrancar "
            "el arranque tumba el breaker parpadean las luces al arrancar"
        ),
        suggests={"features": ["soft_start"]},
        rationale=(
            "Las cargas de alta inercia piden 6-8 veces la corriente nominal al "
            "arrancar. El arranque suave la acota y evita disparar la proteccion."
        ),
    ),
    ApplicationProfile(
        key="supervision_plc",
        text=(
            "integrar con el PLC SCADA monitoreo remoto telemetria supervision "
            "centralizada leer variables desde el cuarto de control historicos "
            "de operacion alarmas en pantalla mantenimiento predictivo"
        ),
        suggests={"features": ["modbus"]},
        rationale=(
            "Leer variables del equipo desde un sistema central exige bus de "
            "campo. Modbus RTU/TCP es el mas extendido."
        ),
    ),
    ApplicationProfile(
        key="red_profibus",
        text=(
            "la planta ya tiene profibus red profibus dp automatizacion siemens "
            "debe hablar con el bus existente estandar de la planta "
            "integracion con la arquitectura de control actual"
        ),
        suggests={"features": ["profibus"]},
        rationale=(
            "Si la planta ya estandarizo Profibus, un equipo que solo hable "
            "Modbus obliga a un gateway extra."
        ),
    ),
    ApplicationProfile(
        key="urgencia_parada",
        text=(
            "se quemo el motor la linea esta parada paro la produccion urgente "
            "lo necesito para ya no puedo esperar reemplazo inmediato "
            "estamos perdiendo produccion cada hora emergencia"
        ),
        suggests={"require_stock": True},
        rationale=(
            "Con la linea parada, un equipo sin inventario no es una opcion "
            "aunque sea mas barato: se exige disponibilidad inmediata."
        ),
    ),
    ApplicationProfile(
        key="proyecto_planificado",
        text=(
            "es un proyecto para el proximo ano estamos cotizando presupuesto "
            "todavia no compramos evaluando alternativas ampliacion planeada "
            "no hay afan tenemos tiempo"
        ),
        suggests={"require_stock": False},
        rationale=(
            "Sin urgencia, no exigir inventario amplia el espacio de soluciones "
            "y suele abaratar la configuracion."
        ),
    ),
]


def as_chunks() -> list:
    """Convierte los perfiles en Chunks indexables.

    El `text` embebido es el vocabulario del cliente; `suggests` y `rationale`
    viajan en `meta` y salen intactos en la recuperacion.
    """
    from app.retrieval.chunks import Chunk

    return [
        Chunk(
            text=p.text,
            source="perfiles_de_aplicacion",
            page=0,
            meta={"key": p.key, "suggests": p.suggests, "rationale": p.rationale},
        )
        for p in PROFILES
    ]


def combine(suggestions: list[dict]) -> tuple[dict, list[str]]:
    """Fusiona las restricciones de varios perfiles. Devuelve (union, conflictos).

    Las `features` se acumulan: pedir arranque suave Y ip66 es coherente.
    `require_stock` es booleano y SI puede entrar en conflicto — "se paro la
    linea" y "es un proyecto del proximo ano" se contradicen. En ese caso no se
    inventa un desempate: se omite del combinado y se reporta, para que el
    agente lo pregunte. Adivinar aqui seria decidir por el cliente.
    """
    features: list[str] = []
    stock_votes: set[bool] = set()

    for suggestion in suggestions:
        for feature in suggestion.get("features", []):
            if feature not in features:
                features.append(feature)
        if "require_stock" in suggestion:
            stock_votes.add(bool(suggestion["require_stock"]))

    merged: dict = {}
    conflicts: list[str] = []

    if features:
        merged["features"] = features

    if len(stock_votes) == 1:
        merged["require_stock"] = next(iter(stock_votes))
    elif len(stock_votes) > 1:
        conflicts.append(
            "La descripcion sugiere a la vez urgencia y proyecto sin afan. "
            "Pregunta al cliente si exige disponibilidad inmediata."
        )

    return merged, conflicts


def unknown_features(graph) -> set[str]:
    """Caracteristicas sugeridas que NINGUN componente del catalogo ofrece.

    Se verifica en el smoke test: un perfil que sugiere una feature inexistente
    genera consultas condenadas a salir insatisfacibles, y el cliente se lleva
    la culpa de una restriccion que le propuso el sistema.
    """
    available: set[str] = set()
    for component in graph.all():
        available |= component.features

    suggested = {f for p in PROFILES for f in p.suggests.get("features", [])}
    return suggested - available
