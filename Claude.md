# CLAUDE.md

Pautas de comportamiento para reducir errores comunes de programación con LLMs. Combinar con las instrucciones específicas del proyecto según haga falta.

**Compensación:** Estas pautas priorizan la cautela por sobre la velocidad. Para tareas triviales, usá el criterio.

## 1. Pensar antes de programar

**No asumas. No ocultes la confusión. Explicitá las compensaciones.**

Antes de implementar:
- Enunciá tus supuestos de forma explícita. Si hay incertidumbre, preguntá.
- Si existen varias interpretaciones, presentalas — no elijas una en silencio.
- Si existe un enfoque más simple, decilo. Cuestioná cuando esté justificado.
- Si algo no está claro, pará. Nombrá qué te resulta confuso. Preguntá.

## 2. Primero la simplicidad

**El mínimo código que resuelva el problema. Nada especulativo.**

- Ninguna funcionalidad más allá de lo pedido.
- Ninguna abstracción para código de un solo uso.
- Ninguna "flexibilidad" ni "configurabilidad" que no se haya solicitado.
- Ningún manejo de errores para escenarios imposibles.
- Si escribís 200 líneas y podrían ser 50, reescribilo.

Preguntate: "¿Un ingeniero senior diría que esto está sobrecomplicado?" Si la respuesta es sí, simplificá.

## 3. Cambios quirúrgicos

**Tocá solo lo que sea necesario. Limpiá solo tu propio desorden.**

Al editar código existente:
- No "mejores" el código, los comentarios ni el formato de alrededor.
- No refactorices cosas que no están rotas.
- Respetá el estilo existente, aunque vos lo harías distinto.
- Si notás código muerto no relacionado, mencionalo — no lo borres.

Cuando tus cambios dejen elementos huérfanos:
- Eliminá los imports/variables/funciones que TUS cambios dejaron sin uso.
- No elimines código muerto preexistente salvo que te lo pidan.

La prueba: cada línea modificada debe poder trazarse directamente al pedido del usuario.

## 4. Ejecución guiada por objetivos

**Definí criterios de éxito. Iterá hasta verificar.**

Transformá las tareas en objetivos verificables:
- "Agregar validación" → "Escribir tests para entradas inválidas y luego hacer que pasen"
- "Arreglar el bug" → "Escribir un test que lo reproduzca y luego hacer que pase"
- "Refactorizar X" → "Asegurar que los tests pasen antes y después"

Para tareas de varios pasos, enunciá un plan breve:
```
1. [Paso] → verificar: [chequeo]
2. [Paso] → verificar: [chequeo]
3. [Paso] → verificar: [chequeo]
```

Criterios de éxito sólidos te permiten iterar de forma independiente. Criterios débiles ("que funcione") requieren aclaraciones constantes.

## 5. Convenciones de commits

**Commits en español, semánticos y sin coautoría.**

- Escribí los mensajes de commit en español.
- Seguí el formato de commits semánticos (Conventional Commits): `tipo(alcance): descripción`, con la descripción en español. Ejemplos:
  - `feat(rag): agregar rechazo cuando el fragmento no tiene URL`
  - `fix(scraper): continuar la corrida cuando una fuente devuelve error`
  - `test(vectorstore): cubrir el ordenamiento por relevancia`
  - `docs(spec): acotar el alcance a UTN-FRBA Sistemas`
  - `chore(config): cargar fuentes WEB de FRBA en sources.yaml`
- Tipos habituales: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `style`, `perf`.
- La primera línea en imperativo y concisa; si hace falta más detalle, dejá una línea en blanco y agregá el cuerpo.
- **No agregues coautoría al commit.** No incluyas líneas `Co-authored-by:` ni ninguna atribución a Claude, la IA o herramientas. El commit va a nombre de quien lo hace, sin colaboradores añadidos.

---

**Estas pautas están funcionando si:** hay menos cambios innecesarios en los diffs, menos reescrituras por sobrecomplicación, y las preguntas aclaratorias llegan antes de implementar en vez de después de los errores.