# TOA original: auditoría y primera ejecución real

Validación local del 26 de octubre de 2026, rama `feature/toa-baseline`,
Python **3.12.3** en `.venv`. No se hicieron commits ni push.

Se ejecutó **un experimento independiente** mediante `Scripts/poblarDB.py`
y `main.py`; el análisis se ejecutó mediante `Scripts/analisis.py`.
Los resultados provienen del CSV almacenado como BLOB en `iteraciones`
y de la fila de `resultados` de la base del framework.

## Auditoría matemática

Referencia primaria: Dehghani y Trojovský (2021),
[Teamwork Optimization Algorithm](https://www.mdpi.com/1424-8220/21/13/4567),
[texto en PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8271451/),
ecuaciones (3)–(11) y algoritmo 1.

La implementación inicial de `src/metaheuristics/Codes/TOA.py` coincide
con las tres etapas y no requirió cambios en sus operaciones matemáticas:

| Operación | Comprobación |
| --- | --- |
| Supervisor, ec. 3 | Copia del individuo de menor fitness al comenzar cada generación. Permanece fijo durante esa generación. |
| Etapa 1, ec. 4–6 | `x + r*(supervisor - I*x)`, con `I=round(1+r)`. |
| Etapa 2, ec. 7–9 | Media de compañeros cuyo fitness actual es estrictamente menor; se evalúa la función en la media y se usa `sign(f_i-f_media)`. No se sustituye por la media de sus fitness. |
| Etapa 3, ec. 10–11 | `x + (-0.01 + 0.02*r)*x`. |
| Aceptación | En cada etapa se acepta exclusivamente si `score < fitness[i]`; un empate no reemplaza al individuo. |
| Orden | Las tres etapas se completan para cada individuo antes de procesar al siguiente, usando las mejoras ya aceptadas. |

Convenciones existentes conservadas: `r` es escalar por etapa y se comparte
con el cálculo de `I` en esa etapa; el redondeo positivo se implementa como
`floor(1+r+0.5)`. El artículo no detalla por completo el muestreo de cada
aparición de `r`, la reparación de límites ni el caso sin compañeros mejores.
Aquí se omite la etapa 2 cuando su media es indefinida y se usa el recorte
del dominio BEN antes de evaluar, conservando la solución reparada si mejora.
Estas convenciones deben mantenerse o acordarse explícitamente antes de
comparar variantes; no se afirma identidad con una implementación oficial
de los autores que no se haya contrastado.

El promedio de compañeros factibles permanece dentro de los límites del
dominio rectangular. TOA llama a `domain.fo`, que repara y contabiliza cada
evaluación. El adaptador interpreta correctamente `(population, fitness)`
y BEN devuelve estos valores sin reevaluarlos, porque TOA declara `fo` en
`MH_ARG_MAP`. El solver restringe esta implementación a BEN continuo.

## Correcciones y archivos

Los cambios anteriores en `src/metaheuristics/imports.py`,
`src/solver/metaheuristic_adapter.py` y la restricción BEN de
`src/solver/universal_solver.py` se conservaron. También se conservaron
las seis pruebas originales de `tests/test_toa.py` y `.vscode/`.

Cambios realizados durante esta validación:

- `Scripts/poblarDB.py`: import de `Scripts.crearBD` con el nombre real
  de la carpeta; BEN genera una sola combinación sin binarización (`N/A`),
  evitando etiquetas irrelevantes o duplicación por múltiples DS_actions.
- `requirements.txt`: se agregó `psutil>=5.9`, importado por el análisis
  pero ausente de los requisitos. Se instaló todo exclusivamente en `.venv`.
- `src/solver/universal_solver.py`: CSV con 17 cifras significativas para
  fitness y estadísticas pequeñas; antes media y desviación podían quedar
  registradas como cero al usar seis decimales fijos.
- `src/util/log.py`: el resumen entre corridas conserva media y desviación
  del fitness sin redondearlas a tres decimales.
- `src/util/json/experiments_config.json`: solo TOA/BEN/F1, dimensión 30,
  población 20, 50 iteraciones, una corrida, modo `iter`, `max_fe=null`;
  SCP, USCP, KP y mapas caóticos desactivados.
- `src/util/json/analysis.json`: curva de fitness con eje logarítmico.
- `tests/test_toa_integration.py`: tres pruebas adicionales, descritas abajo.
- `TOA_BASELINE.md`: este informe. No se agregó una aplicación ni un script
  de demostración; se utilizó el framework existente.

## Base de datos y reproducibilidad

Antes de inicializar se verificaron la ruta configurada, posibles archivos
SQLite y `OII_DB_PATH`. La base `data/database/resultados.db` **no existía**.
La evidencia está en `outputs/toa_baseline/database_before.json`.
Se inicializó con el mecanismo original y se comprobó que había exactamente
un experimento pendiente y ningún resultado antes de ejecutar `main.py`.
Después se verificó una fila terminada, una fila de resultados y un BLOB de
iteraciones. No se borró ni reinició ninguna base.

El experimento tiene **ID 1 y semilla 1**: el framework utiliza el ID para
sembrar NumPy y `random`. La configuración JSON por sí sola no fija la semilla;
en otra base con IDs anteriores los resultados cambiarán. No volver a
ejecutar `poblarDB.py` sin inspeccionar la cola: agrega experimentos y no
deduplica los ya existentes. `main.py` procesa toda la cola pendiente.

Comandos utilizados desde la raíz, en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_toa*.py' -v
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe Scripts/poblarDB.py
.\.venv\Scripts\python.exe main.py
$env:MPLBACKEND = 'Agg'
.\.venv\Scripts\python.exe Scripts/analisis.py
```

Se guardaron logs, configuración efectiva, versiones instaladas, información
del runtime y una copia SQLite del resultado en `outputs/toa_baseline/`.
`manifest.json` identifica los archivos por SHA-256. La copia no cambia la
base de trabajo. Tanto `outputs/` como la base están ignorados por Git;
deben conservarse aparte si se comparten los resultados.

## Resultados reales: F1 Sphere

Dominio `[-100,100]^30`, óptimo conocido `f(0)=0`.

| Métrica | Valor |
| --- | ---: |
| Mejor fitness inicial | 76797.62323505174 |
| Mejor fitness final | 6.903527019971345e-52 |
| NFE inicial / final | 20 / 3900 |
| Tiempo del solver registrado en BD | 0.420 s |
| Tiempo total de la cola, consola | 1.50 s |
| Suma de tiempos parciales redondeados del CSV | 0.406 s |
| Media del fitness de la población inicial | 103884.6522955028 |
| Desviación de la población inicial (`ddof=0`) | 15797.31062338342 |
| Media del fitness de la población final | 7.970054403642055e-44 |
| Desviación de la población final (`ddof=0`) | 3.4000604706455792e-43 |
| Media del mejor fitness entre corridas (`n=1`) | 6.903527019971345e-52 |
| Desviación entre corridas que reporta el framework (`ddof=0`) | 0.0 |
| Desviación muestral entre corridas (`ddof=1`) | No estimable con una corrida |
| Distancia euclídea de la mejor solución al origen | 2.6274563783194086e-26 |
| Máximo valor absoluto entre sus 30 coordenadas | 1.1746506140638756e-26 |

La solución completa se conserva en `outputs/toa_baseline/best_solution.csv`
y `summary.json`. Se comprobó que tiene 30 coordenadas factibles y que
`sum(x**2)` coincide exactamente con el fitness almacenado en BD.

Los 3900 NFE incluyen 20 iniciales, 1000 propuestas de etapa 1, 1000 de
etapa 3 y 940 pares media/propuesta en etapa 2. Se cuentan también las
evaluaciones de candidatos rechazados. No hay un bloque adicional de
20 reevaluaciones por generación.

La diferencia entre tiempos es esperable: la BD mide el solver completo,
el CSV suma tiempos parciales redondeados, y la consola de la cola incluye
despacho y operaciones de base de datos. El resumen de tiempos del análisis
usa el CSV (0.406 s), no el tiempo de BD (0.420 s).

| Iteración | NFE | Mejor fitness (abreviado) |
| ---: | ---: | ---: |
| 0 | 20 | 7.679762e4 |
| 1 | 98 | 1.363864e3 |
| 5 | 410 | 2.596982e-2 |
| 10 | 796 | 2.070598e-8 |
| 20 | 1574 | 1.726983e-19 |
| 30 | 2352 | 2.750273e-30 |
| 40 | 3124 | 5.728319e-41 |
| 50 | 3900 | 6.903527e-52 |

La trayectoria completa, con 51 filas, está en
`outputs/toa_baseline/TOA_F1_1.csv`. El CSV conserva la precisión del registro.

Curva generada por el análisis original:
`outputs/results/best/BEN/fitness_BEN_F1.pdf`.
También se exportó `outputs/toa_baseline/convergence.png` desde el CSV
persistido para visualizar el mejor fitness y la media de la población.

## Diversidad e interpretación

| Métrica registrada | Inicial | Final |
| --- | ---: | ---: |
| DIV de Hussain | 49.410 | 0.000 |
| Exploración XPL (%) | 100.00 | 0.00 |
| Explotación XPT (%) | 0.00 | 100.00 |
| Entropía normalizada ENT | 0.941453 | 0.491223 |
| Diversidad por dimensión, media | 48.66004742549604 | 1.1997199355706423e-23 |
| Diversidad por dimensión, mínima | 34.51816941533518 | 1.790880752807591e-24 |
| Diversidad por dimensión, máxima | 56.78898597232586 | 2.7145000785059314e-23 |

DIV se redondea a tres decimales dentro de su función original: cero no
significa que los individuos sean idénticos. XPL/XPT dependen de ese DIV
redondeado. La diversidad por dimensión conserva mejor el detalle cercano
al óptimo. La entropía usa histogramas de cuatro intervalos efectivos para
20 individuos; cero es frontera entre intervalos, por lo que pequeños valores
positivos y negativos pueden mantener una entropía cercana a 0.5 aunque la
dispersión sea diminuta.

El framework registra GAP=100 y RDP=0 en esta ejecución. Con óptimo cero,
su GAP relativo al mejor fitness permanece en 100% para cualquier mejor
fitness positivo, y RDP devuelve cero por protección de división por cero.
Esos dos valores no cuantifican el error aquí: usar el fitness absoluto y la
distancia al origen. No se cambiaron las definiciones de estas métricas.

La mejora monótona es coherente con la aceptación estricta del TOA y la
solución se aproxima numéricamente al óptimo de Sphere. Las perturbaciones
multiplicativas favorecen la contracción hacia el origen en esta función.
Esta prueba valida la ejecución local; una sola corrida corta sobre Sphere
no reproduce toda la evaluación del artículo ni establece superioridad o
rendimiento en otras funciones.

## Validación y extensión a F1–F23

**9/9 pruebas aprobadas**: seis originales más ejemplos calculados a mano
para las tres etapas/supervisor fijo, dirección del intercambio en una función
no convexa y prueba del solver real con BEN/NFE/persistencia simulada. Esta
última no abre la base de producción. `pip check` no detectó dependencias
incompatibles. Evidencia: `outputs/toa_baseline/tests.log`.

Para ampliar el estudio falta:

1. Seleccionar F1–F23 clásicas (sin sufijo CEC2017); mantener dimensión 30
   en F1–F13 y las dimensiones específicas ya configuradas para F14–F23:
   2, 4, 2, 2, 2, 3, 6, 4, 4 y 4, respectivamente.
2. Revisar definición, límites y óptimos de cada benchmark frente al artículo
   antes de afirmar reproducción experimental, incluidas funciones estocásticas
   como F7. Dimensionar los presupuestos del estudio y las repeticiones.
3. Acordar semillas explícitas emparejadas para comparar TOA con futuras
   variantes: actualmente dependen de IDs y no se emparejan automáticamente.
4. Usar varias corridas independientes para estimar dispersión y aplicar
   comparaciones estadísticas. Mantener una sola corrida no permite hacerlo.
5. Para comparaciones por NFE, resolver primero el corte exacto del presupuesto:
   el solver sincroniza NFE al terminar cada generación y puede exceder el
   límite `max_fe`. Esto no afecta esta ejecución terminada por iteraciones.
6. Inspeccionar la cola antes de agregar experimentos, conservar este resultado
   y verificar que las herramientas de análisis no mezclen distintas dimensiones
   o presupuestos de una misma función.

Differential Evolution no se implementó en esta fase.
