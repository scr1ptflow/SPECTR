import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ranksApi, type RankState } from '@/api/endpoints'

const RANK_NAMES: Record<string, string[]> = {
  combat: ['Harmless', 'Mostly Harmless', 'Novice', 'Competent', 'Expert',
    'Master', 'Dangerous', 'Deadly', 'Elite'],
  trade: ['Penniless', 'Mostly Penniless', 'Peddler', 'Dealer', 'Merchant',
    'Broker', 'Entrepreneur', 'Tycoon', 'Elite'],
  explore: ['Aimless', 'Mostly Aimless', 'Explorer', 'Pathfinder', 'Surveyor',
    'Trailblazer', 'Strider', 'Pioneer', 'Elite'],
  cqc: ['Helpless', 'Mostly Helpless', 'Amateur', 'Semi-Professional',
    'Professional', 'Champion', 'Hero', 'Legend', 'Elite'],
  empire: ['None', 'Outsider', 'Serf', 'Master', 'Squire', 'Knight', 'Lord',
    'Baron', 'Viscount', 'Count', 'Earl', 'Duke', 'Prince', 'King'],
  federation: ['None', 'Recruit', 'Midshipman', 'Petty Officer',
    'Chief Petty Officer', 'Warrant Officer', 'Ensign', 'Lieutenant',
    'Lieutenant Commander', 'Post Commander', 'Post Captain',
    'Rear Admiral', 'Vice Admiral', 'Admiral'],
  soldier: ['Defenceless', 'Unskilled', 'Skilled', 'Capable', 'Proficient',
    'Competent', 'Expert', 'Veteran', 'Elite'],
  exobiologist: ['Directionless', 'Mostly Directionless', 'Explorer',
    'Pathfinder', 'Surveyor', 'Trailblazer', 'Strider', 'Pioneer', 'Elite'],
}

export const useRanksStore = defineStore('ranks', () => {
  const ranks = ref<RankState | null>(null)

  async function fetch() {
    ranks.value = await ranksApi.get()
  }

  function getRankName(category: string, level: number): string {
    const names = RANK_NAMES[category] || []
    return names[level] || String(level)
  }

  return { ranks, fetch, getRankName }
})
