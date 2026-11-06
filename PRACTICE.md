# Guía práctica / Practice guide

Ejercicios **offline** con estados abstractos de una página. No hay
syscalls, `/proc`, mmap ni kernel. *English summary at the end.*

## Comandos locales

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m dirtycow_model trace --version 6b25e21
python3 scripts/gen_results.py /tmp/out && diff -r results /tmp/out
```

## Ejercicios graduados

**Nivel 1: el bucle GUP.** Ejecuta `trace --version 6b25e21` sin zap y
anota la secuencia de fases.
Comprobación: `written` = `C`; las fases son follow, fault, follow,
fault, follow y write.

**Nivel 2: el truco de FOLL_WRITE.** ¿En qué paso desaparece `WRITE` de
los flags y por qué?
Comprobación: tras el fallo sobre `Crd`, `do_wp_page` devuelve
`VM_FAULT_WRITE` y el VMA no tiene `VM_WRITE` (gup.c l.414-415).

**Nivel 3: el zap.** Usa `--zap-after 3`.
Comprobación: `written` = `P`, con un fallo con `flags=FORCE pte=none`
después del zap.

**Nivel 4: el fix.** Repite con `--version 19be0eaffa3a --zap-after 3`.
Comprobación: `written` = `C`, porque `FOLL_COW` se activa y `FOLL_WRITE`
se mantiene.

**Nivel 5: can_follow_write_pte.** ¿Por qué el fix no acepta el pte `Prc`
aunque haya `FOLL_COW`?
Comprobación: P está limpio, y la condición exige `pte_dirty`
(gup.c 19be0eaffa3a l.70).

**Nivel 6: explorar.** Ejecuta `explore --version 6b25e21 --zaps 1`.
Comprobación: `violating` = 1 de 13 schedules y `unfinished` = 0.

**Nivel 7: control VM_WRITE.** Añade `--vm-write --zaps 3`.
Comprobación: `violating` = 0 incluso en 6b25e21.

**Nivel 8: posiciones del zap.** En `results/zap_position.csv`, ¿qué
posiciones dan P?
Comprobación: solo 6b25e21 con zap tras el paso 3 (pte sin poblar) o tras
el paso 1 (pte poblado con P). Ninguna en 19be0eaffa3a.

## English summary

Eight levels: the GUP retry loop, where `FOLL_WRITE` is dropped, the
one-zap race, the `FOLL_COW` fix, why a clean P is refused, the
exhaustive explorer, the `VM_WRITE` control, and the zap positions that
lead to P.
