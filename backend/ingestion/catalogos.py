# -*- coding: utf-8 -*-
"""Catálogos oficiales de referencia para la validación de la ingesta.

Los valores de este módulo son la fuente de verdad de la nomenclatura aceptada y
replican exactamente la salida del pipeline de limpieza del proyecto BI
(`BI-SEN-Back/etl/data_cleaner.py`). Mantenerlos idénticos garantiza que los
registros capturados por el formulario carguen en `dim_ubicacion` y `dim_evento`
sin necesidad de estandarización posterior.

Cualquier modificación aquí debe replicarse en el catálogo del frontend
(`frontend/src/features/ingesta/catalogos.ts`).
"""

import re
import unicodedata

# Orden oficial de los departamentos. Alimenta `dim_ubicacion.orden`, que el
# dashboard usa para ordenar los ejes de sus gráficos.
DEPARTAMENTO_ORDEN = {
    'CONCEPCIÓN': 1,
    'SAN PEDRO': 2,
    'CORDILLERA': 3,
    'GUAIRÁ': 4,
    'CAAGUAZÚ': 5,
    'CAAZAPÁ': 6,
    'ITAPÚA': 7,
    'MISIONES': 8,
    'PARAGUARÍ': 9,
    'ALTO PARANÁ': 10,
    'CENTRAL': 11,
    'ÑEEMBUCÚ': 12,
    'AMAMBAY': 13,
    'CANINDEYÚ': 14,
    'PDTE. HAYES': 15,
    'ALTO PARAGUAY': 16,
    'BOQUERON': 17,
    'CAPITAL': 18,
}

# Distritos válidos por departamento (división político-administrativa oficial).
DISTRITOS_POR_DEPARTAMENTO = {
    'CAPITAL': {'ASUNCIÓN'},
    'CONCEPCIÓN': {
        'CONCEPCIÓN', 'BELÉN', 'HORQUETA', 'LORETO', 'SAN CARLOS', 'SAN LÁZARO',
        "YVY YA'Ú", 'AZOTEY', 'SGTO. JOSÉ FÉLIX LÓPEZ', 'SAN ALFREDO',
        'PASO BARRETO', 'ITACUÁ', 'PASO HORQUETA', 'ARROYITO',
    },
    'SAN PEDRO': {
        'SAN PEDRO DEL YKUAMANDIYÚ', 'ANTEQUERA', 'CHORE',
        'GRAL. ELIZARDO AQUINO', 'ITACURUBÍ DEL ROSARIO', 'LIMA',
        'NUEVA GERMANIA', 'SAN ESTANISLAO', 'SAN PABLO', 'TACUATÍ', 'UNIÓN',
        '25 DE DICIEMBRE', 'VILLA DEL ROSARIO', 'GRAL. RESQUÍN',
        'YATAITY DEL NORTE', 'GUAJAYVÍ', 'CAPIIBARY', 'SANTA ROSA DEL AGUARAY',
        'YRYBUCUÁ', 'LIBERACIÓN', 'SAN JOSÉ DEL ROSARIO',
        'SAN VICENTE PANCHOLO',
    },
    'CORDILLERA': {
        'CAACUPÉ', 'ALTOS', 'ARROYOS Y ESTEROS', 'ATYRÁ', 'CARAGUATAY',
        'EMBOSCADA', 'EUSEBIO AYALA', 'ISLA PUCÚ',
        'ITACURUBÍ DE LA CORDILLERA', 'JUAN DE MENA', 'LOMA GRANDE',
        'MBOCAYATY DEL YHAGUY', 'NUEVA COLOMBIA', 'PIRIBEBUY',
        'PRIMERO DE MARZO', 'SAN BERNARDINO', 'SANTA ELENA',
        'SAN JOSÉ OBRERO', 'TOBATÍ', 'VALENZUELA',
    },
    'GUAIRÁ': {
        'VILLARRICA', 'BORJA', 'CAPITÁN MAURICIO JOSÉ TROCHE',
        'COLONIA INDEPENDENCIA', 'DR. BOTRELL', 'FÉLIX PÉREZ CARDOZO',
        'GARAMBARÉ', 'ITAPÉ', 'ITURBE', 'JOSÉ FASSARDI', 'MBOCAYATY',
        'NATALICIO TALAVERA', 'ÑUMÍ', 'PASO YOBÁI', 'SAN SALVADOR',
        'TEBAICUARY', 'YATAITY DEL GUAIRÁ',
    },
    'CAAGUAZÚ': {
        'CAAGUAZÚ', 'CORONEL OVIEDO', 'DR. J. EULOGIO ESTIGARRIBIA',
        'DR. JUAN MANUEL FRUTOS', 'SAN JOAQUÍN', 'SAN JOSÉ DE LOS ARROYOS',
        'LA PASTORA', 'NUEVA TOLEDO', 'VAQUERÍA', 'YHÚ', '3 DE FEBRERO',
        'CARAYAÓ', 'MCAL. FCO. SOLANO LÓPEZ', 'NUEVA LONDRES',
        'RAÚL ARSENIO OVIEDO', 'REPATRIACIÓN', 'R.I. 3 CORRALES',
        'SIMÓN BOLIVAR',
    },
    'CAAZAPÁ': {
        'CAAZAPÁ', '3 DE MAYO', 'ABAÍ', 'BUENA VISTA', 'CORONEL MACIEL',
        'DR. MOISÉS S. BERTONI', 'FULGENCIO YEGROS',
        'GRAL. HIGINIO MORÍNIGO', 'SAN JUAN NEPOMUCENO', 'TAVAÍ', 'YUTY',
    },
    'ITAPÚA': {
        'ENCARNACIÓN', 'CAMBYRETÁ', 'CAPITÁN MIRANDA', 'CORONEL BOGADO',
        'FRAM', 'GENERAL ARTIGAS', 'HOHENAU', 'JESÚS DE TAVARANGUÉ',
        'LA PAZ', 'OBLIGADO', 'PIRAPÓ', 'SAN COSME Y DAMIÁN',
        'SAN JUAN DEL PARANÁ', 'SAN PEDRO DEL PARANÁ', 'TRINIDAD', 'NATALIO',
        'CARMEN DEL PARANÁ', 'YATYTAY', 'MAYOR JOSÉ D. OTAÑO',
        'SAN RAFAEL DEL PARANÁ', 'BELLA VISTA', 'CAPITÁN MEZA', 'EDELIRA',
        'ITAPÚA POTY', 'ALTO VERÁ', 'TOMÁS ROMERO PEREIRA',
    },
    'MISIONES': {
        'SAN JUAN BAUTISTA', 'AYOLAS', 'SAN IGNACIO GUAZÚ',
        'SANTA MARÍA DE FE', 'SANTIAGO', 'VILLA FLORIDA', 'YABEBIRY',
        'SAN MIGUEL', 'SAN PATRICIO', 'SANTA ROSA',
    },
    'PARAGUARÍ': {
        'PARAGUARÍ', 'CARAPEGUÁ', 'ACAHAY', 'CAAPUCÚ', 'CABALLERO',
        'ESCOBER', 'LA COLMENA', 'MBUYAPEY', 'PIRAYÚ', 'QUIINDY',
        'QUYQUYHÓ', 'SAN ROQUE GONZÁLEZ DE SANTA CRUZ', 'SAPUCAI',
        'TEBICUARYMÍ', 'YAGUARÓN', 'YBYCUÍ', 'YBYTYMÍ', 'MARÍA ANTONIA',
    },
    'ALTO PARANÁ': {
        'CIUDAD DEL ESTE', 'DOCTOR JUAN LEÓN MALLORQUÍN',
        'DOCTOR RAÚL PEÑA', 'DOMINGO MARTÍNEZ DE IRALA', 'HERNANDARIAS',
        'IRUÑA', 'ITAKYRY', "JUAN EMILIO O'LEARY", 'LOS CEDRALES',
        'MBARACAYÚ', 'MINGA GUAZÚ', 'MINGA PORÁ', 'NARANJAL', 'ÑACUNDAY',
        'PRESIDENTE FRANCO', 'SAN ALBERTO', 'SAN CRISTÓBAL',
        'SANTA FE DEL PARANÁ', 'SANTA RITA', 'SANTA ROSA DEL MONDAY',
        'TAVAPY', 'YGUAZÚ',
    },
    'CENTRAL': {
        'AREGUÁ', 'CAPIATÁ', 'FERNANDO DE LA MORA', 'GUARAMBARÉ', 'ITÁ',
        'ITAUGUÁ', 'J. AUGUSTO SALDÍVAR', 'LAMBARÉ', 'LIMPIO', 'LUQUE',
        'MARIANO ROQUE ALONSO', 'ÑEMBY', 'NUEVA ITALIA', 'SAN ANTONIO',
        'SAN LORENZO', 'VILLA ELISA', 'VILLETTA', 'YPACARAÍ', 'YPANÉ',
    },
    'ÑEEMBUCÚ': {
        'PILAR', 'CERRITO', 'DESMOCHADOS', 'GENERAL JOSÉ EDUVIGIS DÍAS',
        'GUAZÚ CUÁ', 'HUMAITÁ', 'ISLA UMBÚ', 'LAURELES', 'PASO DE PATRIA',
        'SAN JUAN BAUTISTA DE ÑEEMBUCÚ', 'TACUARAS', 'VILLA FRANCA',
        'VILLA OLIVA', 'VILLALBÍN',
    },
    'AMAMBAY': {
        'PEDRO JUAN CABALLERO', 'BELLA VISTA NORTE', 'CAPITÁN BADO',
        'KARAPAÍ', 'ZANJA PYTÁ', 'CERRO CORÁ',
    },
    'CANINDEYÚ': {
        'SALTO DEL GUAIRÁ', 'CORPUS CHRISTI', 'CURUGUATY',
        'GENERAL FRANCISCO CABALLERO ÁLVAREZ', 'ITANARÁ', 'KATUETÉ',
        'LA PALOMA', 'NUEVA ESPERANZA', 'VILLA YGATIMÍ', 'YASY CAÑY',
        'YPEJHÚ', 'LAUREL', 'PUERTO ADELA', 'MARACANÁ', 'YBY PYTA',
        'YBYRAROBANÁ',
    },
    'PDTE. HAYES': {
        'VILLA HAYES', 'BENJAMÍN ACEVAL', 'DOCTOR JOSÉ FALCÓN',
        'GENERAL BRUGUEZ', 'NANAWA', 'PUERTO PINASCO',
        'TENIENTE IRALA FERNÁNDEZ', 'NUEVA ASUNCIÓN', 'CAMPO ACEVAL',
        'TENIENTE ESTEBAN MARTÍNEZ',
    },
    'ALTO PARAGUAY': {
        'FUERTE OLIMPO', 'BAHÍA NEGRA', 'CAPITÁN CARMELO PERALTA',
        'PUERTO CASADO',
    },
    'BOQUERON': {
        'FILADELFIA', 'LOMA PLATA', 'MARISCAL ESTIGARRIBIA', 'BOQUERÓN',
    },
}

# Valor centinela que el BI utiliza cuando un dato geográfico no fue informado.
SIN_ESPECIFICAR = 'SIN ESPECIFICAR'

# Tipologías de evento que el formulario permite elegir. Todas existen ya en
# `dim_evento`, de modo que no requieren estandarización posterior.
EVENTOS = (
    'C.I.D.H.',
    'COVID',
    'EXTREMA VULNERABILIDAD',
    'INCENDIO',
    'INUNDACION',
    'OLLA POPULAR',
    "OPERATIVO JAHO'I",
    'OTROS',
    'SEQUIA',
    'TORMENTA SEVERA',
)

# Valor que el pipeline histórico asignaba cuando no lograba inferir el evento.
# Se acepta en la importación porque existe en `dim_evento`, pero el formulario
# no lo ofrece: quien carga en territorio conoce el motivo de la asistencia.
EVENTO_NO_INFORMADO = 'SIN EVENTO'

# Conjunto completo admitido en la tabla, incluyendo el aporte del histórico.
EVENTOS_ADMITIDOS = (*EVENTOS, EVENTO_NO_INFORMADO)

# Evento cuya asistencia se imputa a `kit_sentencia` en la tabla de hechos;
# el resto de los eventos se imputa a `kit_evento`.
EVENTO_SENTENCIA = 'C.I.D.H.'

MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre',
    11: 'Noviembre', 12: 'Diciembre',
}

_ESPACIOS_MULTIPLES = re.compile(r'\s+')


def normalizar_texto(valor):
    """Normaliza un texto libre al formato que espera el Data Warehouse.

    Recorta espacios, colapsa espacios internos y convierte a mayúsculas. No
    elimina tildes porque el catálogo oficial las conserva.
    """
    if valor is None:
        return ''
    texto = unicodedata.normalize('NFC', str(valor)).strip().upper()
    return _ESPACIOS_MULTIPLES.sub(' ', texto)


def orden_de_departamento(departamento):
    """Devuelve el orden oficial del departamento, o 0 si no está catalogado."""
    return DEPARTAMENTO_ORDEN.get(normalizar_texto(departamento), 0)


def distritos_de(departamento):
    """Devuelve el conjunto de distritos válidos para un departamento."""
    return DISTRITOS_POR_DEPARTAMENTO.get(normalizar_texto(departamento), set())
