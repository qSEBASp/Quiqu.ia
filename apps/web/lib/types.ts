export type Result = "win" | "loss" | "draw";
export type Side = "attack" | "defense" | "unknown";

export interface Profile {
  riot_id: string;
  tag: string;
  region: string;
  platform: string;
  provider: "demo" | "henrik";
  puuid: string | null;
  rank_name: string | null;
  has_henrik_key: boolean;
  has_llm_key: boolean;
  llm_model: string | null;
  updated_at: string | null;
}

export interface Totals {
  matches: number;
  wins: number;
  losses: number;
  winrate: number;
  kd: number;
  kills: number;
  deaths: number;
  assists: number;
  acs: number;
  adr: number;
  hs_pct: number;
  kast: number;
  form_score: number;
  current_streak: number;
  streak_result: Result | null;
}

export interface Pattern {
  rule_id: string;
  title: string;
  category: string;
  severity: number;
  count: number;
  match_ids: string[];
}

export interface Strength {
  rule_id: string;
  category: string;
  title: string;
  summary: string;
  detail: string;
  tier: number;
  metric: number | null;
}

export interface StrengthPattern extends Strength {
  count: number;
  match_ids: string[];
}

export interface TrendPoint {
  id: string;
  date: string;
  acs: number;
  hs_pct: number;
  kast: number;
  result: Result;
  map: string;
  agent: string;
}

export interface MatchSummary {
  id: string;
  started_at: string;
  map: string;
  mode: string;
  agent: string;
  agent_role: string;
  result: Result;
  score_us: number;
  score_them: number;
  kills: number;
  deaths: number;
  assists: number;
  acs: number;
  adr: number;
  hs_pct: number;
  kast: number;
  first_bloods: number;
  first_deaths: number;
  econ_score: number;
  form_score: number;
  trade_rate: number;
  insight_count: number;
  top_insight: string | null;
  top_fix: string | null;
  top_insight_category: string | null;
  top_insight_severity: number | null;
  source: string;
}

export interface Overview {
  profile: Profile;
  totals: Totals;
  top_patterns: Pattern[];
  strengths: StrengthPattern[];
  trend: TrendPoint[];
  recent: MatchSummary[];
}

export interface BackdropStat {
  name: string;
  matches: number;
  share: number;
}

export interface Backdrop {
  matches: number;
  role: BackdropStat | null;
}

export interface Metrics {
  rounds: number;
  attack_rounds: number;
  defense_rounds: number;
  attack_winrate: number;
  defense_winrate: number;
  acs: number;
  adr: number;
  hs_pct: number;
  kast: number;
  kd: number;
  kpr: number;
  dpr: number;
  trade_rate: number;
  first_bloods: number;
  first_deaths: number;
  fb_rate: number;
  fd_rate: number;
  util_usage: number;
  util_rounds_known: number;
  ult_usage: number;
  force_buys: number;
  no_armor_buys: number;
  econ_score: number;
  form_score: number;
  // Métricas derivadas que pueden faltar en partidas guardadas antes de
  // reanalizar el historial, por eso son opcionales.
  fd_attack_rate?: number;
  fb_attack_rate?: number;
  pistol_rounds?: number;
  pistol_wins?: number;
  pistol_rate?: number;
  anti_eco_rounds?: number;
  anti_eco_losses?: number;
  attack_timeouts?: number;
  lost_carry_rounds?: number;
  win_rounds?: number;
  loss_rounds?: number;
  adr_win?: number;
  adr_loss?: number;
  damage_cv?: number;
  util_usage_defense?: number;
  util_defense_known?: number;
  defense_zero_util?: number;
  cheap_rounds?: number;
  half_rounds?: number;
  first_half_rate?: number;
  second_half_rate?: number;
  deaths_with_time?: number;
  late_deaths?: number;
  early_deaths?: number;
  damage_per_death?: number;
}

export interface Round {
  number: number;
  side: Side;
  won: boolean;
  reason: string;
  kills: number;
  deaths: number;
  assists: number;
  survived: boolean;
  damage: number;
  headshots: number;
  bodyshots: number;
  legshots: number;
  first_blood: boolean;
  first_death: boolean;
  traded_death: boolean;
  loadout_value: number;
  credits_remaining: number;
  abilities_used: number | null;
  ult_used: boolean;
  has_armor: boolean;
  weapon: string | null;
  buy_type: "full" | "force" | "save" | "unknown";
}

export interface Insight {
  id: number;
  rule_id: string;
  category: string;
  severity: number;
  title: string;
  detail: string;
  recommendation: string;
  evidence: { rounds?: number[]; [key: string]: unknown };
  metric: number | null;
  threshold: number | null;
}

export interface ReportPriority {
  rule_id?: string;
  title: string;
  category?: string;
  severity?: number;
  why: string;
  fix: string;
  evidence?: { rounds?: number[]; [key: string]: unknown };
}

export interface Report {
  summary: string;
  priorities: ReportPriority[];
  drills: string[];
  model: string;
  created_at?: string | null;
}

export interface ScoreboardEntry {
  name: string;
  tag: string;
  team: string;
  agent: string;
  kills: number;
  deaths: number;
  assists: number;
  acs: number;
  is_me: boolean;
}

export interface MatchDetail extends MatchSummary {
  metrics: Metrics;
  scoreboard: ScoreboardEntry[];
  rounds: Round[];
  insights: Insight[];
  strengths: Strength[];
  report: Report | null;
}

export interface SyncResult {
  added: number;
  skipped: number;
  received: number;
  provider: string;
  profile: Profile;
  reset?: boolean;
}

export interface ReanalyzeResult {
  analyzed: number;
  insights: number;
  reports: number;
  kept_ai: number;
}
