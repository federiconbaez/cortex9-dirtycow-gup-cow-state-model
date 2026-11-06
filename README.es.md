# cortex9-dirtycow-gup-cow-state-model

Modelo offline de estados de la carrera entre `__get_user_pages()` y
`madvise(MADV_DONTNEED)` (CVE-2016-5195, "Dirty COW").

- **6b25e21:** antes del fix, se descarta `FOLL_WRITE` tras romper el COW.
- **19be0eaffa3a:** el fix usa `FOLL_COW` y `can_follow_write_pte()`, que
  exige un pte sucio.

**No hay syscalls, `/proc`, mmap ni kernel.** Solo hay estados
abstractos de una página:

- `P`, la página de caché del archivo;
- `C`, la copia anónima;
- `none`.

El explorador recorre todos los entrelazados de los pasos del modelo entre un llamador GUP
`FOLL_WRITE|FOLL_FORCE` contra k zaps. El invariante es que nunca se
escribe P.

**Alcance de la exploración.** El explorador enumera todos los entrelazados *de este programa finito del modelo* (sus pasos atómicos, cotas y elecciones). No dice nada de entrelazados del código real fuera del modelo, y un 0 tras el fix es una propiedad del modelo, no una prueba de que el fix real sea seguro en todo schedule.

Resultados:

- **6b25e21:** hay contraejemplo cuando el zap ocurre justo después del
  fallo que devolvió `VM_FAULT_WRITE`. Entonces el siguiente fallo es de
  lectura y mapea P.
- **19be0eaffa3a:** 0 violaciones en toda la grilla.
- **Control:** con `VM_WRITE` en el VMA no se descarta `FOLL_WRITE`, y no
  hay violación ni siquiera antes del fix.

Para el detalle, consulta README.md, SOURCES.md, LIMITATIONS.md y
PRACTICE.md.

Licencia: Apache-2.0.
