export type AriadneBand = { weg: boolean }

declare module 'claude-code' {
  interface PluginState {
    ariadne: { bandWeg: boolean }
  }
}
