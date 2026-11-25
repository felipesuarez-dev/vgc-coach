# VGC Coach

[English](./README.en.md)

VGC Coach es un asistente de coaching para Pokémon VGC (Video Game Championships). Empaqueta la lógica de coaching en *skills* que funcionan dentro de Codex, Claude Code y OpenCode. Le puedes pedir en lenguaje natural que arme un equipo, revise el meta, planifique leads, audite un equipo o analice una replay.

No es una app independiente ni un cliente de ladder. La lógica compartida vive en este repositorio y se distribuye como paquetes generados para cada runtime.

## Estado del proyecto

- Licencia: [Apache-2.0](./LICENSE)
- Fork de [NoahJenkins/vgc-coach](https://github.com/NoahJenkins/vgc-coach)
- Contribuciones: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Seguridad: [SECURITY.md](./SECURITY.md)
- Documentación: [docs/README.md](./docs/README.md)

Este fork mantiene la atribución al proyecto original y añade un stack de fuentes verificado, un flujo de transición de regulación y una skill de team building más estricta.

## Instalación

Los paquetes instalables se generan desde `skills/` y `docs/skills/`. No edites las copias de `plugins/` a mano.

### Codex

```bash
git clone https://github.com/felipesuarez-dev/vgc-coach.git
cd vgc-coach
python3 tools/build_plugins.py build
python3 tools/install_codex_plugin.py
```

Reinicia Codex después de instalar.

### Claude Code

```bash
claude plugin marketplace add felipesuarez-dev/vgc-coach \
  --sparse .claude-plugin plugins
claude plugin install vgc-coach-claude@vgc-coach
```

Verifica con:

```bash
claude plugin details vgc-coach-claude@vgc-coach
```

### OpenCode V1

Agrega el plugin generado en `opencode.json`:

```json
{
  "plugin": ["vgc-coach-opencode@git+https://github.com/felipesuarez-dev/vgc-coach.git"]
}
```

Reinicia OpenCode 1.x después de editar la configuración.

### OpenCode V2, Desktop y Web

OpenCode V2 usa el campo `skills`, no el plugin V1. Clona el repositorio y apunta `skills` al paquete generado:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/vgc-coach/plugins/vgc-coach-opencode/skills"]
}
```

La TUI, la app de escritorio y la interfaz web leen la misma configuración global. V2 recarga la configuración sin reiniciar; usa `/reload` si la lista de skills no se actualiza.

Para abrir la interfaz web:

```bash
opencode pair
```

Abre el enlace que imprime el comando. Si usas un servidor independiente:

```bash
opencode serve --hostname 0.0.0.0 --port 4096
```

La guía completa, incluyendo la verificación por HTTP y la recarga del servidor web, está en [docs/installation.md](./docs/installation.md).

## Fuentes

El contrato de fuentes vive en
[docs/skills/shared/references/live-source-registry.yaml](./docs/skills/shared/references/live-source-registry.yaml)
y se renderiza en
[live-source-map.md](./docs/skills/shared/references/live-source-map.md).

Resumen:

- **Oficial**: regulación de Pokémon HOME, roster oficial, calendario y resultados de Championship Series.
- **Meta de torneo**: infovgc, LabMaus y Limitless.
- **Meta amplio**: PokeStats y Smogon.
- **Sets de apoyo**: Pikalytics, PokeBase y Pokepaste.
- **Eventos y standings**: PokeData.
- **Editorial**: Victory Road.

ChampionsMeta está retirado (HTTP 402, `DEPLOYMENT_DISABLED`). ChampionsLab queda fuera del stack automático porque sus datos viven en el payload RSC de Next.js.

LabMaus omite su certificado intermedio y exige `Origin`/`Referer`. El repositorio incluye un fetcher que completa la cadena TLS, verifica el hostname y fija el fingerprint del certificado. No uses `curl -k` genérico como solución.

Tabla completa, TTLs, fallbacks y resultados del probe: [docs/sources.md](./docs/sources.md).

## Cómo funciona el team building

El flujo es:

```text
regulación + roster oficial
  -> snapshot de meta con fallbacks
  -> cores reales 2/3/4 y 4/5/6
  -> un equipo de seis
  -> legality ledger
  -> benchmarks acotados
  -> spreads battle-ready
  -> playbook derivado de los cores
  -> auditoría de synergy y matchups
  -> export gate
```

Puntos importantes:

- Una recomendación `current-field` necesita regulación, roster, una fuente de torneo y una fuente de uso amplio.
- El roster oficial verifica especies, no objetos, movimientos, habilidades ni mecánicas.
- Los cores 2/3/4 salen de Limitless; LabMaus publica 4/5/6 y no se le inventan 2/3.
- Los benchmarks y los spreads se bloquean si la legalidad no está verificada.
- `export-ready` solo se usa cuando la legalidad y los benchmarks están completos. No se inventa un import string de Champions.

Guía completa: [docs/team-building.md](./docs/team-building.md).

## Regulación actual y M-D

- **M-C** es la regulación actual: `2026-09-09 02:00 UTC` a `2026-12-02 01:59 UTC`.
- **M-D** está anunciada como `upcoming`: `2026-12-02 02:00 UTC` a `2027-03-03 01:59 UTC`.
- El roster de M-D todavía no está publicado. No se agrega hasta que la página oficial lo enlace.
- Las skills usan `current-regulation.md`, no una nota fechada. La transición cambia un solo wrapper.
- `python3 tools/resolve_regulation.py --check-registry` detecta el estado real y lo compara con el registry.
- El runbook está en [docs/maintenance/regulation-transition.md](./docs/maintenance/regulation-transition.md).

## Validación

```bash
python3 tools/validate.py
```

El alcance completo ejecuta tests, render del registry, cobertura offline del probe, freshness de formato, drift de plugins, trust data del sitio y build de producción.

Comandos individuales y probes live: [docs/validation.md](./docs/validation.md).

## Mantenimiento

- [Runbook de transición de regulación](./docs/maintenance/regulation-transition.md)
- [Runbook de Dependabot](./docs/maintenance/dependabot-rebase.md)

## Herramientas de coaching

Skills principales:

1. `vgc-meta-research`
2. `vgc-team-builder`
3. `vgc-team-audit`
4. `vgc-lead-planner`
5. `vgc-battle-review`

Skills de apoyo:

- `vgc-format-verifier`
- `vgc-source-verifier`
- `vgc-calcs-assistant`
- `vgc-opponent-scout`
- `vgc-practice-journal`

## Estructura del repositorio

```text
vgc-coach/
├── AGENTS.md
├── LICENSE
├── NOTICE
├── README.md
├── README.en.md
├── docs/
│   ├── README.md
│   ├── installation.md
│   ├── sources.md
│   ├── team-building.md
│   ├── validation.md
│   ├── runtime/
│   └── skills/
├── skills/
├── plugins/          # generado
├── data/
│   ├── fixtures/evals/
│   ├── rubrics/
│   └── snapshots/
├── tools/
└── site/
```

## Licencia y atribución

Apache-2.0. Consulta [LICENSE](./LICENSE) y [NOTICE](./NOTICE).

- Upstream: [NoahJenkins/vgc-coach](https://github.com/NoahJenkins/vgc-coach)
- Investigación de endpoints y TTLs: [VGC-Reporter](https://github.com/felipesuarez-dev/VGC-Reporter) (MIT)
