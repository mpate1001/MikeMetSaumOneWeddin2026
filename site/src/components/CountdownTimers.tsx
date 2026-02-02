import { useState, useEffect } from 'react';

const WEDDING_DATE = new Date('2026-05-24T00:00:00');
const FINAL_COUNT_DATE = new Date('2026-04-24T00:00:00'); // One month before

interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  total: number;
}

function calculateTimeRemaining(targetDate: Date): TimeRemaining {
  const now = new Date();
  const total = targetDate.getTime() - now.getTime();

  if (total <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, total: 0 };
  }

  return {
    days: Math.floor(total / (1000 * 60 * 60 * 24)),
    hours: Math.floor((total / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((total / (1000 * 60)) % 60),
    seconds: Math.floor((total / 1000) % 60),
    total,
  };
}

interface CountdownCardProps {
  title: string;
  subtitle: string;
  targetDate: Date;
  accentColor: 'strawberry' | 'space-indigo' | 'amber';
}

function CountdownCard({ title, subtitle, targetDate, accentColor }: CountdownCardProps) {
  const [timeRemaining, setTimeRemaining] = useState(() => calculateTimeRemaining(targetDate));

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining(calculateTimeRemaining(targetDate));
    }, 1000);

    return () => clearInterval(timer);
  }, [targetDate]);

  const colorClasses = {
    strawberry: {
      bg: 'bg-gradient-to-br from-strawberry to-crimson',
      ring: 'ring-strawberry/20',
    },
    'space-indigo': {
      bg: 'bg-gradient-to-br from-space-indigo to-slate-800',
      ring: 'ring-space-indigo/20',
    },
    amber: {
      bg: 'bg-gradient-to-br from-amber-500 to-orange-600',
      ring: 'ring-amber-500/20',
    },
  };

  const colors = colorClasses[accentColor];
  const isUrgent = timeRemaining.days <= 30 && accentColor === 'amber';

  return (
    <div className={`${colors.bg} rounded-xl shadow-lg p-5 text-white ring-4 ${colors.ring} ${isUrgent ? 'animate-pulse' : ''}`}>
      <div className="mb-3">
        <h3 className="font-bold text-lg">{title}</h3>
        <p className="text-white/70 text-sm">{subtitle}</p>
      </div>

      {timeRemaining.total <= 0 ? (
        <div className="text-center py-4">
          <p className="text-2xl font-bold">It's Time!</p>
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="bg-white/20 rounded-lg py-2 px-1">
            <p className="text-2xl md:text-3xl font-bold">{timeRemaining.days}</p>
            <p className="text-xs text-white/80">days</p>
          </div>
          <div className="bg-white/20 rounded-lg py-2 px-1">
            <p className="text-2xl md:text-3xl font-bold">{timeRemaining.hours}</p>
            <p className="text-xs text-white/80">hours</p>
          </div>
          <div className="bg-white/20 rounded-lg py-2 px-1">
            <p className="text-2xl md:text-3xl font-bold">{timeRemaining.minutes}</p>
            <p className="text-xs text-white/80">mins</p>
          </div>
          <div className="bg-white/20 rounded-lg py-2 px-1">
            <p className="text-2xl md:text-3xl font-bold">{timeRemaining.seconds}</p>
            <p className="text-xs text-white/80">secs</p>
          </div>
        </div>
      )}

      <p className="text-center text-white/60 text-xs mt-3">
        {targetDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
      </p>
    </div>
  );
}

export function CountdownTimers() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      <CountdownCard
        title="Wedding Day"
        subtitle="The big day!"
        targetDate={WEDDING_DATE}
        accentColor="strawberry"
      />
      <CountdownCard
        title="Final Count Due"
        subtitle="Venue headcount deadline"
        targetDate={FINAL_COUNT_DATE}
        accentColor="amber"
      />
    </div>
  );
}
