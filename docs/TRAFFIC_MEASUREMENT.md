# Medicion de trafico

Objetivo: saber que enlaces ayudan a mover lectores hacia `https://pulsotechdiario.blogspot.com/` y cuales conviene reforzar.

## Enlaces con UTM

El sitio usa parametros UTM solo en enlaces de distribucion y descubrimiento. El RSS de Blogger se mantiene limpio.

| Origen | Ejemplo de UTM | Uso |
| --- | --- | --- |
| GitHub Pages principal | `utm_source=github_pages&utm_medium=referral&utm_campaign=traffic_hub` | Clics desde la portada estatica hacia Blogger. |
| Hubs de temas | `utm_source=github_pages&utm_medium=referral&utm_campaign=topic_hub` | Clics desde paginas de IA, ciberseguridad y chips. |
| Kit de compartir | `utm_source=share_pack&utm_medium=social&utm_campaign=daily_share` | Enlaces listos para X, LinkedIn, WhatsApp y Telegram. |
| Archivo puente | `utm_source=github_pages&utm_medium=archive&utm_campaign=blogger_bridge` | Clics desde el archivo publico de entradas reales. |

## Donde revisar

1. En Blogger, abrir **Estadisticas** y revisar entradas con mas vistas y fuentes de trafico.
2. En Google Search Console, revisar rendimiento de:
   - `https://pulsotechdiario.blogspot.com/`
   - `https://elianguitarra.github.io/pulso-tech-diario/`
3. Buscar señales de estos parametros en URLs o referrers:
   - `utm_source=github_pages`
   - `utm_source=share_pack`
   - `utm_campaign=traffic_hub`
   - `utm_campaign=daily_share`
   - `utm_campaign=blogger_bridge`

## Lectura semanal

Cada semana anota:

- Entradas con mas vistas.
- Enlaces UTM que aparecen en referrers o URLs visitadas.
- Temas que reciben impresiones en Search Console.
- Titulos con bajo CTR para reescribirlos.
- Guias evergreen que merecen una segunda parte.

La meta inicial no es monetizacion inmediata. La meta inicial es detectar una fuente repetible de lectores: busqueda, archivo, kit social o portada estatica.
