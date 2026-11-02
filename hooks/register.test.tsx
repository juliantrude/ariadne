import { expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'

const BAND = {
  plugin: 'ariadne',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 20,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 19 },
    view: {},
  },
  surface: 'terminal',
} as const

function engine(on: On, lernrepo: boolean) {
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('prompt.submit', (_, e) => e)
  on('fs.exists', (_, e) => ({ value: lernrepo && e.path === '/lern/mathe/ariadne.toml' }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine</Text>
  })
  on('fs.read', (_, e) => {
    if (e.path.endsWith('plugin.json')) return { value: '{"name": "ariadne", "version": "9.9.9"}' }
    return { value: '' }
  })
}

test('im Lern-Repo zeigt das Band Name und Version, bis zur ersten Eingabe', async ($, on) => {
  engine(on, true)
  await $.session.start({ cwd: '/lern/mathe', surface: 'terminal', isInteractive: true })

  let ui = await $.ui.mount(BAND)
  expect((await ui.find({ type: 'Text', text: /Lerntutor/ }))?.text).toBe('Lerntutor · mathe')
  expect(await ui.find({ type: 'Text', text: /v9\.9\.9/ })).toBeTruthy()
  await ui.unmount()

  await $.prompt.submit({ text: 'hallo', wait: false, origin: { kind: 'composer' } })
  ui = await $.ui.mount(BAND)
  expect(await ui.find({ type: 'Text', text: /Ariadne/ })).toBeFalsy()
  await ui.unmount()
})

test('außerhalb eines Lern-Repos bleibt das Band leer', async ($, on) => {
  engine(on, false)
  await $.session.start({ cwd: '/home/irgendwo', surface: 'terminal', isInteractive: true })

  const ui = await $.ui.mount(BAND)
  expect(await ui.find({ type: 'Text', text: /Ariadne/ })).toBeFalsy()
  await ui.unmount()
})

