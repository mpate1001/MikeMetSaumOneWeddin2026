import { useState, useEffect, useMemo } from 'react';
import Papa from 'papaparse';
import type { Guest, GuestFilters, SummaryStats, RSVPStatus } from '../types/guest';

type RawGuestData = Record<string, string>;

function parseRSVPStatus(value: string): RSVPStatus {
  const normalized = value?.trim() || '';
  if (normalized === 'Attending') return 'Attending';
  if (normalized === 'Declined') return 'Declined';
  if (normalized === 'Not Invited') return 'Not Invited';
  return 'No Response';
}

// Find column value by partial key match (handles encoding issues in headers)
function getColumnValue(raw: RawGuestData, ...patterns: string[]): string {
  // First try exact match
  for (const pattern of patterns) {
    if (raw[pattern] !== undefined) return raw[pattern];
  }
  // Then try partial match (case-insensitive)
  const keys = Object.keys(raw);
  for (const pattern of patterns) {
    const lowerPattern = pattern.toLowerCase();
    const matchingKey = keys.find(k => k.toLowerCase().includes(lowerPattern));
    if (matchingKey) return raw[matchingKey];
  }
  return '';
}

function parseBrideOrGroom(value: string | undefined): 'Bride' | 'Groom' | 'Unknown' {
  if (value === 'Bride') return 'Bride';
  if (value === 'Groom') return 'Groom';
  return 'Unknown';
}

function parseGuest(raw: RawGuestData): Guest {
  // Support both old format and new scraper format
  const firstName = raw.First_Name || raw['First Name'] || '';
  const lastName = raw.Last_Name || raw['Last Name'] || '';

  // New format: Side = Bride/Groom, Relationship = relationship type
  // Old format: Side = relationship type, Bride_or_Groom = Bride/Groom
  const side = raw.Relationship || raw.Side || 'Unknown';

  // Determine bride/groom with type-safe parsing
  const brideOrGroom = (raw.Side === 'Bride' || raw.Side === 'Groom')
    ? parseBrideOrGroom(raw.Side)
    : parseBrideOrGroom(raw.Bride_or_Groom);

  return {
    title: raw.Title || '',
    firstName,
    lastName,
    suffix: raw.Suffix || '',
    saumyaVidhiHaaldi: parseRSVPStatus(getColumnValue(raw, "RSVP_Saumyas_Vidhi_and_Haaldi", "Saumya's Vidhi & Haaldi", "saumya")),
    mahekVidhiHaaldi: parseRSVPStatus(getColumnValue(raw, "RSVP_Maheks_Vidhi_and_Haaldi", "Mahek's Vidhi & Haaldi", "mahek")),
    wedding: parseRSVPStatus(getColumnValue(raw, "RSVP_Wedding", "Wedding")),
    reception: parseRSVPStatus(getColumnValue(raw, "RSVP_Reception", "Reception")),
    side,
    brideOrGroom,
    email: raw.Email || '',
    phone: raw.Phone || '',
    address: raw.Address || '',
  };
}

export function useGuestData() {
  const [guests, setGuests] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [filters, setFilters] = useState<GuestFilters>({
    brideOrGroom: 'All',
    rsvpStatus: 'All',
    side: 'All',
    searchQuery: '',
  });

  useEffect(() => {
    const abortController = new AbortController();

    async function fetchData() {
      try {
        const response = await fetch(`${import.meta.env.BASE_URL}data.csv`, {
          signal: abortController.signal,
        });
        if (!response.ok) {
          throw new Error('Failed to fetch guest data');
        }
        const csvText = await response.text();

        // Don't update state if component unmounted
        if (abortController.signal.aborted) return;

        Papa.parse<RawGuestData>(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            if (abortController.signal.aborted) return;
            const parsedGuests = results.data.map(parseGuest);
            setGuests(parsedGuests);
            setLastUpdated(new Date().toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            }));
            setLoading(false);
          },
          error: (err: Error) => {
            if (abortController.signal.aborted) return;
            setError(err.message);
            setLoading(false);
          },
        });
      } catch (err) {
        if (abortController.signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    }

    fetchData();

    return () => {
      abortController.abort();
    };
  }, []);

  const filteredGuests = useMemo(() => {
    return guests.filter((guest) => {
      // Filter by bride/groom
      if (filters.brideOrGroom !== 'All' && guest.brideOrGroom !== filters.brideOrGroom) {
        return false;
      }

      // Filter by RSVP status (check wedding event as primary)
      if (filters.rsvpStatus !== 'All' && guest.wedding !== filters.rsvpStatus) {
        return false;
      }

      // Filter by side
      if (filters.side !== 'All' && guest.side !== filters.side) {
        return false;
      }

      // Filter by search query
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const fullName = `${guest.firstName} ${guest.lastName}`.toLowerCase();
        if (!fullName.includes(query)) {
          return false;
        }
      }

      return true;
    });
  }, [guests, filters]);

  const uniqueSides = useMemo(() => {
    const sides = new Set(guests.map(g => g.side));
    return ['All', ...Array.from(sides).sort()];
  }, [guests]);

  const summaryStats = useMemo((): SummaryStats => {
    const stats = filteredGuests.reduce(
      (acc, guest) => {
        // Count based on wedding event for overall stats
        if (guest.wedding === 'Attending') acc.attending++;
        else if (guest.wedding === 'Declined') acc.declined++;
        else if (guest.wedding === 'No Response') acc.noResponse++;

        if (guest.brideOrGroom === 'Bride') acc.brideGuests++;
        else if (guest.brideOrGroom === 'Groom') acc.groomGuests++;

        return acc;
      },
      { attending: 0, declined: 0, noResponse: 0, brideGuests: 0, groomGuests: 0 }
    );

    const totalResponded = stats.attending + stats.declined;
    const totalInvited = filteredGuests.filter(g => g.wedding !== 'Not Invited').length;

    // Event-level stats
    const events = [
      { key: 'saumyaVidhiHaaldi' as const, name: "Saumya's Vidhi & Haaldi" },
      { key: 'mahekVidhiHaaldi' as const, name: "Mahek's Vidhi & Haaldi" },
      { key: 'wedding' as const, name: 'Wedding' },
      { key: 'reception' as const, name: 'Reception' },
    ];

    const eventStats = events.map(({ key, name }) => ({
      event: name,
      attending: filteredGuests.filter(g => g[key] === 'Attending').length,
      declined: filteredGuests.filter(g => g[key] === 'Declined').length,
      noResponse: filteredGuests.filter(g => g[key] === 'No Response').length,
      notInvited: filteredGuests.filter(g => g[key] === 'Not Invited').length,
      brideAttending: filteredGuests.filter(g => g[key] === 'Attending' && g.brideOrGroom === 'Bride').length,
      groomAttending: filteredGuests.filter(g => g[key] === 'Attending' && g.brideOrGroom === 'Groom').length,
    }));

    // Side-specific stats for Wedding and Reception
    const sideEvents = [
      { key: 'wedding' as const, name: 'Wedding' },
      { key: 'reception' as const, name: 'Reception' },
    ];
    const sides: ('Bride' | 'Groom')[] = ['Bride', 'Groom'];

    const sideEventStats = sideEvents.flatMap(({ key, name }) =>
      sides.map(side => ({
        side,
        event: name,
        attending: filteredGuests.filter(g => g[key] === 'Attending' && g.brideOrGroom === side).length,
        declined: filteredGuests.filter(g => g[key] === 'Declined' && g.brideOrGroom === side).length,
        noResponse: filteredGuests.filter(g => g[key] === 'No Response' && g.brideOrGroom === side).length,
      }))
    );

    return {
      totalGuests: filteredGuests.length,
      totalAttending: stats.attending,
      totalDeclined: stats.declined,
      totalNoResponse: stats.noResponse,
      responseRate: totalInvited > 0 ? (totalResponded / totalInvited) * 100 : 0,
      brideGuests: stats.brideGuests,
      groomGuests: stats.groomGuests,
      eventStats,
      sideEventStats,
    };
  }, [filteredGuests]);

  const relationshipStats = useMemo(() => {
    const counts: Record<string, { count: number; brideOrGroom: 'Bride' | 'Groom' | 'Unknown' }> = {};
    filteredGuests.forEach(guest => {
      if (!counts[guest.side]) {
        counts[guest.side] = { count: 0, brideOrGroom: guest.brideOrGroom };
      }
      counts[guest.side].count++;
    });
    return Object.entries(counts)
      .map(([relationship, data]) => ({
        relationship,
        count: data.count,
        brideOrGroom: data.brideOrGroom,
      }))
      .sort((a, b) => b.count - a.count);
  }, [filteredGuests]);

  return {
    guests: filteredGuests,
    allGuests: guests,
    loading,
    error,
    lastUpdated,
    filters,
    setFilters,
    uniqueSides,
    summaryStats,
    relationshipStats,
  };
}
