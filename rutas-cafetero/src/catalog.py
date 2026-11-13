"""Catálogo de 40 lugares del Quindío.

ADVERTENCIA: las coordenadas y las duraciones son APROXIMADAS (borrador). El grupo debe verificarlas en un
mapa y justificar las duraciones con una fuente o con un criterio propio (sección 4 del enunciado).
Las fincas y los centros de acopio son marcadores de posición ('ejemplo'); el grupo debe reemplazarlos
por lugares reales."""
import csv

# id, nombre, municipio, categoria, lat, lon, visita_min (solo atractivos)
PLACES = [
 # --- Cabeceras municipales (plaza principal) ---
 ("C01", "Armenia (Plaza de Bolívar)", "Armenia", "Cabecera", 4.5339, -75.6811, None),
 ("C02", "Buenavista", "Buenavista", "Cabecera", 4.3597, -75.7422, None),
 ("C03", "Calarcá", "Calarcá", "Cabecera", 4.5292, -75.6431, None),
 ("C04", "Circasia", "Circasia", "Cabecera", 4.6178, -75.6358, None),
 ("C05", "Córdoba", "Córdoba", "Cabecera", 4.3917, -75.6869, None),
 ("C06", "Filandia", "Filandia", "Cabecera", 4.6736, -75.6586, None),
 ("C07", "Génova", "Génova", "Cabecera", 4.2058, -75.7894, None),
 ("C08", "La Tebaida", "La Tebaida", "Cabecera", 4.4528, -75.7897, None),
 ("C09", "Montenegro", "Montenegro", "Cabecera", 4.5667, -75.7503, None),
 ("C10", "Pijao", "Pijao", "Cabecera", 4.3322, -75.7061, None),
 ("C11", "Quimbaya", "Quimbaya", "Cabecera", 4.6247, -75.7647, None),
 ("C12", "Salento", "Salento", "Cabecera", 4.6372, -75.5708, None),
 # --- Atractivos turísticos (visita en minutos: criterio del grupo, a justificar) ---
 ("A01", "Parque Nacional del Café", "Montenegro", "Atractivo", 4.5400, -75.7740, 240),
 ("A02", "PANACA", "Quimbaya", "Atractivo", 4.5950, -75.7950, 240),
 ("A03", "Valle de Cocora", "Salento", "Atractivo", 4.6369, -75.4851, 180),
 ("A04", "Jardín Botánico del Quindío", "Calarcá", "Atractivo", 4.5700, -75.7080, 120),
 ("A05", "Museo del Oro Quimbaya", "Armenia", "Atractivo", 4.5575, -75.6683, 90),
 ("A06", "Mirador de Filandia (Colina Iluminada)", "Filandia", "Atractivo", 4.6745, -75.6590, 45),
 ("A07", "Parque Los Arrieros", "Circasia", "Atractivo", 4.6150, -75.6300, 60),
 ("A08", "Mirador Alto de la Cruz", "Salento", "Atractivo", 4.6392, -75.5688, 45),
 ("A09", "Calle Real de Salento", "Salento", "Atractivo", 4.6385, -75.5710, 75),
 ("A10", "Mariposario del Quindío", "Calarcá", "Atractivo", 4.5320, -75.6200, 75),
 ("A11", "Parque de la Vida", "Armenia", "Atractivo", 4.5500, -75.6650, 60),
 ("A12", "Reserva Bremen - La Popa", "Filandia", "Atractivo", 4.7000, -75.6350, 150),
 ("A13", "Mirador de Buenavista", "Buenavista", "Atractivo", 4.3600, -75.7410, 45),
 ("A14", "Casco histórico de Pijao (Cittaslow)", "Pijao", "Atractivo", 4.3330, -75.7050, 60),
 ("A15", "Mirador de Génova", "Génova", "Atractivo", 4.2100, -75.7850, 45),
 # --- Fincas / hoteles rurales (marcadores de posición) ---
 ("F01", "Finca cafetera (ejemplo) - Salento", "Salento", "Finca/Hotel", 4.6150, -75.5900, None),
 ("F02", "Finca cafetera (ejemplo) - Filandia", "Filandia", "Finca/Hotel", 4.6500, -75.6900, None),
 ("F03", "Finca cafetera (ejemplo) - Montenegro", "Montenegro", "Finca/Hotel", 4.5500, -75.7300, None),
 ("F04", "Finca cafetera (ejemplo) - Quimbaya", "Quimbaya", "Finca/Hotel", 4.6000, -75.7900, None),
 ("F05", "Finca cafetera (ejemplo) - Calarcá", "Calarcá", "Finca/Hotel", 4.5000, -75.6200, None),
 ("F06", "Finca cafetera (ejemplo) - Circasia", "Circasia", "Finca/Hotel", 4.6000, -75.6000, None),
 ("F07", "Finca cafetera (ejemplo) - Armenia", "Armenia", "Finca/Hotel", 4.5100, -75.7100, None),
 ("F08", "Finca cafetera (ejemplo) - Pijao", "Pijao", "Finca/Hotel", 4.3150, -75.7250, None),
 # --- Centros de acopio / trilladoras (marcadores de posición) ---
 ("T01", "Centro de acopio (ejemplo) - Armenia", "Armenia", "Acopio", 4.5200, -75.6900, None),
 ("T02", "Centro de acopio (ejemplo) - Calarcá", "Calarcá", "Acopio", 4.5180, -75.6500, None),
 ("T03", "Trilladora (ejemplo) - Montenegro", "Montenegro", "Acopio", 4.5700, -75.7500, None),
 ("T04", "Centro de acopio (ejemplo) - Génova", "Génova", "Acopio", 4.2150, -75.7800, None),
 ("T05", "Centro de acopio (ejemplo) - La Tebaida", "La Tebaida", "Acopio", 4.4400, -75.7800, None),
]

# Municipios vecinos (aproximado; sirve para escoger pares "cercanos" en el R2)
NEIGHBORS = {frozenset(p) for p in [
 ("Armenia", "Calarcá"), ("Armenia", "Circasia"), ("Armenia", "Montenegro"), ("Armenia", "La Tebaida"),
 ("Armenia", "Salento"), ("Calarcá", "Salento"), ("Calarcá", "Córdoba"), ("Calarcá", "La Tebaida"),
 ("Circasia", "Filandia"), ("Circasia", "Salento"), ("Circasia", "Quimbaya"), ("Circasia", "Montenegro"),
 ("Filandia", "Quimbaya"), ("Filandia", "Salento"), ("Montenegro", "Quimbaya"), ("Montenegro", "La Tebaida"),
 ("Córdoba", "Pijao"), ("Córdoba", "Buenavista"), ("Pijao", "Buenavista"), ("Pijao", "Génova"),
 ("Buenavista", "Génova"), ("Córdoba", "Génova")]}

START_ID = "C01"
COLS = ["id", "nombre", "municipio", "categoria", "lat", "lon", "visita_min"]


def load():
    return [dict(zip(COLS, p)) for p in PLACES]


def save_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for p in PLACES:
            w.writerow(["" if v is None else v for v in p])


def are_close(a, b):
    return a["municipio"] == b["municipio"] or frozenset((a["municipio"], b["municipio"])) in NEIGHBORS
