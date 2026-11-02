// Band über der Eingabe: Ariadnes Knäuel und Name beim Start einer Sitzung im Lern-Repo.
// Es verschwindet mit der ersten Eingabe.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

const GOLD = '#d4a017'
const KNAEUEL = [' ▄███▄', '███████╮', ' ▀███▀ ╰──']

const bandWeg = atom({ plugin: 'ariadne', key: 'bandWeg' } as const, true)

let lernrepo: string | null = null
let version = ''

// Das Plugin ist überall installiert, das Band gehört aber nur in Lern-Repos.
async function findeLernrepo($: EngineInterface, start: string): Promise<string | null> {
  let dir = start
  while (true) {
    if (await $.fs.exists(dir + '/ariadne.toml')) return dir
    const oben = dir.slice(0, dir.lastIndexOf('/')) || '/'
    if (oben === dir) return null
    dir = oben
  }
}

async function lese($: EngineInterface, pfad: string): Promise<string> {
  return $.fs.read($.plugin.root + '/' + pfad).catch(() => '')
}

function leseVersion(manifest: string): string {
  try {
    const v: unknown = JSON.parse(manifest).version
    return typeof v === 'string' ? v : ''
  } catch {
    return ''
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    lernrepo = await findeLernrepo($, e.cwd)
    if (lernrepo !== null) {
      version = leseVersion(await lese($, '.claude-plugin/plugin.json'))
    }
    await update($, bandWeg, () => lernrepo === null)
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    // Ein Fehler beim Ausblenden darf die Eingabe nicht aufhalten.
    await update($, bandWeg, () => true).catch(() => undefined)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    // Zuerst lesen: so zeichnet das Band neu, sobald session.start das Lern-Repo gefunden hat.
    const weg = await read($, bandWeg)
    if (weg || e.props.hasSurvey || lernrepo === null) return next(e)

    const name = lernrepo.slice(lernrepo.lastIndexOf('/') + 1)
    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="row" gap={2}>
        <Box flexDirection="column">
          <Text color={GOLD}>{KNAEUEL[0]}</Text>
          <Text color={GOLD}>{KNAEUEL[1]}</Text>
          <Text color={GOLD}>{KNAEUEL[2]}</Text>
        </Box>
        <Box flexDirection="column" justifyContent="center">
          <Text>
            <Text weight="bold">Ariadne</Text>
            {version ? <Text dimColor> v{version}</Text> : null}
          </Text>
          <Text dimColor>Lerntutor · {name}</Text>
          <Text dimColor>/ariadne:dashboard zeigt den Überblick</Text>
        </Box>
      </Box>
    )
  })
}
