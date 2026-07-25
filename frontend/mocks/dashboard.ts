import type { DashboardResponse } from "@/lib/api/types";

export function mockDashboard(objetivoActivo: string): DashboardResponse {
  return {
    supuestos: {
      tasa_conversion_asumida: 0.15,
      umbral_co_ocurrencia_bundle: 3,
      nota:
        "Los impactos económicos son estimaciones bajo estos supuestos declarados, calculadas por código " +
        "sobre datos reales de las conversaciones. Ninguna cifra proviene del modelo de lenguaje.",
    },
    demanda_no_satisfecha: [
      {
        tipo: "demanda_no_satisfecha",
        naturaleza: "brecha_de_producto",
        clientes_afectados: 16,
        restriccion_causante: ["power_kw_22.0", "voltage_220"],
        perfil: { power_kw: 22.0, voltage: 220 },
        presupuesto_promedio_cop: 5000000,
        minimo_viable_cop: 7200000,
        brecha_cop: 2200000,
        demanda_direccionable_cop: 12000000,
        formula: "16 clientes x $5,000,000 presupuesto promedio x 15% conversion = $12,000,000",
        recomendacion:
          "BRECHA DE PRODUCTO: no existe motor de 22 kW a 220 V en el catálogo. 16 clientes chocaron con la " +
          "misma restricción. Evaluar referencia intermedia o solución con transformador.",
      },
      {
        tipo: "demanda_no_satisfecha",
        naturaleza: "brecha_de_precio",
        clientes_afectados: 11,
        restriccion_causante: ["budget_4500000"],
        perfil: { power_kw: 7.5, voltage: 440 },
        presupuesto_promedio_cop: 4500000,
        minimo_viable_cop: 5900000,
        brecha_cop: 1400000,
        demanda_direccionable_cop: 7425000,
        formula: "11 clientes x $4,500,000 presupuesto promedio x 15% conversion = $7,425,000",
        recomendacion:
          "BRECHA DE PRECIO: el mínimo viable está $1,400,000 por encima del presupuesto típico. " +
          "Un kit de entrada o financiación a 12 meses recupera la demanda.",
      },
    ],
    brechas_de_bundle: [
      {
        tipo: "brecha_de_bundle",
        componentes: ["CFW300-B", "MPW25-3"],
        nombres: ["Variador CFW300 220V", "Guardamotor MPW25 3A"],
        co_ocurrencias: 12,
        margen_combinado_cop: 800000,
        impacto_estimado_cop: 1440000,
        formula: "12 co-ocurrencias x $800,000 margen combinado x 15% conversion = $1,440,000",
        recomendacion:
          "Crear bundle 'Variador CFW300 220V + Guardamotor MPW25 3A': aparecen juntos en 12 " +
          "configuraciones resueltas y hoy se cotizan por separado.",
      },
      {
        tipo: "brecha_de_bundle",
        componentes: ["MOT-W22-055-220", "CAB-4MM"],
        nombres: ["Motor W22 IE3 5.5kW 220V", "Cable 4 mm² apantallado"],
        co_ocurrencias: 9,
        margen_combinado_cop: 520000,
        impacto_estimado_cop: 702000,
        formula: "9 co-ocurrencias x $520,000 margen combinado x 15% conversion = $702,000",
        recomendacion:
          "Crear bundle 'Motor W22 IE3 5.5kW 220V + Cable 4 mm² apantallado' como kit de instalación.",
      },
    ],
    riesgo_de_inventario: [
      {
        tipo: "riesgo_de_inventario",
        componente: "MPW25-3",
        nombre: "Guardamotor MPW25 3A",
        stock: 2,
        unica_opcion_para: 8,
        veces_recomendado: 40,
        indice_riesgo: 24.0,
        exposicion_cop: 9000000,
        formula: "(40 recomendaciones + 8 dependientes) / 2 unidades en stock = indice 24.0",
        recomendacion:
          "Si MPW25-3 se agota, 8 configuraciones quedan sin alternativa válida. Reponer antes de la " +
          "próxima campaña: exposición estimada $9,000,000.",
      },
      {
        tipo: "riesgo_de_inventario",
        componente: "CFW300-B",
        nombre: "Variador CFW300 220V",
        stock: 5,
        unica_opcion_para: 3,
        veces_recomendado: 31,
        indice_riesgo: 6.8,
        exposicion_cop: 4100000,
        formula: "(31 recomendaciones + 3 dependientes) / 5 unidades en stock = indice 6.8",
        recomendacion:
          "Riesgo moderado. CFW300-B es única opción para 3 escenarios de arranque suave a 220 V.",
      },
    ],
    eventos_analizados: 402,
    resumen: {
      conversaciones_totales: 402,
      resueltas: 234,
      sin_solucion: 168,
      objetivo_activo: objetivoActivo,
    },
  };
}
