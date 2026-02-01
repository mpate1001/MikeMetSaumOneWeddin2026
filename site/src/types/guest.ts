export type RSVPStatus = 'Attending' | 'Declined' | 'No Response' | 'Not Invited';

export interface Guest {
  title: string;
  firstName: string;
  lastName: string;
  suffix: string;
  saumyaVidhiHaaldi: RSVPStatus;
  mahekVidhiHaaldi: RSVPStatus;
  wedding: RSVPStatus;
  reception: RSVPStatus;
  side: string;
  brideOrGroom: 'Bride' | 'Groom' | 'Unknown';
}

export interface GuestFilters {
  brideOrGroom: 'All' | 'Bride' | 'Groom';
  rsvpStatus: RSVPStatus | 'All';
  side: string;
  searchQuery: string;
}

export interface EventStats {
  event: string;
  attending: number;
  declined: number;
  noResponse: number;
  notInvited: number;
}

export interface SummaryStats {
  totalGuests: number;
  totalAttending: number;
  totalDeclined: number;
  totalNoResponse: number;
  responseRate: number;
  brideGuests: number;
  groomGuests: number;
  eventStats: EventStats[];
}
