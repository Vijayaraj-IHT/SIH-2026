// =============================================================================
// Multi-Sport Tournament Fixture Generator Engine
// Implements Berger Round Robin Algorithm and Single Elimination with Byes
// =============================================================================

export interface DraftPairing {
  roundNumber: number;
  matchOrder: number;
  teamAId: string | null;
  teamBId: string | null;
  isBye: boolean;
  label: string;
  sourceTypeA?: 'FIXTURE_RESULT' | 'GROUP_POSITION' | 'POOL_RANK';
  sourceRoleA?: 'WINNER' | 'RUNNER_UP' | 'LOSER' | 'GROUP_POSITION';
  sourceFixtureIndexA?: number;
  sourceTypeB?: 'FIXTURE_RESULT' | 'GROUP_POSITION' | 'POOL_RANK';
  sourceRoleB?: 'WINNER' | 'RUNNER_UP' | 'LOSER' | 'GROUP_POSITION';
  sourceFixtureIndexB?: number;
}

/**
 * Generates round-robin fixtures using the Berger circle algorithm
 */
export function generateRoundRobinFixtures(teamIds: string[]): DraftPairing[] {
  const teams = [...teamIds];
  const pairings: DraftPairing[] = [];

  // If odd number of teams, add a dummy BYE team (null)
  if (teams.length % 2 !== 0) {
    teams.push('BYE');
  }

  const n = teams.length;
  const rounds = n - 1;
  const matchesPerRound = n / 2;

  let globalOrder = 1;

  for (let r = 0; r < rounds; r++) {
    for (let m = 0; m < matchesPerRound; m++) {
      const teamA = teams[m];
      const teamB = teams[n - 1 - m];

      const isBye = teamA === 'BYE' || teamB === 'BYE';
      const actualTeamA = teamA === 'BYE' ? null : teamA;
      const actualTeamB = teamB === 'BYE' ? null : teamB;

      if (!isBye) {
        pairings.push({
          roundNumber: r + 1,
          matchOrder: globalOrder++,
          teamAId: actualTeamA,
          teamBId: actualTeamB,
          isBye: false,
          label: `Round ${r + 1} - Match ${m + 1}`,
        });
      }
    }

    // Rotate teams in the circle keeping index 0 fixed
    const fixed = teams[0];
    const rest = teams.slice(1);
    const last = rest.pop()!;
    teams.length = 0;
    teams.push(fixed, last, ...rest);
  }

  return pairings;
}

/**
 * Generates single-elimination tournament knockout brackets with automatic Byes
 */
export function generateKnockoutBrackets(teamIds: string[]): {
  rounds: { name: string; stageOrder: number; matches: DraftPairing[] }[];
} {
  const count = teamIds.length;
  if (count < 2) return { rounds: [] };

  // Calculate nearest power of 2
  let bracketSize = 2;
  while (bracketSize < count) {
    bracketSize *= 2;
  }

  const byesCount = bracketSize - count;
  const totalRounds = Math.log2(bracketSize);

  const roundNames = ['Round of 32', 'Round of 16', 'Quarter Final', 'Semi Final', 'Final'];
  const relevantNames = roundNames.slice(roundNames.length - totalRounds);

  const roundsData: { name: string; stageOrder: number; matches: DraftPairing[] }[] = [];

  // Round 1 (with seeding and byes)
  const round1Matches: DraftPairing[] = [];
  const r1MatchCount = bracketSize / 2;

  let seededSlots: (string | 'BYE')[] = [];
  for (let i = 0; i < count; i++) {
    seededSlots.push(teamIds[i]);
  }
  for (let i = 0; i < byesCount; i++) {
    seededSlots.push('BYE');
  }

  for (let i = 0; i < r1MatchCount; i++) {
    const tA = seededSlots[i * 2];
    const tB = seededSlots[i * 2 + 1];

    round1Matches.push({
      roundNumber: 1,
      matchOrder: i + 1,
      teamAId: tA === 'BYE' ? null : tA,
      teamBId: tB === 'BYE' ? null : tB,
      isBye: tA === 'BYE' || tB === 'BYE',
      label: `${relevantNames[0]} ${i + 1}`,
    });
  }

  roundsData.push({
    name: relevantNames[0],
    stageOrder: 1,
    matches: round1Matches,
  });

  // Subsequent knockout rounds (linking upstream winners)
  for (let r = 1; r < totalRounds; r++) {
    const matchCount = bracketSize / Math.pow(2, r + 1);
    const currentMatches: DraftPairing[] = [];
    const prevMatches = roundsData[r - 1].matches;

    for (let m = 0; m < matchCount; m++) {
      const sourceM1Index = m * 2;
      const sourceM2Index = m * 2 + 1;

      currentMatches.push({
        roundNumber: r + 1,
        matchOrder: m + 1,
        teamAId: null,
        teamBId: null,
        isBye: false,
        label: `${relevantNames[r]} ${m + 1}`,
        sourceTypeA: 'FIXTURE_RESULT',
        sourceRoleA: 'WINNER',
        sourceFixtureIndexA: sourceM1Index,
        sourceTypeB: 'FIXTURE_RESULT',
        sourceRoleB: 'WINNER',
        sourceFixtureIndexB: sourceM2Index,
      });
    }

    roundsData.push({
      name: relevantNames[r],
      stageOrder: r + 1,
      matches: currentMatches,
    });
  }

  return { rounds: roundsData };
}
