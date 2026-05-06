# Auditoria de PL2 - `Lets_go_SHOPing`

Fecha de auditoria: 2026-05-02  
Repositorio auditado: `PL2/Lets_go_SHOPing`  
Base visible: `git rev-parse --short HEAD` -> `121050a`  
Estado del arbol durante la auditoria: **dirty**

Ficheros que ya estaban modificados localmente antes de esta actualizacion de la auditoria:
- `.gitignore`
- `LICENSE`
- `README.md`
- `domains/basic/domain.jshop`
- `domains/advanced/domain.jshop`
- `scripts/scenarios_lib.py`

## Veredicto ejecutivo

**Resultado corto:** la practica **funciona tecnicamente** y la comparativa automatizada del ejercicio 1.1 ya esta alineada con **Practica 1, ejercicio 1.2 (FF)**, pero **la entrega completa sigue sin estar cerrada** frente al enunciado.

Lo verificado como correcto en el estado actual:
- El dominio basico genera problemas y JSHOP2 encuentra plan.
- El dominio avanzado genera problemas y JSHOP2 encuentra plan.
- La compatibilidad con la estructura del profesor funciona.
- La suite avanzada obligatoria pasa completa: `12/12` escenarios.
- El benchmark del dominio basico genera `CSV`, `MD` y `PNG` cuando se ejecuta con un Python que tenga `matplotlib`.
- La comparativa de 1.1 usa por defecto la baseline correcta de `PL1` ejercicio `1.2`:
  - `references/pl1_part1_ex12_ff_baseline.csv`
  - etiqueta `PL1 Exercise 1.2 (FF)`
  - metrica `ff_time_s`
- Existen pruebas especificas para la baseline y para el benchmark:
  - `tests/test_benchmark_basic.py`

Lo que impide darla por cerrada como entrega:
- No hay paquete de entrega completo con **memoria PDF**, **video de defensa** ni **ZIP final**.
- La bateria automatica de `unittest` sigue protegiendo solo `3` escenarios avanzados en `tests/test_smoke.py`, aunque la suite completa si pasa cuando se ejecuta `scripts/run_scenarios.py`.

## Metodologia y entorno

Entorno realmente usado en esta actualizacion:
- `python3 --version` -> `Python 3.12.3`
- `java -version` -> `OpenJDK 21.0.10`
- `javac -version` -> `javac 21.0.10`

Observacion de entorno:
- Con `python3` del sistema, `import matplotlib` falla.
- Para comprobar la generacion real de la imagen del benchmark se uso `../../PL1/venv/bin/python`, donde `matplotlib` si esta disponible.

## Evidencia ejecutada

### 1. Tests automatizados

Comandos ejecutados:

```bash
python3 -m unittest tests.test_smoke -v
python3 -m unittest tests.test_benchmark_basic -v
```

Resultado:
- `tests.test_smoke` paso completo: `3 tests`, `OK`.
- `tests.test_benchmark_basic` paso completo: `5 tests`, `OK`.

Interpretacion:
- El smoke test confirma el flujo minimo del dominio basico, tres escenarios avanzados y la compatibilidad con el layout del profesor.
- `tests.test_benchmark_basic` confirma lo que mas habia que corregir en 1.1:
  - carga de baseline FF cruda de PL1
  - carga de baseline FF normalizada
  - compatibilidad manual con baseline BFS legacy
  - ejecucion del benchmark con una baseline FF correcta

### 2. Validacion completa del ejercicio 1.2

Comando ejecutado:

```bash
python3 scripts/run_scenarios.py --suite advanced --results-dir .cache/audit_scenarios_refresh
```

Resultado:
- Pasan los `12` escenarios de `scripts/scenarios_lib.py`.
- Se genero evidencia por escenario: problema `.jshop`, salida cruda `.stdout.txt` y resultado parseado `.result.json`.
- Resumen consolidado en:
  - `.cache/audit_scenarios_refresh/summary.json`
  - `.cache/audit_scenarios_refresh/summary.md`

Escenarios cubiertos por la suite:
- `s01_no_carrier_loose`
- `s02_single_carrier`
- `s03_mixed_contents_same_carrier`
- `s04_carrier_then_loose_remainder`
- `s05_small_carrier_loads_max`
- `s06_large_carrier_loads_partial`
- `s07_choose_smallest_fitting`
- `s08_choose_largest_if_none_fit`
- `s09_reselect_after_return`
- `s10_serve_highest_need_first`
- `s11_multistop_without_return`
- `s12_combined_regression`

Conclusion tecnica del ejercicio 1.2:
- **La logica avanzada funciona y cubre la lista obligatoria del enunciado en esta auditoria.**

### 3. Benchmark actualizado del ejercicio 1.1

Comando ejecutado:

```bash
../../PL1/venv/bin/python scripts/benchmark_basic.py --min-size 2 --max-size 6 --step 1 --results-dir .cache/audit_bench_ff_with_plot
```

Resultado:
- Se generan correctamente:
  - `.cache/audit_bench_ff_with_plot/benchmark_basic.csv`
  - `.cache/audit_bench_ff_with_plot/benchmark_basic.md`
  - `.cache/audit_bench_ff_with_plot/benchmark_basic.png`
- El `MD` generado identifica correctamente la comparativa:
  - baseline `PL1 Exercise 1.2 (FF)`
  - baseline CSV `references/pl1_part1_ex12_ff_baseline.csv`
  - baseline metric `ff_time_s`

Resumen observado para `size=2..6`:

| size | status | time_used_s | plan_length | baseline_time_s | baseline_plan_length |
| --- | --- | --- | --- | --- | --- |
| 2 | solved | 0.053000 | 6 | 0.000000 | 7 |
| 3 | solved | 0.025000 | 10 | 0.000000 | 11 |
| 4 | solved | 0.029000 | 14 | 0.000000 | 14 |
| 5 | solved | 0.103000 | 17 | 0.000000 | 17 |
| 6 | solved | 0.025000 | 19 | 0.000000 | 22 |

Lectura tecnica:
- El benchmark esta **bien implementado y bien conectado** con la baseline correcta.
- Los resultados para tamanos pequenos no muestran a JSHOP2 sistematicamente por debajo de FF en esta maquina.
- Esto **no es un fallo funcional del benchmark**, pero si un punto que la memoria final deberia explicar al responder la reflexion pedida en 1.1.

### 4. Exportacion de baseline FF

Comando ejecutado:

```bash
python3 scripts/export_pl1_ff_baseline.py --source-csv ../../PL1/Planning-practice/parte1/results/benchmark_ff_2_to_60.csv --output .cache/audit_exported_ff_baseline_refresh.csv
```

Resultado:
- El script imprime correctamente:
  - `Source CSV: ../../PL1/Planning-practice/parte1/results/benchmark_ff_2_to_60.csv`
  - `Output CSV: .cache/audit_exported_ff_baseline_refresh.csv`
- El CSV normalizado generado contiene las columnas esperadas:
  - `size`
  - `status`
  - `ff_time_s`
  - `wall_time_s`
  - `plan_length`

Conclusion:
- La baseline vendorizada del repositorio ya no depende de una conversion manual opaca.

### 5. Comprobacion de entregables finales

Comando ejecutado:

```bash
find . -maxdepth 2 \( -name '*.pdf' -o -name '*.mp4' -o -name '*.zip' \) | sort
```

Resultado:
- No se encontro ningun `*.pdf`
- No se encontro ningun `*.mp4`
- No se encontro ningun `*.zip`

## Correcciones verificadas respecto a la revision anterior

La incidencia mas importante abierta en la auditoria anterior ya no sigue abierta:

- `scripts/benchmark_basic.py` usa por defecto `references/pl1_part1_ex12_ff_baseline.csv`
- el benchmark admite:
  - CSV FF crudo de PL1 con `plan_steps`
  - CSV FF normalizado con `plan_length`
  - CSV BFS legacy solo como compatibilidad manual
- el `CSV` del benchmark ya no usa nombres acoplados a BFS:
  - ahora usa `baseline_time_s`
  - ahora usa `baseline_plan_length`
- el `MD` del benchmark y la grafica identifican la baseline como `PL1 Exercise 1.2 (FF)`
- existe `scripts/export_pl1_ff_baseline.py` para regenerar la baseline de referencia
- existe `tests/test_benchmark_basic.py` para proteger este comportamiento

## Hallazgos abiertos

### H1. Falta la entrega completa exigida por el enunciado

**Severidad:** alta  
**Estado:** pendiente

El enunciado exige que el ZIP final incluya:
- memoria en PDF
- video de defensa
- codigo fuente, tests y soluciones generadas para las situaciones de 1.2

Referencia:
- `Practica_2_Planificacion_jerarquica_con_SHOP_English.md:14-24`

Sin embargo, en el repositorio auditado no aparecen esos entregables finales empaquetados.

Impacto:
- **Como proyecto ejecutable esta bien.**
- **Como entrega final frente al enunciado no esta completa.**

### H2. Los `smoke tests` no cubren toda la bateria obligatoria del dominio avanzado

**Severidad:** media  
**Estado:** mejora recomendada

La suite obligatoria real contiene `12` escenarios:
- `scripts/scenarios_lib.py`

Pero los tests automaticos ligeros de `unittest` solo ejercitan `3` de ellos:
- `tests/test_smoke.py`

Escenarios incluidos en `test_smoke.py`:
- `s02_single_carrier`
- `s04_carrier_then_loose_remainder`
- `s11_multistop_without_return`

Impacto:
- No es un fallo funcional inmediato, porque la suite completa **si paso** en esta auditoria.
- Si el dominio cambia mas adelante, parte de la logica obligatoria podria romperse sin que el smoke test lo detecte.

Recomendacion:
- Mantener el smoke test ligero si se quiere, pero anadir una ejecucion automatica de la suite completa al checklist de entrega o a CI.

## Aspectos verificados como correctos

### Ejercicio 1.1

Correcto:
- Existe dominio SHOP2 basico: `domains/basic/domain.jshop`
- Existe generador especifico: `scripts/generate_basic_shop.py`
- Existe benchmark reproducible: `scripts/benchmark_basic.py`
- Se generan problemas, se resuelven y se producen salidas `CSV`, `MD` y `PNG`
- La comparativa automatica esta ya alineada con la referencia correcta de `PL1` ejercicio `1.2`

Pendiente de cierre documental:
- llevar la grafica y la comparativa al `PDF` final
- escribir la discusion pedida sobre crecimiento temporal y HTN frente a planificacion clasica

### Ejercicio 1.2

Correcto:
- Existe dominio avanzado con fluentes y costes de viaje: `domains/advanced/domain.jshop`
- Existe generador aleatorio avanzado: `scripts/generate_advanced_shop.py`
- Existe suite determinista de validacion: `scripts/run_scenarios.py`
- La suite completa pasa en esta auditoria

Cobertura funcional confirmada:
- sin transportadores
- un solo transportador
- mezcla de contenidos en un mismo transportador
- resto suelto tras usar transportador
- carga maxima si el transportador no llega
- carga parcial si el transportador sobra
- eleccion del menor suficiente
- eleccion del mayor insuficiente
- reeleccion tras volver al deposito
- prioridad a la localizacion con mayor necesidad
- viaje multi-parada sin volver al deposito

Pendiente de cierre documental:
- empaquetar las soluciones generadas como parte de la entrega final
- explicar en la memoria y en el video como cada situacion queda demostrada

## Limitaciones y observaciones de entorno

- `python3` del sistema no trae `matplotlib`, asi que el comando del benchmark no genera `PNG` en ese entorno base.
- Esto **no es un bug del codigo**, porque el propio `README.md` lo documenta como dependencia opcional.
- La imagen se pudo generar correctamente con otro Python ya presente en el workspace.

## Conclusion final

### Estado tecnico

**Aprobado.**  
El proyecto es ejecutable, los dos dominios funcionan, los escenarios avanzados pasan y el benchmark produce sus artefactos con la comparativa correcta frente a `PL1` ejercicio `1.2`.

### Estado como entrega completa

**No cerrado.**  
Faltan elementos obligatorios de entrega y conviene ampliar la cobertura automatica ligera para no depender solo de `3` escenarios avanzados en `unittest`.

## Recomendaciones finales

1. Preparar la entrega real con:
   - memoria en PDF
   - video de defensa
   - paquete final con codigo y soluciones generadas
2. Llevar al PDF final la grafica y la discusion del benchmark de 1.1, usando ya la baseline correcta de `PL1` ejercicio `1.2`.
3. Mantener `scripts/run_scenarios.py` como prueba fuerte de 1.2 y ampliar la automatizacion ligera para que no dependa solo de `3` escenarios en `tests/test_smoke.py`.
