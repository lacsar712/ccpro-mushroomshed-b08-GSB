export type RoomStatus = 'fruiting' | 'idle' | 'sanitize'
export type HarvestGrade = 'A' | 'B' | 'C'

export interface CurrentUser {
  id: number
  username: string
  role: string
  displayName: string
}

export interface ShiftHandover {
  id: number
  shedId: number
  workDate: string
  phrase: string
  handedBy: string
  takenBy: string
  closedAt?: string | null
}

export interface Shed {
  id: number
  name: string
  location: string
  notes?: string | null
  openHandover?: ShiftHandover | null
}

export interface Room {
  id: number
  shedId: number
  roomCode: string
  species: string
  capacityBags: number
  status: RoomStatus
}

export interface ClimateLog {
  id: number
  roomId: number
  recordedAt: string
  tempC: number
  humidityPct: number
  co2Ppm?: number | null
  notes?: string | null
}

export interface FlushHarvest {
  id: number
  roomId: number
  harvestedAt: string
  flushNo: number
  weightKg: number
  grade: HarvestGrade
  operatorName: string
}

export interface DashboardStats {
  shedTotal: number
  fruitingRoomCount: number
  climateLast24h: number
  harvestKgLast7d: number
}
