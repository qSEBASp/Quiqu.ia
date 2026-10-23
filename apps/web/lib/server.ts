import { getJSON } from "./api";
import type { MatchDetail, MatchSummary, Overview, Profile } from "./types";

export async function fetchOverview(): Promise<Overview | null> {
  try {
    return await getJSON<Overview>("/api/overview");
  } catch {
    return null;
  }
}

export async function fetchProfile(): Promise<Profile | null> {
  try {
    return await getJSON<Profile>("/api/profile");
  } catch {
    return null;
  }
}

export async function fetchMatches(): Promise<MatchSummary[]> {
  try {
    const data = await getJSON<{ matches: MatchSummary[] }>("/api/matches?limit=200");
    return data.matches;
  } catch {
    return [];
  }
}

export async function fetchMatch(id: string): Promise<MatchDetail | null> {
  try {
    return await getJSON<MatchDetail>(`/api/matches/${encodeURIComponent(id)}`);
  } catch {
    return null;
  }
}
