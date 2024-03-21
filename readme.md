# EDD CLI

CLI que permite ejecutar testcases tanto localmente como en un servidor.

## Instalación

Requiere [poetry](https://python-poetry.org/). Probado con Python 3.11 y superior.

Por ahora, requiere de Docker para ejecutar los test cases.

```bash
# Instalar dependencias y este paquete
poetry install

# Entrar al entorno virtual
poetry shell

# Ir al directorio donde se va a ejecutar
# Si se ejecuta localmente, los test deben encontrase en ./tests

# Usar el CLI
edd --help
# edd run    # para ejecutar localmente
# edd server # para ejecutar el servidor (ver /docs)
```

## Resolución de problemas

### Se queda pegado o con errores

Puede ocurrir un problema inicialmente, al descargar la imagen o ejecutar el contenedor por primera vez.
Se puede resolver eliminar el cache y corriéndolo nuevamente.

```sh
rm -rf .edd-cache
```

## Arquitectura

- El servidor no asume la responsabilidad de la cola de ejecución.
- El servidor no guarda resultados, pero si cachea ejecuciones y repositorios.
- El servidor expone los tests correctamente subidos.
- Se dispone `/docs` interactivos para probar manualmente el servidor.

### Test cases

Se asume que los tests cases se encontrarán en `./tests` tanto localmente como en el servidor.
Aunque en el caso de los test cases locales, la carpeta corresponde a los test propios de una tarea en particular, mientras que en el servidor, la carpeta corresponde a los test cases de todas las tareas.

```sh
# server
tests
├── T2-2022-2
│   ├── parte-1
│   │   ├── setup.json
│   │   ├── {archivos de setup}
│   │   ├── test-1
│   │   │   ├── test.json
│   │   │   └── {archivos de test}
...

# local
tests  # sería T2-2022-2 en el servidor
├── parte-1
│   ├── setup.json
│   ├── {archivos de setup}
│   ├── test-1
│   │   ├── test.json
│   │   └── {archivos de test}
...
```

Hay 2 archivos especiales, `setup.json` y `test.json`. Ambos tienen el mismo formato. `setup.json` representa que se debe correr antes de cada test, y `test.json` representa el test en sí.

```jsonc
{
  "name": "Nombre del test",
  // `steps` es un arreglo con pasos a seguir, como en setups de CI/CD.
  // El entorno inicial es el repositorio del alumno, y dependiendo de
  // `include`, `require`, y `command`, serán los archivos que generará.
  "steps": {
    // `include` y `require` son para copiar
    // archivos en la etapa que le corresponden.
    // `include` añade archivos desde los archivos del test.
    // `require` añade archivos desde los archivos del repositorio
    //           o de la etapa pasada.
    // Ambos siguen el mismo formato.
    // - como string si el archivo se copia tal cual
    // - como objeto si se copia a otro nombre o ubicación
    "include": ["archivo-4", { "source": "archivo-5", "target": "archivo-6" }],
    "require": ["archivo-1", { "source": "archivo-2", "target": "archivo-3" }],
    // `command` es para ejecutar comandos en el entorno.
    "command": ["program", "arg1", "arg2"],
    // `time-it` indica si se debe medir el tiempo de ejecución. Por defecto es `false`.
    "time-it": true
  }
}
```

### Entornos de ejecución

Con lo indicado en los test cases, se creará un directorio temporal que será el entorno de ejecución, que es único por contenido de archivos e instrucciones a ejecutar. Es decir, a menos que se tengan exactamente los mismos archivos y las mismas instrucciones, se creará un directorio distinto para cada test.

Estos entornos se guardan en `./.edd-cache` localmente y `$(TEMP)/edd-cache` en el servidor.
Como son carpetas únicas cuyo nombre depende del contenido y la configuración del test, se pueden cachear y reutilizar en siguientes utilizaciones. Esto es útil cuando una tarea tiene múltiples partes, y solo se modificó una.

Por ahora no se eliminan automáticamente, así que hay que tener cuidado de que crezcan más de lo esperado. Se expone un endpoint para eliminarlos en el servidor.

### Salida, stdout y tiempo

El entorno almacenará el resultado final del directorio de ejecución. Además, almacenará el stdout y tiempo de ejecución de cada test, con el formato `.{nombre}.{nombre-carpeta}`.

### Autenticación

Se utiliza el modelo de autentificación `HTTPBearer`, obteniendo la variable de entorno `SECRET` y validando que el token del header `Authorization` sea igual a `Bearer ${SECRET}`.
