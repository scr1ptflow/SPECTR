import { api } from './client'

export interface CommanderState {
  name: string
  credits: number
  loan: number
  squadron: string
  powerplay_power: string
  powerplay_rank: number
  powerplay_merits: number
}

export interface RankState {
  combat: number
  trade: number
  explore: number
  cqc: number
  empire: number
  federation: number
  soldier: number
  exobiologist: number
  combat_progress: number
  trade_progress: number
  explore_progress: number
}

export interface ShipState {
  ship_type: string
  ship_name: string
  ship_ident: string
  hull_health: number
  fuel_capacity: number
  fuel_current: number
  cargo_capacity: number
  cargo_count: number
  rebuy: number
  modules: any[]
}

export interface LocationState {
  system: string
  system_address: number
  body: string
  body_type: string
  distance_from_star_ls: number
  faction: string
  government: string
  economy: string
  security: string
  population: number
  allegiance: string
  station: string
  station_type: string
  docked: boolean
  near_body: boolean
}

export interface NavigationState {
  target_system: string
  target_body: string
  route: any[]
  jump_count: number
  total_distance_ly: number
}

export interface GameState {
  commander: CommanderState
  ranks: RankState
  ship: ShipState
  location: LocationState
  navigation: NavigationState
  cargo: { capacity: number; count: number; items: any[] }
  missions: { active: any[]; complete: any[]; failed: any[] }
  engineering: { current_modification: string; engineer: string; grade: number; materials: Record<string, number> }
  scans: { bodies_scanned: number; bodies_detailed: number; organic_scans: any[]; organic_sold: Record<string, any>; total_scan_value: number }
  notoriety: number
  timestamp: string
  raw_events: number
}

export interface CommanderRank {
  level: number
  name: string
  progress: number
}

export interface Finding {
  title: string
  description: string
  severity: string
}

export interface Recommendation {
  priority: string
  message: string
  reason: string
  action: string
}

export interface DepartmentReport {
  department: string
  title: string
  status: string
  summary: string
  findings: Finding[]
  recommendations: Recommendation[]
  details: Record<string, any>
  history: Record<string, any>
  generated: string
}

export interface CommanderReport extends DepartmentReport {
  details: {
    name: string
    credits: number
    loan: number
    squadron: string
    powerplay_power: string
    powerplay_rank: number
    powerplay_merits: number
    ranks: Record<string, CommanderRank>
  }
  history: {
    total_rank: number
    elite_ranks: number
  }
}

export interface NavigationReport extends DepartmentReport {
  details: {
    system: string
    system_address: number
    body: string
    body_type: string
    distance_from_star_ls: number
    faction: string
    government: string
    economy: string
    security: string
    population: number
    allegiance: string
    station: string
    station_type: string
    docked: boolean
    near_body: boolean
    latitude: number | null
    longitude: number | null
    jump_count: number
    total_distance_ly: number
    target_system: string
    target_body: string
    route: any[]
  }
  history: {
    jumps: number
    total_distance_ly: number
    bodies_scanned: number
    bodies_detailed: number
    organic_scans: number
  }
}

export interface EngineeringReport extends DepartmentReport {
  details: {
    ship_type: string
    ship_name: string
    ship_ident: string
    hull_health: number
    fuel_capacity: number
    fuel_current: number
    cargo_capacity: number
    cargo_count: number
    rebuy: number
    modules: any[]
    current_modification: string
    engineer: string
    grade: number
    progress: number
    materials: Record<string, number>
    material_count: number
    material_types: number
  }
  history: {
    modifications_applied: number
    material_count: number
    material_types: number
  }
}

export interface OperationsReport extends DepartmentReport {
  details: {
    active: any[]
    complete: any[]
    failed: any[]
    active_count: number
    complete_count: number
    failed_count: number
    cargo_capacity: number
    cargo_count: number
    cargo_items: any[]
  }
  history: {
    missions_completed: number
    missions_failed: number
  }
}

export interface LaboratoryReport extends DepartmentReport {
  details: {
    bodies_scanned: number
    bodies_detailed: number
    organic_scan_count: number
    unique_species: number
    species: { species: string; variant: string; body: string; count: number }[]
    sold: { species: string; variant: string; value: number; count: number }[]
    total_earned: number
  }
  history: {
    bodies_scanned: number
    organic_scans: number
    species_sold: number
  }
}

export interface ArchiveReport extends DepartmentReport {
  details: {
    jumps: number
    total_distance_ly: number
    bodies_scanned: number
    bodies_detailed: number
    organic_scans: number
    missions_completed: number
    missions_failed: number
    missions_active: number
  }
  history: {
    jumps: number
    distance: number
    scans: number
    missions_done: number
  }
}

export interface IntelligenceReport extends DepartmentReport {
  details: {
    risk_level: string
    alerts: { title: string; description: string; severity: string }[]
    session_highlights: string[]
  }
  history: {
    risk_level: string
    highlights: string[]
  }
}

export interface BridgeReport {
  captain_briefing: {
    summary: string
    status: string
  }
  ship_status: {
    ship_type: string
    ship_name: string
    ship_ident: string
    hull_health: number
    fuel_capacity: number
    fuel_current: number
    fuel_percent: number
    cargo_capacity: number
    cargo_count: number
    cargo_percent: number
    rebuy: number
    jump_range: number | null
    power_margin: number | null
  }
  current_mission: {
    id: number
    title: string
    destination: string
    reward: number
    expiration: string
    remaining_jumps: number | null
  } | null
  department_status: {
    department: string
    status: string
    summary: string
  }[]
  current_location: {
    system: string
    body: string
    primary_star: string
    bodies_count: number
    stations: string[]
    fleet_carriers: string[]
    security: string
    economy: string
    population: number
    faction: string
    government: string
    allegiance: string
    docked: boolean
    near_body: boolean
  }
  alerts: {
    title: string
    description: string
    severity: string
    department: string
  }[]
  recommendations: {
    priority: string
    message: string
    reason: string
    action: string
  }[]
  expedition_summary: {
    jumps: number
    distance_ly: number
    bodies_scanned: number
    bodies_detailed: number
    organic_scans: number
    missions_completed: number
    missions_failed: number
    missions_active: number
  }
  captains_log: {
    event: string
    department: string
  }[]
  generated: string
}

export interface SessionState {
  session_id: number
  active: boolean
  started_at: string
  duration_seconds: number
  commander: string
  ship: string
  starting_system: string
  credits_start: number
  credits_current: number
  credits_earned: number
  jumps: number
  distance_ly: number
  systems_visited: number
  bodies_scanned: number
  organic_scans: number
  missions_completed: number
  missions_failed: number
  events_count: number
}

export const commanderApi = {
  get: () => api.get<CommanderReport>('/commander'),
}

export const navigationApi = {
  get: () => api.get<NavigationReport>('/navigation'),
}

export const shipApi = {
  get: () => api.get<ShipState>('/ship'),
}

export const missionsApi = {
  get: () => api.get<OperationsReport>('/missions'),
}

export const scansApi = {
  get: () => api.get<LaboratoryReport>('/scans'),
}

export const engineeringApi = {
  get: () => api.get<EngineeringReport>('/engineering'),
}

export const ranksApi = {
  get: () => api.get<RankState>('/ranks'),
}

export const bridgeApi = {
  get: () => api.get<BridgeReport>('/bridge'),
}

export const sessionApi = {
  get: () => api.get<SessionState>('/session'),
}

export const archiveApi = {
  get: () => api.get<ArchiveReport>('/archive'),
}

export const intelligenceApi = {
  get: () => api.get<IntelligenceReport>('/intelligence'),
}
