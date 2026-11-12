# Spec R5 — Aplicación (app/index.html)
- Ruta origen–destino en el mapa con tiempo; envolvente sobre el mapa; itinerario (6–8 atractivos) con Held-Karp y voraz, totales y diferencia; tablas y gráficas R1–R4.
- Un solo archivo, sin servidor. Se regenera con python -m src.build_app.
## Verificación
- Tiempo de la ruta en el navegador = matriz R2 (la app lo muestra). Costo del itinerario = Python.
